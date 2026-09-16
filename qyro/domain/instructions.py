"""
Shell instructions returned by platform adapters.

Before the refactor, the "how does a user install / uninstall / subscribe to
the repo" strings were duplicated across `installer()`, `repo()` and
`upload()`, once per distribution. Now each platform adapter builds these
objects once, and every use case reuses them.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ShellInstructions:
    """A titled block of shell commands to show the user."""

    heading: str = ""
    commands: List[str] = field(default_factory=list)
    footer: str = ""

    def render(self, indent: str = "    ") -> str:
        parts = []
        if self.heading:
            parts.append(self.heading)
        parts.extend(indent + c for c in self.commands)
        if self.footer:
            parts.append(self.footer)
        return "\n".join(parts)


@dataclass
class InstallerResult:
    """Outcome of `qyro installer`."""

    output_file: str
    install: ShellInstructions = field(default_factory=ShellInstructions)
    uninstall: ShellInstructions = field(default_factory=ShellInstructions)
    install_location: str = ""


@dataclass
class RepoResult:
    """Outcome of `qyro repo` — how to test the generated repository locally."""

    setup: ShellInstructions = field(default_factory=ShellInstructions)
    revert: ShellInstructions = field(default_factory=ShellInstructions)


@dataclass
class UploadResult:
    """Outcome of `qyro upload` — how end users install the uploaded app."""

    installer_url: str
    install: ShellInstructions = field(default_factory=ShellInstructions)
    force_update: ShellInstructions = field(default_factory=ShellInstructions)
    notes: List[str] = field(default_factory=list)


@dataclass
class FreezeResult:
    executable_path: str