from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from pdf_word_translator.models import EN_RU, RU_EN
from pdf_word_translator.providers.context_providers import ArgosContextProvider
from pdf_word_translator.utils import argos_manager


class _FakeLanguage:
    def __init__(self, code: str) -> None:
        self.code = code
        self._translations: dict[str, object] = {}

    def add_translation(self, target_code: str) -> None:
        self._translations[target_code] = object()

    def get_translation(self, other) -> object | None:
        return self._translations.get(other.code)


class _FakePackage:
    def __init__(self, from_code: str, to_code: str, version: str) -> None:
        self.from_code = from_code
        self.to_code = to_code
        self.package_version = version
        self.package_name = f"translate-{from_code}_{to_code}"
        self.download_url = f"https://example.invalid/{self.package_name}.argosmodel"
        self.download_calls = 0

    def download(self) -> str:
        self.download_calls += 1
        return f"/tmp/{self.package_name}-{self.package_version}.argosmodel"


def _fake_runtime(*, installed_pairs: set[tuple[str, str]], available_versions: dict[tuple[str, str], str]):
    languages = {
        "en": _FakeLanguage("en"),
        "ru": _FakeLanguage("ru"),
    }
    for source_code, target_code in installed_pairs:
        languages[source_code].add_translation(target_code)

    available_packages = [_FakePackage(src, dst, version) for (src, dst), version in available_versions.items()]
    install_calls: list[str] = []
    update_calls: list[str] = []

    def install_from_path(path: str) -> None:
        install_calls.append(path)
        name = Path(path).name
        if "ru_en" in name:
            languages["ru"].add_translation("en")
        if "en_ru" in name:
            languages["en"].add_translation("ru")

    package_module = SimpleNamespace(
        update_package_index=lambda: update_calls.append("updated"),
        get_available_packages=lambda: available_packages,
        install_from_path=install_from_path,
    )
    translate_module = SimpleNamespace(get_installed_languages=lambda: list(languages.values()))

    def fake_import(name: str):
        if name == "argostranslate.package":
            return package_module
        if name == "argostranslate.translate":
            return translate_module
        raise ModuleNotFoundError(name)

    return fake_import, available_packages, install_calls, update_calls


def test_list_argos_models_reports_missing_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_import(_name: str):
        raise ModuleNotFoundError("argostranslate")

    monkeypatch.setattr(argos_manager, "import_module", missing_import)

    state = argos_manager.list_argos_models(update_index=False)

    assert not state.dependency_ready
    assert "argostranslate" in state.dependency_error
    assert [model.direction for model in state.models] == [EN_RU, RU_EN]


def test_list_argos_models_reports_installed_and_available_directions(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_import, packages, _install_calls, update_calls = _fake_runtime(
        installed_pairs={("en", "ru")},
        available_versions={("en", "ru"): "1.2.0", ("ru", "en"): "1.3.0"},
    )
    monkeypatch.setattr(argos_manager, "import_module", fake_import)

    state = argos_manager.list_argos_models(update_index=True)

    assert state.dependency_ready
    assert state.index_updated
    assert update_calls == ["updated"]
    assert state.for_direction(EN_RU).installed is True
    assert state.for_direction(EN_RU).package_version == "1.2.0"
    assert state.for_direction(RU_EN).installed is False
    assert state.for_direction(RU_EN).available_for_download is True
    assert packages[1].package_name in state.for_direction(RU_EN).package_name


def test_install_argos_model_for_direction_downloads_and_installs(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_import, packages, install_calls, update_calls = _fake_runtime(
        installed_pairs=set(),
        available_versions={("ru", "en"): "2.0.0"},
    )
    monkeypatch.setattr(argos_manager, "import_module", fake_import)

    result = argos_manager.install_argos_model_for_direction(RU_EN)

    assert update_calls == ["updated"]
    assert packages[0].download_calls == 1
    assert install_calls == ["/tmp/translate-ru_en-2.0.0.argosmodel"]
    assert result.direction == RU_EN
    assert result.package_version == "2.0.0"


def test_import_argos_model_from_path_marks_new_direction_installed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_import, _packages, install_calls, _update_calls = _fake_runtime(
        installed_pairs={("en", "ru")},
        available_versions={("en", "ru"): "1.0.0", ("ru", "en"): "1.0.0"},
    )
    monkeypatch.setattr(argos_manager, "import_module", fake_import)
    archive = tmp_path / "translate-ru_en-local.argosmodel"
    archive.write_text("stub", encoding="utf-8")

    result = argos_manager.import_argos_model_from_path(archive)

    assert install_calls == [str(archive.resolve())]
    assert result.installed_from_local_file is True
    assert result.direction == RU_EN
    assert result.display_name == "RU → EN"


def test_argos_direction_ready_requires_model(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_import, _packages, _install_calls, _update_calls = _fake_runtime(
        installed_pairs=set(),
        available_versions={("en", "ru"): "1.0.0"},
    )
    monkeypatch.setattr(argos_manager, "import_module", fake_import)

    ready, message = argos_manager.argos_direction_ready(EN_RU)

    assert not ready
    assert "Офлайн-модели Argos" in message


def test_argos_provider_returns_manager_hint_when_model_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pdf_word_translator.providers.context_providers.argos_direction_ready",
        lambda direction: (False, "Откройте «Перевод → Офлайн-модели Argos…»"),
    )
    provider = ArgosContextProvider()

    result = provider.translate_text("Hello world", EN_RU)

    assert not result.ok
    assert "Офлайн-модели Argos" in result.text
