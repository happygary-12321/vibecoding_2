"""PyVista scene and fixed-step display scheduling; physics remains in SI units.

Importing this module does not import PyVista or create a window. This keeps the
small scheduler testable with synthetic elapsed times and the standard library.
"""

from dataclasses import dataclass, field
import math
import sys
from time import perf_counter

from integration import complete_step
from state import Box, CircleState, PhysicsParameters


MAX_STEPS_PER_UPDATE = 60


@dataclass
class FixedStepScheduler:
    state: CircleState
    parameters: PhysicsParameters
    box: Box
    accumulator: float = field(default=0.0, init=False)
    discarded_time: float = field(default=0.0, init=False)
    discarded_steps: int = field(default=0, init=False)
    elapsed_time: float = field(default=0.0, init=False)

    def __post_init__(self):
        self.state.validate()
        self.box.validate_for(self.parameters)

    def advance(self, elapsed: float) -> int:
        """Consume one display interval and return the number of physics steps.

        Near-integer quotients are snapped within eight ulps to avoid losing a
        step solely to floating-point addition/division at a timestep boundary.
        Excess whole steps are discarded, while the fractional remainder stays.
        """
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("elapsed time must be finite and nonnegative")
        total = self.accumulator + elapsed
        quotient = total / self.parameters.dt
        if not math.isfinite(quotient):
            raise ValueError("elapsed time / dt is too large for the scheduler")
        nearest = round(quotient)
        if abs(quotient - nearest) <= 8 * math.ulp(quotient):
            available = nearest
        else:
            available = math.floor(quotient)
        count = min(available, MAX_STEPS_PER_UPDATE)
        for _ in range(count):
            complete_step(self.state, self.parameters, self.box)
        dropped = available - count
        self.accumulator = max(0.0, total - available * self.parameters.dt)
        self.discarded_steps += dropped
        self.discarded_time += dropped * self.parameters.dt
        self.elapsed_time += elapsed
        return count


class RenderingDependencyError(RuntimeError):
    """Missing PyVista/VTK, distinct from unexpected programming errors."""


def run_simulation(parameters: PhysicsParameters) -> None:
    """Open the native GUI and run until the user closes it."""
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
        disk = pv.Disc(center=(0, 0, 0), inner=0, outer=parameters.radius,
                       normal=(0, 0, 1), r_res=1, c_res=96)
        actor = plotter.add_mesh(disk, color="#1676b8", lighting=False, pickable=False)
        actor.position = (state.x, state.y, 0)
        # World coordinates are meters. Line widths are display-only pixels.
        for start, end in (((0, 0, 0), (box.width, 0, 0)),
                           ((0, 0, 0), (0, box.height, 0)),
                           ((box.width, 0, 0), (box.width, box.height, 0))):
            plotter.add_mesh(pv.Line(start, end), color="#27364b", line_width=4, pickable=False)
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
        plotter.camera_position = [(box.width / 2, box.height / 2, 10),
                                   (box.width / 2, box.height / 2, 0), (0, 1, 0)]
        plotter.enable_parallel_projection()
        plotter.camera.parallel_scale = 2.2
        plotter.camera.clipping_range = (0.1, 20)

        interactor = plotter.iren
        # No camera style => no rotate/pan/zoom or VTK style keyboard shortcuts.
        # Setting the public property also prevents show() restoring the old style.
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
                # VTK callbacks otherwise print/swallow Python exceptions. Exit
                # the event loop and re-raise with the original traceback below.
                failure.append((exc, exc.__traceback__))
                interactor.terminate_app()

        interactor.add_observer("TimerEvent", update)
        interactor.initialize()
        timer_id = interactor.create_timer(16, repeating=True)
        if timer_id <= 0:
            raise RuntimeError("VTK could not create the display timer")
        # Native event processing keeps the window responsive. Closing the
        # plotter tears down its interactor, timer, observers, and render window.
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
