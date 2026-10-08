"""Run headless numerical experiments, regression suites, and plotting.

Notes
-----
Numerical histories are lists of dictionaries containing scalar SI values,
not NumPy state arrays. Production integration/contact functions generate
the trajectories. Matplotlib is imported only during plotting.
See assign3/SPEC.md [EQ-DRIFT], [EQ-CONTACT-ENERGY], and [EQ-ACCOUNTING].
Calling run_validation writes evidence; importing this module does not.
"""

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict, replace
from importlib import metadata
import io
import json
import math
from pathlib import Path
import platform
import sys
import traceback
import unittest

from contacts import resolve_contacts
from integration import complete_step, step
from state import Box, CircleState, PhysicsParameters


def whole_steps(duration, dt, option):
    """Validate a duration and convert it to a bounded whole-step count.

    Parameters
    ----------
    duration : float
        Finite positive duration in s.
    dt : float
        Finite positive fixed step in s.
    option : str
        Option label included in error messages.

    Returns
    -------
    int
        Rounded duration/dt, between 1 and 1,000,000 inclusive.

    Raises
    ------
    ValueError
        If inputs or quotient are nonfinite, inputs are nonpositive, the
        quotient differs from an integer by more than eight ulps, or the
        count is outside the permitted range.

    Notes
    -----
    Does not adjust dt or duration and performs no integration.
    See assign3/SPEC.md [EQ-TIME]. Numeric argument types are assumed.
    """
    if not math.isfinite(duration) or duration <= 0 or not math.isfinite(dt) or dt <= 0:
        raise ValueError(f"{option} and --dt must be finite and positive")
    ratio = duration / dt
    if not math.isfinite(ratio):
        raise ValueError(f"{option}/dt is too large; increase --dt or shorten {option}")
    count = round(ratio)
    if count < 1 or abs(ratio - count) > 8 * math.ulp(ratio):
        suggestion = max(1, count) * dt
        raise ValueError(f"{option}={duration:g} must be a whole number of dt={dt:g} steps; "
                         f"try {option}={suggestion:.17g} or choose an aligned --dt")
    # Bound the size of JSON traces and work, rather than silently changing dt.
    if count > 1_000_000:
        raise ValueError(f"{option} requires more than 1000000 steps; shorten it or increase --dt")
    return count


def validate_experiments(dt, duration, bounce_duration):
    """Validate coarse/fine free-fall and bouncing experiment lengths.

    Parameters
    ----------
    dt : float
        Finite positive coarse timestep in s; fine free fall uses dt/2.
    duration : float
        Finite positive free-fall duration in s, aligned to both timesteps.
    bounce_duration : float
        Finite positive bouncing duration in s, aligned to dt.

    Returns
    -------
    tuple of int
        Three-element (coarse_count, fine_count, bounce_count). Every count
        is at most 1,000,000 and fine_count is twice coarse_count.

    Raises
    ------
    ValueError
        If whole_steps rejects any run, counts do not match, or the free-fall
        duration/endpoint reaches the floor under the fixed setup.

    Notes
    -----
    Uses y0=10 m, radius=0.2 m, and g=9.81 m/s^2 in its floor checks.
    These checks are not generalized to arbitrary physical parameters.
    No files or state are changed. See assign3/SPEC.md [EQ-FLIGHT] and [EQ-STEP].
    """
    coarse = whole_steps(duration, dt, "--duration")
    fine = whole_steps(duration, dt / 2, "--duration (fine run)")
    bounce = whole_steps(bounce_duration, dt, "--bounce-duration")
    if fine != 2 * coarse:
        raise ValueError("coarse and fine durations must have matching whole-step endpoints")
    # Coarse discrete trajectory is lower than the exact/fine trajectories.
    if duration >= math.sqrt(2 * (10 - 0.2) / 9.81):
        raise ValueError("--duration reaches the floor in the free-fall experiment; "
                         "shorten --duration (default 1 second)")
    lowest = 10 - 0.5 * 9.81 * (coarse * dt) ** 2 - 0.5 * 9.81 * dt * (coarse * dt)
    if lowest <= 0.2:
        raise ValueError("--duration reaches the floor in the free-fall experiment; "
                         "shorten --duration (default 1 second) to keep y > 0.2 m")
    return coarse, fine, bounce


