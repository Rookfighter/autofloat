#!python3

import argparse
import subprocess
import logging
from pathlib import Path
import sys
from version import Version

INCREMENT_CHOICES = ["major", "minor", "bugfix"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--increment", choices=INCREMENT_CHOICES, required=True)
    parser.add_argument("-v", "--verbose", help="Show additional output.", action="store_true")
    parser.add_argument("-q", "--quiet", help="Show minimal output.", action="store_true")
    parser.add_argument("filenames", nargs="+")
    return parser.parse_args()


def init_logging(quiet: bool, verbose: bool):
    format = "%(message)s"

    level = logging.INFO
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG

    logging.basicConfig(format=format, level=level)


def get_version() -> dict:
    result = subprocess.run(
        ["git", "describe", "--tags", "--long"], capture_output=True, check=True
    )

    version = result.stdout.decode().strip()
    if len(version) < 5:
        raise RuntimeError(f'invalid output "{version}')

    if version.startswith("v"):
        version = version[1:]

    logging.info("Found version %s", version)

    major, minor, remainder = version.split(".")
    bugfix, _, sha = remainder.split("-")

    return {"major": int(major), "minor": int(minor), "bugfix": int(bugfix), "sha": sha}


def increment_version(version: dict, action: str) -> dict:
    assert action in INCREMENT_CHOICES

    if action == "major":
        return {"major": version["major"] + 1, "minor": 0, "bugfix": 0, "sha": version["sha"]}
    if action == "minor":
        return {
            "major": version["major"],
            "minor": version["minor"] + 1,
            "bugfix": 0,
            "sha": version["sha"],
        }
    if action == "bugfix":
        return {
            "major": version["major"],
            "minor": version["minor"],
            "bugfix": version["bugfix"] + 1,
            "sha": version["sha"],
        }


def write_version(version: Version, path: Path):
        result = subprocess.run(["toml", "set", path, "package.version", version.as_str_short()], check=True, capture_output=True)
        output_str = result.stdout.decode(encoding="utf-8")
        with path.open("w") as f:
            f.write(output_str)

def main():
    args = parse_args()

    init_logging(args.quiet, args.verbose)

    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, check=True)
    status_output = status.stdout.decode(encoding="utf-8")
    if len(status_output) != 0:
        logging.error("Working directory has uncommited changes:\n%s\nAborting", status_output)
        sys.exit(-1)

    version = Version.from_git()

    logging.info("Retrieved version %s from git", version)

    version.increment(args.increment)

    logging.info("New version %s", version)

    for filename in args.filenames:
        filepath = Path(filename).absolute()
        if not filepath.exists():
            logging.warning("%s does not exist, skipping", filepath)

        write_version(version, filepath)

    subprocess.run(["git", "commit", "-a", "-m", f"Release v{version.as_str_short()}"], check=True)
    subprocess.run(["git", "tag", f"v{version.as_str_short()}"], check=True)


if __name__ == "__main__":
    main()
