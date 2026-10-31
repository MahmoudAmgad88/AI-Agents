# The CLI translates terminal arguments into application actions. Exit code 0 means success; 1 means failure.
import argparse
import sys

from pydantic import ValidationError

from agent101.config import load_request
from agent101.demo import demo_request
from agent101.policy import PolicyError
from agent101.runner import RunFailure, run


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent101 procurement assistant")
    parser.add_argument("command", choices=["validate", "demo", "run"])
    parser.add_argument(
        "--config",
        default="examples/request.json",
        help="Request JSON for validate or run",
    )
    parser.add_argument("--output", default="outputs")
    args = parser.parse_args()

    try:
        request = demo_request() if args.command == "demo" else load_request(args.config)

        if args.command == "validate":
            print("Request is valid. No API calls were made.")
            return 0

        directory = run(
            request,
            args.output,
            demo=args.command == "demo",
        )
        print(f"Report: {directory / 'report.html'}")
        print(f"Manifest: {directory / 'run.json'}")
        return 0

    except (PolicyError, RunFailure) as exc:
        print(str(exc), file=sys.stderr)
    except (OSError, ValidationError) as exc:
        print(
            f"Configuration or file operation failed: {type(exc).__name__}",
            file=sys.stderr,
        )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