def tolerance(base, count, scale):
    """Compute the scale-dependent floating-point residual allowance.

    Parameters
    ----------
    base : float
        Minimum absolute tolerance in the quantity's SI unit.
    count : int
        Dimensionless step count used in the roundoff budget.
    scale : float
        Numeric magnitude expressed in the same SI unit as base.

    Returns
    -------
    float
        max(base, 8 * machine_epsilon * count * max(1, scale)).

    Notes
    -----
    Inputs are not validated. This is a residual allowance, not a bound
    on integration error against continuous motion. See assign3/SPEC.md
    [EQ-TOL] and [EQ-DRIFT].
    """
    return max(base, 8 * sys.float_info.epsilon * count * max(1.0, scale))


def check_close(checks, name, measured, expected, tol):
    """Append a finite absolute-residual check to a result list.

    Parameters
    ----------
    checks : list of dict
        Mutable destination for check records.
    name : str
        Human-readable check label.
    measured, expected : float
        Scalar values in the same units.
    tol : float
        Absolute allowance in those units; caller supplies an appropriate value.

    Returns
    -------
    None
        Appends a dictionary with name, measured, expected, residual,
        tolerance, and passed; does not raise on a failed comparison.

    Notes
    -----
    Passes only for finite measured - expected with absolute value <= tol.
    Mutates checks; inputs are not otherwise validated.
    See assign3/SPEC.md [EQ-TOL].
    """
    residual = measured - expected
    checks.append(dict(name=name, measured=measured, expected=expected,
                       residual=residual, tolerance=tol,
                       passed=math.isfinite(residual) and abs(residual) <= tol))


def check_true(checks, name, measured):
    """Append a boolean check without raising an assertion on failure.

    Parameters
    ----------
    checks : list of dict
        Mutable destination for check records.
    name : str
        Human-readable check label.
    measured : object
        Value converted with bool.

    Returns
    -------
    None
        Appends name, bool(measured), expected=True, and passed=bool(measured).

    Notes
    -----
    Mutates checks; exceptions from the object's truth conversion propagate.
    """
    checks.append(dict(name=name, measured=bool(measured), expected=True, passed=bool(measured)))


def energy(state, parameters):
    """Compute translational kinetic plus gravitational potential energy.

    Parameters
    ----------
    state : CircleState
        Scalar velocities in m/s and center height y in m.
    parameters : PhysicsParameters
        Mass in kg and downward gravity magnitude in m/s^2.

    Returns
    -------
    float
        Total mechanical energy in J, using center height in the potential term.

    Notes
    -----
    No mutation or validation is performed. This diagnostic does not imply
    discrete energy conservation. See assign3/SPEC.md [EQ-ENERGY].
    """
    return (0.5 * parameters.mass * (state.vx ** 2 + state.vy ** 2)
            + parameters.mass * parameters.gravity * state.y)


def sample(state, parameters):
    """Copy scalar state fields into an energy/time sample dictionary.

    Parameters
    ----------
    state : CircleState
        State to inspect without advancing it.
    parameters : PhysicsParameters
        Supplies dt in s, mass in kg, and gravity in m/s^2.

    Returns
    -------
    dict
        time (s), x/y (m), vx/vy (m/s), step_count (integer), and energy (J).

    Notes
    -----
    State is not mutated or revalidated. Time is step_count * dt.
    See assign3/SPEC.md [EQ-TIME] and [EQ-ENERGY].
    """
    return dict(time=state.time(parameters), **asdict(state), energy=energy(state, parameters))


