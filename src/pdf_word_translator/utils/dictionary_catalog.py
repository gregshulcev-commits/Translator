"""Built-in catalog of downloadable and bundled dictionary packs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import AppConfig
from .freedict_importer import default_urls_for_pair


@dataclass(frozen=True)
class DictionaryPackSpec:
    pack_id: str
    title: str
    description: str
    source_lang: str
    target_lang: str
    pack_kind: str
    install_mode: str  # "bundled_csv" or "freedict_remote"
    csv_path: Path | None = None
    urls: tuple[str, ...] = ()

    @property
    def direction(self) -> str:
        return f"{self.source_lang}-{self.target_lang}"

    @property
    def category(self) -> str:
        return self.pack_kind

    @property
    def source(self) -> str:
        if self.install_mode == "freedict_remote":
            return self.urls[0] if self.urls else "FreeDict"
        return str(self.csv_path) if self.csv_path else "bundled"


# Backward-compatible alias used by previous iterations.
CatalogDictionaryPack = DictionaryPackSpec


class DictionaryCatalog:
    def __init__(self, config: AppConfig):
        self._config = config

    def all(self) -> list[DictionaryPackSpec]:
        return available_pack_specs(self._config)


def catalog(project_root: Path | AppConfig | None = None) -> DictionaryCatalog:
    if isinstance(project_root, AppConfig):
        return DictionaryCatalog(project_root)
    return DictionaryCatalog(AppConfig())


def available_pack_specs(config: AppConfig) -> list[DictionaryPackSpec]:
    packs_dir = config.bundled_packs_dir
    return [
        DictionaryPackSpec(
            pack_id="freedict_en_ru",
            title="FreeDict общий EN→RU",
            description="Крупный общий словарь FreeDict (скачивается и конвертируется в SQLite).",
            source_lang="en",
            target_lang="ru",
            pack_kind="general",
            install_mode="freedict_remote",
            urls=default_urls_for_pair("en", "ru"),
        ),
        DictionaryPackSpec(
            pack_id="freedict_ru_en",
            title="FreeDict общий RU→EN",
            description="Крупный общий словарь FreeDict для обратного направления.",
            source_lang="ru",
            target_lang="en",
            pack_kind="general",
            install_mode="freedict_remote",
            urls=default_urls_for_pair("ru", "en"),
        ),
        DictionaryPackSpec(
            pack_id="technical_en_ru",
            title="Технический EN→RU",
            description="Небольшой встроенный глоссарий по документации, управлению и электронике.",
            source_lang="en",
            target_lang="ru",
            pack_kind="technical",
            install_mode="bundled_csv",
            csv_path=packs_dir / "technical_en_ru.csv",
        ),
        DictionaryPackSpec(
            pack_id="technical_ru_en",
            title="Технический RU→EN",
            description="Обратный технический глоссарий для чтения русских документов.",
            source_lang="ru",
            target_lang="en",
            pack_kind="technical",
            install_mode="bundled_csv",
            csv_path=packs_dir / "technical_ru_en.csv",
        ),
        DictionaryPackSpec(
            pack_id="literary_en_ru",
            title="Литературный EN→RU",
            description="Компактный художественный словарь для FB2 и художественных текстов.",
            source_lang="en",
            target_lang="ru",
            pack_kind="literary",
            install_mode="bundled_csv",
            csv_path=packs_dir / "literary_en_ru.csv",
        ),
        DictionaryPackSpec(
            pack_id="literary_ru_en",
            title="Литературный RU→EN",
            description="Обратный художественный словарь для RU→EN.",
            source_lang="ru",
            target_lang="en",
            pack_kind="literary",
            install_mode="bundled_csv",
            csv_path=packs_dir / "literary_ru_en.csv",
        ),
    ]


def pack_spec_by_id(config: AppConfig, pack_id: str) -> DictionaryPackSpec:
    for spec in available_pack_specs(config):
        if spec.pack_id == pack_id:
            return spec
    raise KeyError(pack_id)
