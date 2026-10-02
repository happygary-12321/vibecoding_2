"""Small entry point for the real-time simulation."""

import sys

from cli import parse_args
from state import PhysicsParameters


def main(argv=None) -> int:
    args = parse_args("Real-time circle simulation in an open box.", argv)
    parameters = PhysicsParameters(restitution=args.restitution, dt=args.dt)
    # Help and invalid options finish before the rendering module is imported.
    from rendering import RenderingDependencyError, run_simulation

    try:
        run_simulation(parameters)
    except RenderingDependencyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