def free_fall(parameters, count, checks, label):
    """Generate contact-free samples and append discrete-formula checks.

    Parameters
    ----------
    parameters : PhysicsParameters
        Valid physical parameters with fixed positive dt in s.
    count : int
        Number of steps; caller must supply a nonnegative integer.
    checks : list of dict
        Mutable destination for numerical check records.
    label : str
        Prefix for check names, such as 'coarse' or 'fine'.

    Returns
    -------
    dict
        parameters and box dictionaries; samples (count + 1 dictionaries,
        including time zero); position/velocity/energy tolerances; final sample.
        Rows include state, analytical references, signed errors, and residuals.

    Raises
    ------
    ValueError
        If the fixed 100 m by 100 m box is incompatible with the radius.

    Notes
    -----
    Creates a local state at (50, 10) m with zero velocity and advances it
    with step, never resolving contacts. Appends checks but does not mutate
    parameters or write files. Direct calls do not enforce CLI duration limits.
    Expected signed height error is -g*dt*t/2. Energy checks compare per-step
    and cumulative drift with discrete predictions, not zero drift.
    See assign3/SPEC.md [EQ-FLIGHT], [EQ-STEP], [EQ-DRIFT], and [EQ-TOL].
    """
    state = CircleState(x=50, y=10, vx=0)
    box = Box(width=100, height=100)
    box.validate_for(parameters)
    initial_energy = energy(state, parameters)
    samples = []
    previous_energy = initial_energy
    for n in range(count + 1):
        if n:
            step(state, parameters)
        row = sample(state, parameters)
        t = row["time"]
        exact = 10 - 0.5 * parameters.gravity * t ** 2
        predicted = -0.5 * parameters.gravity * parameters.dt * t
        expected_drift = -0.5 * parameters.mass * parameters.gravity ** 2 * parameters.dt * t
        step_drift = -0.5 * parameters.mass * parameters.gravity ** 2 * parameters.dt ** 2 if n else 0.0
        row.update(exact_height=exact, expected_height=exact + predicted,
                   signed_error=state.y - exact, predicted_signed_error=predicted,
                   height_residual=state.y - exact - predicted,
                   expected_vy=-parameters.gravity * t,
                   velocity_residual=state.vy + parameters.gravity * t,
                   expected_energy_drift=expected_drift,
                   measured_energy_drift=row["energy"] - initial_energy,
                   energy_residual=row["energy"] - initial_energy - expected_drift,
                   expected_step_energy_drift=step_drift,
                   measured_step_energy_drift=row["energy"] - previous_energy,
                   step_energy_residual=row["energy"] - previous_energy - step_drift)
        samples.append(row)
        previous_energy = row["energy"]
    position_tol = tolerance(1e-10, count, 10)
    velocity_tol = tolerance(1e-10, count, parameters.gravity * count * parameters.dt)
    energy_tol = tolerance(1e-9, count, initial_energy)
    for key, tol in (("height_residual", position_tol), ("velocity_residual", velocity_tol),
                     ("energy_residual", energy_tol), ("step_energy_residual", energy_tol)):
        check_close(checks, f"{label}: max absolute {key}",
                    max(abs(r[key]) for r in samples), 0, tol)
    check_true(checks, f"{label}: surfaces safely distant",
               all(r["y"] > parameters.radius and parameters.radius < r["x"] < box.width - parameters.radius
                   for r in samples))
    return dict(parameters=asdict(parameters), box=asdict(box), samples=samples,
                tolerances=dict(position=position_tol, velocity=velocity_tol, energy=energy_tol),
                final=samples[-1])


