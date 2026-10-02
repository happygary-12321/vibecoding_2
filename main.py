"""Entry point for the future real-time simulation."""

import sys

from cli import parse_args


def main(argv=None) -> int:
    args = parse_args("Real-time circle simulation (not implemented yet).", argv)
    print(
        f"Simulation not implemented (Stage 1 scaffold). "
        f"restitution={args.restitution}, dt={args.dt} s. No window opened.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
