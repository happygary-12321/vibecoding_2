"""Display the circle with PyVista and schedule fixed physics timesteps.

Notes
-----
Importing this module does not import PyVista or open a window.
Physics coordinates remain meters; actor positions use (x, y, 0) without
scaling. Pixel widths and the 16 ms timer request are display settings.
See assign3/SPEC.md [EQ-STEP], [EQ-TIME], and Section 5's scheduler policy.
"""

from dataclasses import dataclass, field
import math
import sys
from time import perf_counter

from integration import complete_step
from state import Box, CircleState, PhysicsParameters


# Bound work per display callback; excess whole steps are discarded below.
MAX_STEPS_PER_UPDATE = 60


@dataclass
class FixedStepScheduler:
    """Accumulate elapsed seconds and execute at most 60 steps per update.

    Parameters
    ----------
    state : CircleState
        Mutable physics state held by reference.
    parameters : PhysicsParameters
        Fixed physical parameters, including positive dt in s.
    box : Box
        Geometry in m compatible with the selected circle radius.

    Attributes
    ----------
    state : CircleState
        Shared state mutated by advance.
    parameters : PhysicsParameters
        Parameter reference; callers must keep dt fixed.
    box : Box
        Geometry reference used by complete_step.
    accumulator : float
        Retained fractional seconds, initially 0.0; not a constructor option.
    discarded_time : float
        Cumulative discarded whole-step seconds, initially 0.0.
    discarded_steps : int
        Cumulative discarded dimensionless step count, initially 0.
    elapsed_time : float
        Cumulative elapsed seconds supplied to successful updates, initially 0.0.

    Raises
    ------
    ValueError
        If initial state.validate or box.validate_for rejects the inputs.
    OverflowError
        If initial state finiteness checking cannot convert a large integer.

    Notes
    -----
    This is a mutable dataclass. The bookkeeping fields are init=False.
    No GUI or clock is owned here. See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
    Discarded whole steps are not simulated later.
    """
    state: CircleState
    parameters: PhysicsParameters
    box: Box
    accumulator: float = field(default=0.0, init=False)
    discarded_time: float = field(default=0.0, init=False)
    discarded_steps: int = field(default=0, init=False)
    elapsed_time: float = field(default=0.0, init=False)

    def __post_init__(self):
        """Validate the referenced state and geometry after initialization.

        Returns
        -------
        None
            State and geometry are inspected without integration.

        Raises
        ------
        ValueError
            If state validation or radius-dependent geometry validation fails.
        OverflowError
            If initial state finiteness checking cannot convert a large integer.
        """
        self.state.validate()
        self.box.validate_for(self.parameters)

    def advance(self, elapsed: float) -> int:
        """Consume elapsed seconds and advance the shared state by fixed steps.

        Parameters
        ----------
        elapsed : float
            Finite nonnegative interval in s. The total-time/dt quotient must
            also be finite. No explicit scalar type check is performed.

        Returns
        -------
        int
            Number of complete physics steps executed, between 0 and 60.

        Raises
        ------
        ValueError
            If elapsed is negative/nonfinite, the quotient is nonfinite, or
            complete_step rejects the geometry.
        TypeError
            If elapsed does not support the numeric operations used here.

        Notes
        -----
        Mutates state and scheduler counters. Near-integer quotients snap within
        eight ulps; otherwise available steps are floored. Only min(available, 60)
        steps execute. All excess whole steps are discarded; the fractional
        remainder is retained as max(0, total - available * dt).
        dt is not changed and there is no interpolation. An exception during
        stepping does not roll back state. See assign3/SPEC.md [EQ-STEP],
        [EQ-TIME], and Section 5. There is no per-update state validation here.
        """
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("elapsed time must be finite and nonnegative")
        total = self.accumulator + elapsed
        quotient = total / self.parameters.dt
        if not math.isfinite(quotient):
            raise ValueError("elapsed time / dt is too large for the scheduler")
        # Snap within eight ulps of a whole-step boundary to allow arithmetic
        # roundoff; other fractions round down instead of advancing early.
        nearest = round(quotient)
        if abs(quotient - nearest) <= 8 * math.ulp(quotient):
            available = nearest
        else:
            available = math.floor(quotient)
        count = min(available, MAX_STEPS_PER_UPDATE)
        for _ in range(count):
            complete_step(self.state, self.parameters, self.box)
        dropped = available - count
        # Remove ALL available whole steps, including unsimulated backlog.
        # Retain the fraction; clamp tiny negatives caused by boundary snapping.
        self.accumulator = max(0.0, total - available * self.parameters.dt)
        self.discarded_steps += dropped
        self.discarded_time += dropped * self.parameters.dt
        self.elapsed_time += elapsed
        return count