def bouncing(parameters, count, checks, label):
    """Generate a default-state contact trajectory and energy accounting.

    Parameters
    ----------
    parameters : PhysicsParameters
        Valid physical constants and fixed positive dt in s.
    count : int
        Number of complete steps; caller supplies a nonnegative integer.
    checks : list of dict
        Mutable destination for checks.
    label : str
        Prefix for the appended check names.

    Returns
    -------
    dict
        parameters and box dictionaries, count + 1 sample dictionaries,
        chronological contact dictionaries, per-surface impact_counts,
        and scalar energy_tolerance in J. Contact corrections are two-element
        tuples in m; velocities are scalar m/s.

    Raises
    ------
    ValueError
        If complete_step rejects geometry or post-step state validation fails.

    Notes
    -----
    Starts from CircleState() and Box(), advances a local state, and appends
    checks without file output. Contact dictionaries include time/count,
    record fields, is_impact, kinetic change, restitution loss, correction
    energy, and residuals. Counts include only records with changed normal
    velocity. Integration drift is reconstructed by subtracting measured
    contact kinetic change and m*g*dy from post-step energy. The e=1 diagnostic
    checks zero restitution loss, not exact total-energy conservation.
    See assign3/SPEC.md [EQ-STEP], [EQ-ENERGY], [EQ-DRIFT],
    [EQ-CONTACT-ENERGY], [EQ-ACCOUNTING], and [EQ-TOL].
    """
    state, box = CircleState(), Box()
    initial_energy = energy(state, parameters)
    initial = sample(state, parameters)
    samples = [dict(initial, cumulative_integration_drift=0.0,
                    cumulative_restitution_loss=0.0, cumulative_correction_energy=0.0,
                    cumulative_accounting_residual=0.0)]
    records_out = []
    counts = dict(floor=0, left=0, right=0)
    drift_total = loss_total = correction_total = 0.0
    max_integration_residual = max_restitution_residual = max_total_residual = 0.0
    all_bounded = True
    for _ in range(count):
        before = energy(state, parameters)
        records = complete_step(state, parameters, box)
        after = energy(state, parameters)
        measured_contact_kinetic = predicted_loss = correction_energy = 0.0
        for record in records:
            kinetic_change = 0.5 * parameters.mass * (
                record.normal_velocity_after ** 2 - record.normal_velocity_before ** 2)
            loss = (-0.5 * parameters.mass * (1 - parameters.restitution ** 2)
                    * record.normal_velocity_before ** 2 if record.normal_velocity_before < 0 else 0.0)
            correction = parameters.mass * parameters.gravity * record.position_correction[1]
            measured_contact_kinetic += kinetic_change
            predicted_loss += loss
            correction_energy += correction
            max_restitution_residual = max(max_restitution_residual, abs(kinetic_change - loss))
            if record.is_impact:
                counts[record.surface] += 1
            records_out.append(dict(time=state.time(parameters), step_count=state.step_count,
                                    **asdict(record), is_impact=record.is_impact,
                                    measured_kinetic_change=kinetic_change, expected_restitution_loss=loss,
                                    restitution_residual=kinetic_change - loss,
                                    correction_energy=correction))
        # Reconstruct the pre-contact energy from recorded velocity/position changes.
        # No independent position or velocity integration is performed here.
        pre_contact = after - measured_contact_kinetic - correction_energy
        measured_drift = pre_contact - before
        expected_drift = -0.5 * parameters.mass * parameters.gravity ** 2 * parameters.dt ** 2
        expected_total = expected_drift + predicted_loss + correction_energy
        integration_residual = measured_drift - expected_drift
        total_residual = after - before - expected_total
        drift_total += expected_drift
        loss_total += predicted_loss
        correction_total += correction_energy
        cumulative_residual = after - initial_energy - drift_total - loss_total - correction_total
        max_integration_residual = max(max_integration_residual, abs(integration_residual))
        max_total_residual = max(max_total_residual, abs(total_residual), abs(cumulative_residual))
        state.validate()
        all_bounded &= state.y >= parameters.radius and parameters.radius <= state.x <= box.width - parameters.radius
        samples.append(dict(sample(state, parameters), energy_before=before,
                            reconstructed_pre_contact_energy=pre_contact,
                            measured_integration_drift=measured_drift, expected_integration_drift=expected_drift,
                            integration_residual=integration_residual,
                            measured_contact_kinetic_change=measured_contact_kinetic,
                            expected_restitution_loss=predicted_loss, correction_energy=correction_energy,
                            measured_total_change=after - before, expected_total_change=expected_total,
                            accounting_residual=total_residual, cumulative_integration_drift=drift_total,
                            cumulative_restitution_loss=loss_total, cumulative_correction_energy=correction_total,
                            cumulative_accounting_residual=cumulative_residual))
    energy_tol = tolerance(1e-9, count, max(abs(r["energy"]) for r in samples))
    for name, residual in (("integration", max_integration_residual),
                           ("restitution", max_restitution_residual), ("total accounting", max_total_residual)):
        check_close(checks, f"{label}: max absolute {name} residual (J)", residual, 0, energy_tol)
    check_true(checks, f"{label}: finite bounded trajectory", all_bounded)
    if parameters.restitution == 1:
        check_close(checks, f"{label}: zero restitution loss (J)", loss_total, 0, energy_tol)
    return dict(parameters=asdict(parameters), box=asdict(box), samples=samples,
                contacts=records_out, impact_counts=counts, energy_tolerance=energy_tol)


