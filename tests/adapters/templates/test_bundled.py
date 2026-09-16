from pathlib import Path

import pytest

from qyro.adapters.templates.bundled import BundledTemplateProvider
from qyro.domain.errors import TemplateUnavailableError
from qyro.domain.project import Binding, TargetPlatform
from qyro.domain.version import Version


class TestBundledTemplateProvider:
    def test_resolve_template_returns_template_directory(self, tmp_path):
        template_dir = (
            tmp_path
            / "pyside6"
            / "x86_64"
        )
        template_dir.mkdir(parents=True)

        provider = BundledTemplateProvider(tmp_path)

        result = provider.resolve_template(
            Binding.PYSIDE6,
            TargetPlatform.X86,
        )

        assert result == template_dir

    def test_resolve_template_uses_ios_platform_name(self, tmp_path):
        template_dir = tmp_path / "pyside6" / "ios"
        template_dir.mkdir(parents=True)

        provider = BundledTemplateProvider(tmp_path)

        result = provider.resolve_template(
            Binding.PYSIDE6,
            TargetPlatform.IPHONE,
        )

        assert result == template_dir

    def test_resolve_template_uses_android_platform_name(self, tmp_path):
        template_dir = tmp_path / "kivy" / "android"
        template_dir.mkdir(parents=True)

        provider = BundledTemplateProvider(tmp_path)

        result = provider.resolve_template(
            Binding.KIVY,
            TargetPlatform.ANDROID,
        )

        assert result == template_dir

    def test_resolve_template_accepts_version(self, tmp_path):
        template_dir = tmp_path / "pyside6" / "x86_64"
        template_dir.mkdir(parents=True)

        provider = BundledTemplateProvider(tmp_path)

        result = provider.resolve_template(
            Binding.PYSIDE6,
            TargetPlatform.X86,
            Version.parse("1.1.0"),
        )

        assert result == template_dir

    def test_resolve_template_raises_when_template_does_not_exist(
        self,
        tmp_path,
    ):
        provider = BundledTemplateProvider(tmp_path)

        with pytest.raises(TemplateUnavailableError):
            provider.resolve_template(
                Binding.PYSIDE6,
                TargetPlatform.X86,
            )