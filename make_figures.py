"""Entry point for future headless numerical validation and figures."""

import sys

from cli import parse_args


def main(argv=None) -> int:
    args = parse_args("Headless validation and figures (not implemented yet).", argv)
    print(
        f"Numerical validation and figures not implemented (Stage 1 scaffold). "
        f"restitution={args.restitution}, dt={args.dt} s. No checks run or plots saved.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
