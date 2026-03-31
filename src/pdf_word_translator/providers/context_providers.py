"""Optional contextual translation providers used by the compact help panel."""
from __future__ import annotations

from dataclasses import dataclass
import json
import threading
import urllib.error
import urllib.request

from ..models import ContextTranslationResult, TranslationDirection, direction_source_lang, direction_target_lang
from ..plugin_api import ContextTranslationProvider
from ..utils.argos_manager import argos_direction_ready
from ..utils.settings_store import UiSettings


@dataclass(frozen=True)
class ProviderChoice:
    provider_id: str
    display_name: str
    description: str


class DisabledContextProvider(ContextTranslationProvider):
    def provider_id(self) -> str:
        return "disabled"

    def display_name(self) -> str:
        return "Отключено"

    def translate_text(self, text: str, direction: TranslationDirection) -> ContextTranslationResult:
        return ContextTranslationResult(
            provider_id=self.provider_id(),
            provider_name=self.display_name(),
            status="disabled",
            text="Контекстный перевод отключён.",
        )


class ArgosContextProvider(ContextTranslationProvider):
    def provider_id(self) -> str:
        return "argos"

    def display_name(self) -> str:
        return "Argos (офлайн)"

    def translate_text(self, text: str, direction: TranslationDirection) -> ContextTranslationResult:
        ready, message = argos_direction_ready(direction)
        if not ready:
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                text=message,
            )
        try:
            import argostranslate.translate  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                error=str(exc),
                text=message or "Argos недоступен в текущем окружении.",
            )
        try:
            translated = argostranslate.translate.translate(
                text,
                direction_source_lang(direction),
                direction_target_lang(direction),
            )
        except Exception as exc:  # pragma: no cover - optional dependency runtime
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                error=str(exc),
                text=f"Argos не готов: {exc}",
            )
        if not translated.strip():
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="empty",
                text="Argos не вернул результат.",
            )
        return ContextTranslationResult(
            provider_id=self.provider_id(),
            provider_name=self.display_name(),
            status="ok",
            text=translated.strip(),
        )


class LibreTranslateContextProvider(ContextTranslationProvider):
    def __init__(self, base_url: str, api_key: str = ""):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key.strip()

    def provider_id(self) -> str:
        return "libretranslate"

    def display_name(self) -> str:
        return "LibreTranslate"

    def translate_text(self, text: str, direction: TranslationDirection) -> ContextTranslationResult:
        if not self._base_url:
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                text="Укажите URL LibreTranslate в настройках провайдера.",
            )
        payload = {
            "q": text,
            "source": direction_source_lang(direction),
            "target": direction_target_lang(direction),
            "format": "text",
        }
        if self._api_key:
            payload["api_key"] = self._api_key
        request = urllib.request.Request(
            f"{self._base_url}/translate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                text=f"LibreTranslate недоступен: {exc}",
                error=str(exc),
            )
        translated = str(body.get("translatedText", "")).strip()
        if not translated:
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="empty",
                text="LibreTranslate не вернул перевод.",
            )
        return ContextTranslationResult(
            provider_id=self.provider_id(),
            provider_name=self.display_name(),
            status="ok",
            text=translated,
        )


class YandexCloudContextProvider(ContextTranslationProvider):
    def __init__(self, api_key: str = "", folder_id: str = "", iam_token: str = ""):
        self._api_key = api_key.strip()
        self._folder_id = folder_id.strip()
        self._iam_token = iam_token.strip()

    def provider_id(self) -> str:
        return "yandex"

    def display_name(self) -> str:
        return "Yandex Cloud"

    def translate_text(self, text: str, direction: TranslationDirection) -> ContextTranslationResult:
        auth_value = ""
        if self._api_key:
            auth_value = f"Api-Key {self._api_key}"
        elif self._iam_token:
            auth_value = f"Bearer {self._iam_token}"
        else:
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                text="Укажите API-ключ или IAM token Yandex Cloud в настройках провайдера.",
            )
        if not self._folder_id:
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                text="Укажите Folder ID Yandex Cloud в настройках провайдера.",
            )
        payload = {
            "folderId": self._folder_id,
            "texts": [text],
            "sourceLanguageCode": direction_source_lang(direction),
            "targetLanguageCode": direction_target_lang(direction),
            "format": "PLAIN_TEXT",
        }
        request = urllib.request.Request(
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_value,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                details = exc.read().decode("utf-8")
            except Exception:
                details = str(exc)
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                text=f"Yandex Cloud ошибка: {details}",
                error=details,
            )
        except urllib.error.URLError as exc:
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                text=f"Yandex Cloud недоступен: {exc}",
                error=str(exc),
            )
        translations = body.get("translations") or []
        translated = ""
        if translations:
            translated = str(translations[0].get("text", "")).strip()
        if not translated:
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="empty",
                text="Yandex Cloud не вернул перевод.",
            )
        return ContextTranslationResult(
            provider_id=self.provider_id(),
            provider_name=self.display_name(),
            status="ok",
            text=translated,
        )


class ContextTranslationService:
    """Manage provider selection, persistence and background execution."""

    PROVIDER_CHOICES = (
        ProviderChoice("disabled", "Отключено", "Вторая строка показывает только статус или пример словаря."),
        ProviderChoice("argos", "Argos (офлайн)", "Локальная нейронная модель, если установлен argostranslate и EN↔RU модель."),
        ProviderChoice("libretranslate", "LibreTranslate", "HTTP API: локальный или удалённый сервер LibreTranslate."),
        ProviderChoice("yandex", "Yandex Cloud", "Онлайн API с сервисным аккаунтом и API-ключом."),
    )

    def __init__(self, settings: UiSettings):
        self._settings = settings
        self._providers: dict[str, ContextTranslationProvider] = {}
        self._request_counter = 0
        self.update_settings(settings)

    @classmethod
    def provider_choices(cls) -> tuple[ProviderChoice, ...]:
        return cls.PROVIDER_CHOICES

    def update_settings(self, settings: UiSettings) -> None:
        self._settings = settings.normalized()
        self._providers = {
            "disabled": DisabledContextProvider(),
            "argos": ArgosContextProvider(),
            "libretranslate": LibreTranslateContextProvider(
                self._settings.libretranslate_url,
                self._settings.libretranslate_api_key,
            ),
            "yandex": YandexCloudContextProvider(
                api_key=self._settings.yandex_api_key,
                folder_id=self._settings.yandex_folder_id,
                iam_token=self._settings.yandex_iam_token,
            ),
        }

    def active_provider_id(self) -> str:
        return self._settings.context_provider_id

    def provider_name(self, provider_id: str | None = None) -> str:
        provider_id = provider_id or self.active_provider_id()
        provider = self._providers.get(provider_id) or self._providers["disabled"]
        return provider.display_name()

    def provider_for_current_settings(self) -> ContextTranslationProvider:
        return self._providers.get(self.active_provider_id(), self._providers["disabled"])

    def next_request_id(self) -> int:
        self._request_counter += 1
        return self._request_counter

    def translate_async(self, text: str, direction: TranslationDirection, callback, request_id: int | None = None) -> int:
        request_id = request_id or self.next_request_id()
        provider = self.provider_for_current_settings()
        if not text.strip():
            callback(request_id, ContextTranslationResult(provider.provider_id(), provider.display_name(), status="empty", text="—"))
            return request_id

        def worker() -> None:
            result = provider.translate_text(text, direction)
            callback(request_id, result)

        if provider.provider_id() == "disabled":
            worker()
            return request_id

        thread = threading.Thread(target=worker, daemon=True, name=f"context-translate-{request_id}")
        thread.start()
        return request_id
