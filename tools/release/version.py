import subprocess
from pathlib import Path


class Version:
    def __init__(self, major: int, minor: int, bugfix: int, build: int, suffix: str):
        self.major = major
        self.minor = minor
        self.bugfix = bugfix
        self.build = build
        self.suffix = suffix

    @staticmethod
    def from_git(cwd: Path = Path.cwd()):
        git_describe = subprocess.run(
            ["git", "describe", "--tags", "--long"], capture_output=True, check=True, cwd=cwd
        )

        output_str = git_describe.stdout.decode().strip()

        if len(output_str) < 5:
            raise RuntimeError(f'invalid output "{output_str}')

        if output_str.startswith("v"):
            output_str = output_str[1:]

        major, minor, remainder = output_str.split(".")
        bugfix, build, sha = remainder.split("-")
        sha = sha[1:]

        return Version(int(major), int(minor), int(bugfix), int(build), sha)

    def increment(self, action: str):
        if action == "major":
            self.major += 1
            self.minor = 0
            self.bugfix = 0
            self.build = 0
            return
        if action == "minor":
            self.minor += 1
            self.bugfix = 0
            self.build = 0
            return
        if action == "bugfix":
            self.bugfix += 1
            self.build = 0
            return

        raise ValueError(f"invalid action {action}")

    def as_str_long(self) -> str:
        result = f"{self.major}.{self.minor}.{self.bugfix}.{self.build}"
        if len(self.suffix) >0:
            result = f"{result}-{self.suffix}"
        return result

    def as_str_short(self) -> str:
        return f"{self.major}.{self.minor}.{self.bugfix}"

    def __repr__(self):
        return self.as_str_long()