def contact_direction(checks):
    """Check upward floor-overlap correction with the production resolver.

    Parameters
    ----------
    checks : list of dict
        Mutable destination for three checks.

    Returns
    -------
    dict
        Initial/expected/measured heights in m, vertical velocities in m/s,
        restitution, impact flag, and an explicitly illustrative faulty value.

    Notes
    -----
    Uses local state y=0.15 m, vy=+2 m/s and e=0.8, independent of CLI e.
    Checks y=0.2 m, unchanged vy, and one non-impact floor record; scalar
    allowances are 1e-12 SI. The faulty -1.6 m/s value is an isolated
    illustration, not a production defect. No files are written.
    See assign3/SPEC.md [EQ-FLOOR] and [EQ-NORMAL].
    """
    parameters = PhysicsParameters(restitution=0.8)
    state = CircleState(y=0.15, vy=2.0)
    records = resolve_contacts(state, parameters, Box())
    check_close(checks, "upward floor overlap: y (m)", state.y, 0.2, 1e-12)
    check_close(checks, "upward floor overlap: vy (m/s)", state.vy, 2.0, 1e-12)
    check_true(checks, "upward floor overlap: one non-impact floor record",
               len(records) == 1 and records[0].surface == "floor" and not records[0].is_impact)
    return dict(initial_y=0.15, expected_y=0.2, measured_y=state.y, restitution=0.8,
                before_vy=2.0, expected_correct_vy=2.0, measured_correct_vy=state.vy,
                correct_is_impact=any(r.is_impact for r in records),
                illustrative_faulty_vy=-parameters.restitution * 2.0,
                note="Isolated illustration, not an injected production-code bug.")


def regression_checks(output):
    """Run integration/contact unittest suites and write their captured output.

    Parameters
    ----------
    output : pathlib.Path
        Existing output directory; this helper does not create it.

    Returns
    -------
    dict
        tests_run (int), passed (bool), and failures/errors (lists of
        dictionaries with test names and traceback text).

    Raises
    ------
    OSError
        If regression_checks.txt cannot be written.

    Notes
    -----
    Imports check_integration and check_contacts and runs their loaded suites.
    Their script-only version guards do not run on import. Test stdout/stderr
    are redirected into the overwritten UTF-8 regression_checks.txt file.
    Failed assertions are returned as unittest results, not re-raised.
    CLI/scheduler suites are not loaded. See assign3/SPEC.md Section 8.
    """
    import check_contacts
    import check_integration

    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module)
                               for module in (check_integration, check_contacts))
    stream = io.StringIO()
    with redirect_stdout(stream), redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (output / "regression_checks.txt").write_text(stream.getvalue(), encoding="utf-8")
    return dict(tests_run=result.testsRun, passed=result.wasSuccessful(),
                failures=[dict(test=str(test), traceback=detail) for test, detail in result.failures],
                errors=[dict(test=str(test), traceback=detail) for test, detail in result.errors])


