"""
Core project entities: the Qt binding, the project configuration and the spec
for a generated component.

All the small rules that used to be inlined in `init()` and `create()` live
here now — default bundle id, default base widget per binding, CamelCase
conversion — which means they're unit-testable without a terminal.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from qyro.domain.errors import InvalidComponentTypeError, InvalidBindingError
from qyro.domain.version import Version


def to_camel_case(name: str) -> str:
    """Convert snake_case / kebab-case / spaced names to CamelCase."""
    parts = name.strip().replace("-", " ").replace("_", " ").split()
    return "".join(word[:1].upper() + word[1:] for word in parts)


class AddonModule(str, Enum):
    HOTRL = "hotrl"
    PYDUX = "pydux"
    SENTRY = "sentry-sdk"
    REQUESTS = "requests"


class TargetPlatform(str, Enum):
    IPHONE = "iPhone"
    ANDROID = "Android"
    X86 = "x86"
    APPLE_SILICON = "Apple Silicon"


class Binding(str, Enum):
    PYQT5 = "PyQt5"
    PYQT6 = "PyQt6"
    PYSIDE2 = "PySide2"
    PYSIDE6 = "PySide6"
    KIVY = "Kivy"
    TKINTER = "Tkinter"

    @classmethod
    def values(cls) -> tuple:
        return tuple(b.value for b in cls)

    @classmethod
    def parse(cls, value: str) -> "Binding":
        for binding in cls:
            if binding.value.lower() == str(value).strip().lower():
                return binding
        raise InvalidBindingError(str(value), cls.values())

    @property
    def is_pyside(self) -> bool:
        return self in (Binding.PYSIDE2, Binding.PYSIDE6)

    @property
    def default_base_widget(self) -> str:
        if self.is_pyside:
            return "QWidget"
        if self == Binding.KIVY:
            return "Widget"
        if self == Binding.TKINTER:
            return "Frame"
        return "QtWidget"

    def supports(self, platform: TargetPlatform) -> bool:
        if platform in (
            TargetPlatform.IPHONE,
            TargetPlatform.ANDROID,
        ):
            return self in (
                Binding.KIVY,
                Binding.PYSIDE6,
            )

        if platform == TargetPlatform.X86:
            return True

        if platform == TargetPlatform.APPLE_SILICON:
            return self in (
                Binding.PYSIDE6,
                Binding.KIVY,
                Binding.PYQT6,
                Binding.TKINTER
            )

        return False


@dataclass
class ProjectConfig:
    """Everything `qyro init` needs to scaffold a project."""

    app_name: str
    version: Version
    author: str
    binding: Binding
    mac_bundle_identifier: Optional[str] = None
    addons: list[AddonModule] = field(default_factory=list)
    target_platform: TargetPlatform = TargetPlatform.X86

    DEFAULT_HIDDEN_IMPORTS = ("__future__",)

    @staticmethod
    def suggest_bundle_identifier(app_name: str, author: str) -> str:
        author_part = (author.lower().split() or ["unknown"])[0]
        app_part = "".join(app_name.lower().split())
        return f"com.{author_part}.{app_part}"

    def as_display_dict(self) -> Dict[str, str]:
        """Field -> value, for the confirmation summary. No formatting here."""
        return {
            "App name": self.app_name,
            "Version": str(self.version),
            "Author": self.author,
            "Binding": self.binding.value,
            "Mac bundle identifier": self.mac_bundle_identifier or "(none)",
            "Add-ons": ", ".join(addon.value for addon in self.addons) or "(none)",
            "Target platform": self.target_platform.value,
        }

    def as_template_variables(self) -> Dict[str, object]:
        """Variables substituted into the project template files."""
        return {
            "app_name": self.app_name,
            "author": self.author,
            "mac_bundle_identifier": self.mac_bundle_identifier,
            "python_bindings": self.binding.value,
            "addons": [addon.value for addon in self.addons], # for qyro_runtime info

            # for pyproject.toml
            "addon_dependencies": ",\n".join(
                f'    "{addon.value}"'
                for addon in self.addons
            ),
            "target_platform": self.target_platform.value,
            "version": str(self.version),
        }

    def as_base_settings(self) -> Dict[str, object]:
        """The keys written into <project_location>/settings/base.json."""
        return {
            "app_name": self.app_name,
            "author": self.author,
            "version": str(self.version),
            "binding": self.binding.value,
            "hidden_imports": list(self.DEFAULT_HIDDEN_IMPORTS),
        }


class ComponentType(str, Enum):
    COMPONENT = "component"
    VIEW = "view"

    @classmethod
    def values(cls) -> tuple:
        return tuple(t.value for t in cls)

    @classmethod
    def parse(cls, value: str) -> "ComponentType":
        for member in cls:
            if member.value == str(value).strip().lower():
                return member
        raise InvalidComponentTypeError(str(value), cls.values())

    @property
    def directory_name(self) -> str:
        """components/ or views/."""
        return self.value + "s"


@dataclass
class ComponentSpec:
    """A component or view to be generated."""

    name: str
    type: ComponentType
    binding: Binding
    inherits_from: str

    @property
    def file_name(self) -> str:
        return f"{self.name}.py"

    def template_variables(self) -> Dict[str, str]:
        return {
            "Binding": self.binding.value,
            "Name": self.name,
            "Widget": self.inherits_from,
        }