class RenderingDependencyError(RuntimeError):
    """Signal a missing PyVista or VTK dependency during renderer setup.

    Attributes
    ----------
    args : tuple
        Inherited exception-constructor arguments. run_simulation supplies
        one installation-message string, so emitted instances hold a
        one-element tuple. This class defines no additional state.

    Notes
    -----
    This RuntimeError subclass adds no custom attributes or constructor.
    run_simulation raises it for ModuleNotFoundError naming pyvista, vtk,
    or vtkmodules while importing/resolving the plotter. main.main catches
    it, prints the installation message, and returns status 1.
    """


def run_simulation(parameters: PhysicsParameters) -> None:
    """Open a native PyVista window and run until its event loop terminates.

    Parameters
    ----------
    parameters : PhysicsParameters
        Physical constants and fixed dt in s. State and box are created
        internally with their defaults; custom radius must fit that box.

    Returns
    -------
    None
        The function blocks during the GUI session and returns after cleanup.

    Raises
    ------
    RenderingDependencyError
        If PyVista/VTK is missing while the plotter type is resolved.
    ValueError
        If scheduler initialization rejects state or geometry.
    RuntimeError
        If the interactor cannot create a timer.
    Exception
        Other setup/rendering errors propagate. Callback exceptions are
        captured, terminate the loop, and are re-raised with their traceback.

    Notes
    -----
    Lazily imports PyVista, creates meshes/actor/camera/timer, and prints
    versions, settings and final counters. The plotter is closed in finally
    after successful plotter construction. A first timer event sets the
    perf_counter baseline; later events pass elapsed seconds to the scheduler.
    The repeating timer request is 16 ms, not the physical dt.

    The disk center is translated to (state.x, state.y, 0) in world meters,
    with no application coordinate scaling. Wall line widths and window
    dimensions are pixels. The camera is fixed and parallel; the dashed
    upper guide does not collide. Side-wall physics has no height limit.
    For the disk, only actor position changes; its mesh is not rebuilt.
    Updates also change the status text and render the scene.
    Keyboard q/Escape and window closure end the session. The scheduler
    discards whole-step backlog above 60 per update. The label uses literal
    default geometry/radius text even for custom physical parameters.
    See assign3/SPEC.md [EQ-STEP], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
    """
    try:
        import pyvista as pv

        plotter_type = pv.Plotter  # Resolve PyVista's lazy plotting import here.
    except ModuleNotFoundError as exc:
        if (exc.name or "").split(".")[0] not in {"pyvista", "vtk", "vtkmodules"}:
            raise
        raise RenderingDependencyError(
            "PyVista/VTK is missing. Install with the same Python 3.12.10 interpreter:\n"
            f'  "{sys.executable}" -m pip install -r requirements-rendering.txt'
        ) from exc

    state, box = CircleState(), Box()
    scheduler = FixedStepScheduler(state, parameters, box)
    print(f"Python: {sys.version.split()[0]}; PyVista: {pv.__version__}; "
          f"VTK: {'.'.join(map(str, pv.vtk_version_info))}", flush=True)
    print(f"restitution={parameters.restitution}, dt={parameters.dt} s; "
          "close with Q, Escape, or the window close button.", flush=True)
    plotter = plotter_type(window_size=(960, 800), title="Circle in an open box", off_screen=False)
    failure = []
    try:
        plotter.set_background("#f5f7fa")
        # Tessellation affects the visible disk, not radius-based collision tests.
        disk = pv.Disc(center=(0, 0, 0), inner=0, outer=parameters.radius,
                       normal=(0, 0, 1), r_res=1, c_res=96)
        actor = plotter.add_mesh(disk, color="#1676b8", lighting=False, pickable=False)
        actor.position = (state.x, state.y, 0)
        # World coordinates are meters. Line widths are display-only pixels.
        for start, end in (((0, 0, 0), (box.width, 0, 0)),
                           ((0, 0, 0), (0, box.height, 0)),
                           ((box.width, 0, 0), (box.width, box.height, 0))):
            plotter.add_mesh(pv.Line(start, end), color="#27364b", line_width=4, pickable=False)
        # Twenty 55%-filled segments draw a guide, not a collision surface.
        for index in range(20):
            start = index * box.width / 20
            end = start + 0.55 * box.width / 20
            plotter.add_mesh(pv.Line((start, box.height, 0), (end, box.height, 0)),
                             color="#929aa6", line_width=2, pickable=False)
        plotter.add_text("4 m x 3 m | radius 0.2 m | y upward\n"
                         "Dashed upper guide: NO ceiling collision\n"
                         "Fixed view | Q / Escape: close",
                         position="upper_left", font_size=11, color="#27364b")
        status = plotter.add_text("", position=(12, 12), font_size=10, color="#27364b")
        # Fixed parallel framing in world units; physics coordinates pass through.
        # Window/text sizes and offsets above are display settings.
        plotter.camera_position = [(box.width / 2, box.height / 2, 10),
                                   (box.width / 2, box.height / 2, 0), (0, 1, 0)]
        plotter.enable_parallel_projection()
        plotter.camera.parallel_scale = 2.2
        plotter.camera.clipping_range = (0.1, 20)

        interactor = plotter.iren
        # Clear the interaction style and key callbacks before binding exits.
        # No application camera controls follow the fixed framing above.
        interactor.style = None
        interactor.clear_key_event_callbacks()
        plotter.add_key_event("q", interactor.terminate_app)
        plotter.add_key_event("Escape", interactor.terminate_app)
        previous = None

        def update(_caller, _event):
            nonlocal previous
            try:
                now = perf_counter()
                # Start the clock on the first timer event, after scene setup.
                if previous is not None:
                    scheduler.advance(now - previous)
                previous = now
                actor.position = (state.x, state.y, 0)
                status.SetInput(f"Simulation: {state.time(parameters):.2f} s | "
                                f"e={parameters.restitution:g} | dt={parameters.dt:.6g} s\n"
                                f"Discarded backlog: {scheduler.discarded_time:.3f} s "
                                "(overload makes simulation lag wall time)")
                plotter.render()
            except Exception as exc:
                # Carry callback failures across the event-loop boundary; after
                # show returns, re-raise the first with its original traceback.
                failure.append((exc, exc.__traceback__))
                interactor.terminate_app()

        interactor.add_observer("TimerEvent", update)
        interactor.initialize()
        # Display timer requests milliseconds; physics dt remains in seconds.
        timer_id = interactor.create_timer(16, repeating=True)
        if timer_id <= 0:
            raise RuntimeError("VTK could not create the display timer")
        # Enter the native event loop; finally also closes the plotter on errors.
        plotter.show(auto_close=True)
        if failure:
            error, original_traceback = failure[0]
            raise error.with_traceback(original_traceback)
    finally:
        plotter.close()
        print(f"Stopped: steps={state.step_count}, simulation={state.time(parameters):.6g} s, "
              f"discarded={scheduler.discarded_time:.6g} s "
              f"({scheduler.discarded_steps} whole steps), "
              f"remainder={scheduler.accumulator:.6g} s.", flush=True)