def write_plots(report, output):
    """Write the four validation PNGs from a populated report.

    Parameters
    ----------
    report : dict
        Requires environment, two free_fall runs, two bouncing runs,
        and contact_direction data with the structure produced here.
    output : pathlib.Path
        Existing destination directory.

    Returns
    -------
    list of str
        Saved filenames in order: free_fall.png, free_fall_energy.png,
        bouncing_energy.png, contact_direction.png.

    Raises
    ------
    ImportError
        If Matplotlib or a required plotting dependency cannot be imported.
    OSError
        If a figure cannot be written.
    KeyError
        If a required report key is missing.

    Notes
    -----
    Imports Matplotlib, forces Agg before pyplot, sets global font size to
    10, and mutates report['environment']['matplotlib_backend']. Overwrites
    PNGs at 180 dpi with tight bounding boxes. Each figure is closed after
    a successful save; failures can leave partial output or an open figure.
    Other plotting/data errors propagate. No physics is integrated here.
    See assign3/SPEC.md [EQ-DRIFT] and [EQ-ACCOUNTING].
    """
    import matplotlib
    matplotlib.use("Agg", force=True)  # Must precede pyplot import.
    import matplotlib.pyplot as plt

    report["environment"]["matplotlib_backend"] = matplotlib.get_backend()
    plt.rcParams.update({"font.size": 10})
    saved = []

    def save(fig, name):
        fig.savefig(output / name, dpi=180, bbox_inches="tight")
        plt.close(fig)
        saved.append(name)

    coarse, fine = report["free_fall"]
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, layout="constrained")
    axes[0].plot([r["time"] for r in fine["samples"]],
                 [r["exact_height"] for r in fine["samples"]], color="black", label="Analytical height")
    for run, color, label in ((coarse, "tab:blue", "dt"), (fine, "tab:orange", "dt/2")):
        rows = run["samples"]
        times = [r["time"] for r in rows]
        axes[0].plot(times, [r["y"] for r in rows], color=color, linestyle="--",
                     label=f"{label} = {run['parameters']['dt']:.6g} s")
        axes[1].plot(times, [r["signed_error"] for r in rows], color=color, label=f"Measured {label}")
        axes[1].plot(times, [r["predicted_signed_error"] for r in rows], color=color,
                     linestyle=":", linewidth=2.5, label=f"Predicted {label}: -g h t / 2")
    axes[0].set(ylabel="Center height (m)", title="Free fall: semi-implicit Euler")
    axes[1].set(xlabel="Time (s)", ylabel="Numeric minus exact height (m)")
    for axis in axes:
        axis.legend()
        axis.grid(alpha=0.25)
    save(fig, "free_fall.png")

    fig, axis = plt.subplots(figsize=(9, 4.5), layout="constrained")
    for run, label in ((coarse, "dt"), (fine, "dt/2")):
        rows = run["samples"]
        axis.plot([r["time"] for r in rows], [r["measured_energy_drift"] for r in rows], label=f"Measured {label}")
        axis.plot([r["time"] for r in rows], [r["expected_energy_drift"] for r in rows],
                  linestyle=":", label=f"Predicted {label}")
    axis.set(xlabel="Time (s)", ylabel="E(t) - E(0) (J)", title="Contact-free numerical energy drift")
    axis.legend()
    axis.grid(alpha=0.25)
    save(fig, "free_fall_energy.png")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    for column, run in enumerate(report["bouncing"]):
        rows = run["samples"]
        times = [r["time"] for r in rows]
        energy_axis, accounting_axis = axes[0, column], axes[1, column]
        energy_axis.plot(times, [r["energy"] for r in rows], label="Total mechanical energy")
        for surface, marker, color in (("floor", "o", "tab:red"), ("left", "<", "tab:green"), ("right", ">", "tab:purple")):
            impacts = [r for r in run["contacts"] if r["surface"] == surface and r["is_impact"]]
            energy_axis.scatter([r["time"] for r in impacts],
                                [rows[r["step_count"]]["energy"] for r in impacts],
                                marker=marker, color=color, s=14, label=f"{surface} impacts", zorder=3)
        for key, label in (("cumulative_integration_drift", "Integration drift"),
                           ("cumulative_restitution_loss", "Restitution loss"),
                           ("cumulative_correction_energy", "Position correction")):
            accounting_axis.plot(times, [r[key] for r in rows], label=label)
        accounting_axis.plot(times, [r["energy"] - rows[0]["energy"] for r in rows],
                             "k--", label="Measured total change")
        run_name = "Selected restitution" if column == 0 else "Elastic diagnostic"
        energy_axis.set(title=f"{run_name}: e = {run['parameters']['restitution']:g}", ylabel="Energy (J)")
        accounting_axis.set(ylabel="Cumulative energy change (J)")
        for axis in (energy_axis, accounting_axis):
            axis.set_xlabel("Time (s)")
            axis.legend(fontsize=8)
            axis.grid(alpha=0.25)
    save(fig, "bouncing_energy.png")

    diagnostic = report["contact_direction"]
    fig, axis = plt.subplots(figsize=(8, 5), layout="constrained")
    axis.plot([0, 1], [2, diagnostic["measured_correct_vy"]], "o-", label="Correct: real contact resolver")
    axis.plot([0, 1], [2, diagnostic["illustrative_faulty_vy"]], "s--", label="Illustrative faulty rule (not injected)")
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(xticks=[0, 1], xticklabels=["Before contact", "After contact"],
             ylabel="Vertical velocity (m/s), positive upward", ylim=(-2.2, 2.9),
             title="Upward-moving floor overlap: direction matters")
    axis.text(0.03, 0.05, "y: 0.15 → 0.20 m for both rules; e = 0.8\nCorrect response is not an impact.",
              transform=axis.transAxes)
    axis.legend(loc="upper center", fontsize=9)
    axis.grid(alpha=0.25)
    save(fig, "contact_direction.png")
    return saved


