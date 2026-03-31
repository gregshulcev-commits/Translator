"""Helpers for detecting and installing optional Argos Translate models.

The application keeps the core dictionary workflow independent from neural
translation, but the optional Argos provider needs a small amount of lifecycle
management: detect whether the Python package is installed, discover available
models for EN↔RU, install them from the online index, and import local
`.argosmodel` archives from the GUI.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import ModuleType
import re

from ..models import EN_RU, RU_EN, TranslationDirection, direction_source_lang, direction_target_lang

SUPPORTED_ARGOS_DIRECTIONS: tuple[TranslationDirection, ...] = (EN_RU, RU_EN)


class ArgosManagerError(RuntimeError):
    """Raised when the optional Argos runtime or model package is unavailable."""


@dataclass(frozen=True)
class ArgosModelStatus:
    """Status of one supported Argos language direction."""

    direction: TranslationDirection
    from_code: str
    to_code: str
    display_name: str
    installed: bool = False
    available_for_download: bool = False
    package_version: str = ""
    package_name: str = ""
    download_url: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ArgosRuntimeState:
    """High-level state of the optional Argos runtime and supported models."""

    dependency_ready: bool
    dependency_error: str = ""
    index_updated: bool = False
    index_error: str = ""
    models: tuple[ArgosModelStatus, ...] = ()

    def for_direction(self, direction: TranslationDirection) -> ArgosModelStatus | None:
        for model in self.models:
            if model.direction == direction:
                return model
        return None


@dataclass(frozen=True)
class ArgosInstallResult:
    """Result of installing or importing an Argos model."""

    message: str
    direction: str = ""
    display_name: str = ""
    archive_path: str = ""
    installed_from_local_file: bool = False
    package_version: str = ""
    package_name: str = ""


def direction_display(direction: TranslationDirection) -> str:
    return "EN → RU" if direction == EN_RU else "RU → EN"


def list_argos_models(
    *,
    update_index: bool = False,
    directions: tuple[TranslationDirection, ...] = SUPPORTED_ARGOS_DIRECTIONS,
) -> ArgosRuntimeState:
    """Return supported Argos directions and their installation/download status.

    The function is safe to call even when ``argostranslate`` is not installed.
    In that case it returns a descriptive runtime state instead of raising.
    """

    try:
        package_module, translate_module = _load_argos_modules()
    except ArgosManagerError as exc:
        return ArgosRuntimeState(
            dependency_ready=False,
            dependency_error=str(exc),
            models=tuple(_empty_status(direction, notes=str(exc)) for direction in directions),
        )

    installed_pairs = _installed_pairs(translate_module, directions)
    available_map: dict[tuple[str, str], object] = {}
    index_updated = False
    index_error = ""

    try:
        if update_index:
            package_module.update_package_index()
            index_updated = True
        available_packages = list(package_module.get_available_packages())
        available_map = _available_package_map(available_packages)
    except Exception as exc:  # pragma: no cover - depends on optional runtime state
        if update_index:
            index_error = f"Не удалось обновить индекс Argos: {exc}"
        else:
            index_error = (
                "Локальный индекс Argos ещё не загружен. Нажмите «Обновить список из сети» "
                "или используйте tools/install_argos_model.py --list."
            )

    models = []
    for direction in directions:
        from_code = direction_source_lang(direction)
        to_code = direction_target_lang(direction)
        package_obj = available_map.get((from_code, to_code))
        package_name = _package_name(package_obj)
        package_version = _package_version(package_obj)
        download_url = _package_download_url(package_obj)
        installed = (from_code, to_code) in installed_pairs
        available_for_download = package_obj is not None

        notes = ""
        if installed:
            notes = "Модель установлена локально."
        elif available_for_download:
            notes = "Готова к установке из индекса Argos."
        elif index_error:
            notes = index_error
        else:
            notes = "В индексе Argos нет пакета для этого направления."

        models.append(
            ArgosModelStatus(
                direction=direction,
                from_code=from_code,
                to_code=to_code,
                display_name=direction_display(direction),
                installed=installed,
                available_for_download=available_for_download,
                package_version=package_version,
                package_name=package_name,
                download_url=download_url,
                notes=notes,
            )
        )

    return ArgosRuntimeState(
        dependency_ready=True,
        index_updated=index_updated,
        index_error=index_error,
        models=tuple(models),
    )


def install_argos_model_for_direction(direction: TranslationDirection) -> ArgosInstallResult:
    """Download and install an Argos model for one language direction."""

    package_module, _translate_module = _load_argos_modules()
    from_code = direction_source_lang(direction)
    to_code = direction_target_lang(direction)

    try:
        package_module.update_package_index()
        available_packages = list(package_module.get_available_packages())
    except Exception as exc:  # pragma: no cover - network/optional runtime
        raise ArgosManagerError(f"Не удалось обновить индекс Argos: {exc}") from exc

    package_obj = _available_package_map(available_packages).get((from_code, to_code))
    if package_obj is None:
        raise ArgosManagerError(f"Пакет Argos {from_code}->{to_code} не найден в индексе.")

    try:
        archive_path = package_obj.download()
        package_module.install_from_path(archive_path)
    except Exception as exc:  # pragma: no cover - optional runtime download/install
        raise ArgosManagerError(f"Не удалось установить модель {from_code}->{to_code}: {exc}") from exc

    return ArgosInstallResult(
        message=f"Модель Argos установлена: {direction_display(direction)}",
        direction=direction,
        display_name=direction_display(direction),
        archive_path=str(archive_path),
        package_version=_package_version(package_obj),
        package_name=_package_name(package_obj),
    )


def import_argos_model_from_path(source_path: Path) -> ArgosInstallResult:
    """Install an Argos model from a local ``.argosmodel`` archive."""

    source_path = Path(source_path).expanduser().resolve()
    if not source_path.exists():
        raise ArgosManagerError(f"Файл модели не найден: {source_path}")

    before = list_argos_models(update_index=False)
    package_module, _translate_module = _load_argos_modules()
    try:
        package_module.install_from_path(str(source_path))
    except Exception as exc:  # pragma: no cover - optional runtime install
        raise ArgosManagerError(f"Не удалось импортировать модель Argos: {exc}") from exc

    after = list_argos_models(update_index=False)
    before_installed = {model.direction for model in before.models if model.installed}
    newly_installed = next(
        (model for model in after.models if model.installed and model.direction not in before_installed),
        None,
    )
    message = f"Локальная модель импортирована: {source_path.name}"
    direction = ""
    display_name = ""
    if newly_installed is not None:
        direction = newly_installed.direction
        display_name = newly_installed.display_name
        message = f"Локальная модель импортирована: {newly_installed.display_name}"

    return ArgosInstallResult(
        message=message,
        direction=direction,
        display_name=display_name,
        archive_path=str(source_path),
        installed_from_local_file=True,
    )


def argos_direction_ready(direction: TranslationDirection) -> tuple[bool, str]:
    """Return whether the Argos provider can translate in the requested direction."""

    state = list_argos_models(update_index=False, directions=(direction,))
    if not state.dependency_ready:
        return False, (
            "Argos не установлен. Установите optional dependency из requirements-optional.txt, "
            "затем откройте «Перевод → Офлайн-модели Argos…»."
        )
    model = state.for_direction(direction)
    if model is None or not model.installed:
        return False, (
            f"Для направления {direction_display(direction)} ещё нет локальной модели Argos. "
            "Откройте «Перевод → Офлайн-модели Argos…» и установите модель из сети или импортируйте .argosmodel файл."
        )
    return True, ""


def _load_argos_modules() -> tuple[ModuleType, ModuleType]:
    try:
        package_module = import_module("argostranslate.package")
        translate_module = import_module("argostranslate.translate")
    except Exception as exc:  # pragma: no cover - depends on optional dependency presence
        raise ArgosManagerError(
            "Python-пакет argostranslate не установлен в текущем окружении. "
            "Установите optional dependency: python -m pip install -r requirements-optional.txt"
        ) from exc
    return package_module, translate_module


def _installed_pairs(translate_module: ModuleType, directions: tuple[TranslationDirection, ...]) -> set[tuple[str, str]]:
    try:
        installed_languages = list(translate_module.get_installed_languages())
    except Exception:
        return set()

    by_code: dict[str, object] = {}
    for language in installed_languages:
        code = str(getattr(language, "code", "") or "").strip()
        if code:
            by_code[code] = language

    installed_pairs: set[tuple[str, str]] = set()
    for direction in directions:
        from_code = direction_source_lang(direction)
        to_code = direction_target_lang(direction)
        source_language = by_code.get(from_code)
        target_language = by_code.get(to_code)
        if source_language is None or target_language is None:
            continue
        try:
            translation = source_language.get_translation(target_language)
        except Exception:
            translation = None
        if translation is not None:
            installed_pairs.add((from_code, to_code))
    return installed_pairs


def _available_package_map(available_packages: list[object]) -> dict[tuple[str, str], object]:
    grouped: dict[tuple[str, str], list[object]] = {}
    for package_obj in available_packages:
        from_code = str(getattr(package_obj, "from_code", "") or "").strip()
        to_code = str(getattr(package_obj, "to_code", "") or "").strip()
        if not from_code or not to_code:
            continue
        grouped.setdefault((from_code, to_code), []).append(package_obj)

    return {key: _best_package(packages) for key, packages in grouped.items()}


def _best_package(packages: list[object]) -> object:
    if len(packages) == 1:
        return packages[0]
    return max(packages, key=lambda item: (_version_key(_package_version(item)), _package_name(item)))


def _version_key(raw_version: str) -> tuple[object, ...]:
    if not raw_version:
        return (0,)
    parts = []
    for token in re.split(r"[^0-9A-Za-z]+", raw_version):
        if not token:
            continue
        if token.isdigit():
            parts.append(int(token))
        else:
            parts.append(token.lower())
    return tuple(parts) or (0,)


def _package_version(package_obj: object | None) -> str:
    if package_obj is None:
        return ""
    for attr in ("package_version", "version"):
        value = getattr(package_obj, attr, "")
        if value:
            return str(value)
    return ""


def _package_name(package_obj: object | None) -> str:
    if package_obj is None:
        return ""
    for attr in ("package_name", "name"):
        value = getattr(package_obj, attr, "")
        if value:
            return str(value)
    from_code = str(getattr(package_obj, "from_code", "") or "").strip()
    to_code = str(getattr(package_obj, "to_code", "") or "").strip()
    version = _package_version(package_obj)
    base = f"translate-{from_code}_{to_code}" if from_code and to_code else "translate"
    return f"{base} {version}".strip()


def _package_download_url(package_obj: object | None) -> str:
    if package_obj is None:
        return ""
    for attr in ("argos_package_url", "download_url", "package_url", "url"):
        value = getattr(package_obj, attr, "")
        if value:
            return str(value)
    return ""


def _empty_status(direction: TranslationDirection, *, notes: str) -> ArgosModelStatus:
    return ArgosModelStatus(
        direction=direction,
        from_code=direction_source_lang(direction),
        to_code=direction_target_lang(direction),
        display_name=direction_display(direction),
        notes=notes,
    )
