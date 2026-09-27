import json

from qyro.adapters.persistence.storage import SettingsRepository


def test_loads_base_from_build_settings_when_settings_missing(tmp_path):
    build_settings = tmp_path / "build" / "settings"
    build_settings.mkdir(parents=True)
    (build_settings / "base.json").write_text(
        json.dumps({"app_name": "LegacyApp", "version": "1.2.3"}),
        encoding="utf-8",
    )

    repo = SettingsRepository(project_root=tmp_path)

    assert repo.get("app_name") == "LegacyApp"
    assert repo.get("version") == "1.2.3"


def test_activate_profile_reads_release_from_build_settings(tmp_path):
    build_settings = tmp_path / "build" / "settings"
    build_settings.mkdir(parents=True)
    (build_settings / "base.json").write_text(
        json.dumps({"app_name": "LegacyApp"}),
        encoding="utf-8",
    )
    (build_settings / "release.json").write_text(
        json.dumps(
            {
                "bundle": {
                    "extra_files": ["README.md"],
                    "dmg": {"icon_size": 120},
                }
            }
        ),
        encoding="utf-8",
    )

    repo = SettingsRepository(project_root=tmp_path)
    repo.activate_profile("release")

    bundle = repo.get_optional("bundle", {})
    assert bundle.get("extra_files") == ["README.md"]
    assert bundle.get("dmg", {}).get("icon_size") == 120