def run_validation(output_dir, restitution, dt, duration, bounce_duration):
    """Run numerical validation and overwrite evidence in a selected directory.

    Parameters
    ----------
    output_dir : str or pathlib.Path
        Output directory, created with parents if necessary.
    restitution : float
        Finite dimensionless coefficient in [0, 1].
    dt : float
        Finite positive coarse/bouncing timestep in s.
    duration : float
        Positive free-fall duration in s, aligned to dt and dt/2 and
        constrained to stay above the floor.
    bounce_duration : float
        Positive bouncing duration in s aligned to dt.

    Returns
    -------
    dict
        Report with status ('passed' or 'failed'), physical parameters,
        durations, SI units, environment, checks and filenames. Successful
        reports also contain regressions, free_fall/bouncing histories,
        matching_samples and contact_direction. Caught failures may instead
        leave partial results and an exception traceback.

    Raises
    ------
    ValueError
        If initial experiment/parameter validation fails, or final JSON
        serialization encounters a nonfinite numeric value.
    OSError
        If directory creation or initial/final JSON writing fails.
    Exception
        Other errors outside the experiment/plotting try block propagate.

    Notes
    -----
    All arguments are required in this Python API; defaults belong to the CLI.
    Writes initial results.json with status 'running', runs integration/contact
    regressions and experiments, then writes four PNGs and final results.json.
    Also overwrites regression_checks.txt. Existing directories are not cleared,
    so a failed run can leave old figures. Captures Python/executable/package
    versions and checks loaded modules for rendering/PyVista imports.
    Exceptions inside the experiment/plotting block become failed status and
    stored traceback; initial setup and final serialization are outside it.
    No GUI is opened. Uses selected e and an additional elastic bouncing run,
    plus a fixed-e direction diagnostic. See assign3/SPEC.md [EQ-STEP],
    [EQ-DRIFT], [EQ-ACCOUNTING], and [EQ-TOL].
    """
    counts = validate_experiments(dt, duration, bounce_duration)
    parameters = PhysicsParameters(restitution=restitution, dt=dt)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    versions = {}
    for package in ("matplotlib", "numpy", "pillow", "contourpy", "cycler", "fonttools",
                    "kiwisolver", "packaging", "pyparsing", "python-dateutil", "six"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    report = dict(status="running", parameters=asdict(parameters),
                  units=dict(position="m", time="s", velocity="m/s", mass="kg", energy="J"),
                  durations=dict(free_fall=duration, bouncing=bounce_duration),
                  environment=dict(python=platform.python_version(), executable=sys.executable,
                                   dependencies=versions), checks=[], figures=[],
                  tolerance_policy="max(base, 8 * machine_epsilon * step_count * max(1, scale)); "
                  "position/velocity base 1e-10 SI; energy base 1e-9 J; direct contacts 1e-12 SI")
    result_path = output / "results.json"
    result_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        report["regressions"] = regression_checks(output)
        check_true(report["checks"], "integration and contact regression suites", report["regressions"]["passed"])
        report["free_fall"] = [free_fall(parameters, counts[0], report["checks"], "coarse"),
                               free_fall(replace(parameters, dt=dt / 2), counts[1], report["checks"], "fine")]
        coarse, fine = report["free_fall"]
        matching = [dict(time=c["time"], fine_time=f["time"], coarse_error=c["signed_error"],
                         fine_error=f["signed_error"], refinement_residual=c["signed_error"] - 2 * f["signed_error"])
                    for c, f in zip(coarse["samples"], fine["samples"][::2])]
        report["matching_samples"] = matching
        check_close(report["checks"], "matching sample times (s)",
                    max(abs(r["time"] - r["fine_time"]) for r in matching), 0, 1e-12)
        check_close(report["checks"], "coarse error minus twice fine error (m)",
                    max(abs(r["refinement_residual"]) for r in matching), 0,
                    coarse["tolerances"]["position"] + 2 * fine["tolerances"]["position"])
        report["bouncing"] = [bouncing(parameters, counts[2], report["checks"], "selected restitution"),
                              bouncing(replace(parameters, restitution=1.0), counts[2], report["checks"], "elastic")]
        report["contact_direction"] = contact_direction(report["checks"])
        report["figures"] = write_plots(report, output)
        forbidden = sorted(name for name in sys.modules if name == "rendering" or name == "pyvista" or name.startswith("pyvista."))
        report["environment"]["forbidden_imports"] = forbidden
        check_true(report["checks"], "no rendering or PyVista imports", not forbidden)
        report["status"] = "passed" if all(c["passed"] for c in report["checks"]) else "failed"
    except Exception:
        report["status"] = "failed"
        report["exception"] = traceback.format_exc()
    result_path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return report
