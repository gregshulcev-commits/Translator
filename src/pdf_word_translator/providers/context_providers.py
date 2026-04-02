"""Optional contextual translation providers used by the compact help panel."""
from __future__ import annotations

from dataclasses import dataclass
import json
import threading
import urllib.error
import urllib.parse
import urllib.request

from ..models import (
    EN_RU,
    RU_EN,
    SUPPORTED_DIRECTIONS,
    ContextTranslationResult,
    TranslationDirection,
    direction_source_lang,
    direction_target_lang,
)
from ..plugin_api import ContextTranslationProvider
from ..utils.argos_manager import argos_direction_ready
from ..utils.settings_store import UiSettings


LIBRETRANSLATE_DEFAULT_URL = "http://127.0.0.1:5000"
LIBRETRANSLATE_PUBLIC_HOSTS = {"libretranslate.com", "www.libretranslate.com"}


@dataclass(frozen=True)
class ProviderChoice:
    provider_id: str
    display_name: str
    description: str


@dataclass(frozen=True)
class ProviderDiagnostic:
    provider_id: str
    state: str
    message: str

    @property
    def ok(self) -> bool:
        return self.state in {"ready", "disabled"}


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
    def __init__(self, base_url: str, api_key: str = "", *, timeout: int = 30):
        self._base_url = normalize_libretranslate_url(base_url)
        self._api_key = api_key.strip()
        self._timeout = max(1, int(timeout))

    def provider_id(self) -> str:
        return "libretranslate"

    def display_name(self) -> str:
        return "LibreTranslate"

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def api_key(self) -> str:
        return self._api_key

    def configuration_status(self) -> ProviderDiagnostic:
        return libretranslate_configuration_diagnostic(self._base_url, self._api_key)

    def translate_text(self, text: str, direction: TranslationDirection) -> ContextTranslationResult:
        diagnostic = self.configuration_status()
        if diagnostic.state == "error":
            return ContextTranslationResult(
                provider_id=self.provider_id(),
                provider_name=self.display_name(),
                status="error",
                text=diagnostic.message,
            )

        payload: dict[str, str] = {
            "q": text,
            "source": direction_source_lang(direction),
            "target": direction_target_lang(direction),
            "format": "text",
        }
        if self._api_key:
            payload["api_key"] = self._api_key

        endpoint = libretranslate_translate_url(self._base_url)
        request_builders = (
            _build_libretranslate_json_request,
            _build_libretranslate_form_request,
        )

        for index, build_request in enumerate(request_builders):
            request = build_request(endpoint, payload)
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:  # nosec B310
                    body = _read_json_response(response)
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
            except urllib.error.HTTPError as exc:
                if index == 0 and exc.code in {400, 415, 422}:
                    continue
                return ContextTranslationResult(
                    provider_id=self.provider_id(),
                    provider_name=self.display_name(),
                    status="error",
                    text=_http_error_message(exc, prefix="LibreTranslate"),
                    error=str(exc),
                )
            except urllib.error.URLError as exc:
                return ContextTranslationResult(
                    provider_id=self.provider_id(),
                    provider_name=self.display_name(),
                    status="error",
                    text=f"LibreTranslate недоступен: {exc}",
                    error=str(exc),
                )
            except ValueError as exc:
                if index == 0:
                    continue
                return ContextTranslationResult(
                    provider_id=self.provider_id(),
                    provider_name=self.display_name(),
                    status="error",
                    text=f"LibreTranslate вернул неожиданный ответ: {exc}",
                    error=str(exc),
                )

        return ContextTranslationResult(
            provider_id=self.provider_id(),
            provider_name=self.display_name(),
            status="error",
            text="LibreTranslate не удалось вызвать через JSON или form-data.",
        )


class YandexCloudContextProvider(ContextTranslationProvider):
    def __init__(self, api_key: str | None = None, folder_id: str | None = None, iam_token: str | None = None):
        self._api_key = str(api_key or "").strip()
        self._folder_id = str(folder_id or "").strip()
        self._iam_token = str(iam_token or "").strip()

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
            with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
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

    def provider_status(
        self,
        direction: TranslationDirection | None = None,
        provider_id: str | None = None,
    ) -> ProviderDiagnostic:
        provider_id = provider_id or self.active_provider_id()
        direction = direction or self._settings.direction
        if provider_id == "disabled":
            return ProviderDiagnostic("disabled", "disabled", "Контекстный перевод отключён.")
        if provider_id == "argos":
            ready, message = argos_direction_ready(direction)
            if ready:
                return ProviderDiagnostic("argos", "ready", "Argos (офлайн): локальная модель установлена и готова к переводу контекста.")
            return ProviderDiagnostic("argos", "error", message)
        if provider_id == "libretranslate":
            return libretranslate_configuration_diagnostic(
                self._settings.libretranslate_url,
                self._settings.libretranslate_api_key,
            )
        if provider_id == "yandex":
            return yandex_configuration_diagnostic(
                api_key=self._settings.yandex_api_key,
                folder_id=self._settings.yandex_folder_id,
                iam_token=self._settings.yandex_iam_token,
            )
        return ProviderDiagnostic(provider_id, "error", f"Неизвестный провайдер контекстного перевода: {provider_id}")

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


def normalize_libretranslate_url(value: str) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""
    if "://" not in raw_value:
        raw_value = f"http://{raw_value}"
    parsed = urllib.parse.urlsplit(raw_value)
    if parsed.scheme.lower() not in {"http", "https"}:
        return raw_value.rstrip("/")
    path = parsed.path.rstrip("/")
    lowered_path = path.lower()
    for suffix in ("/translate", "/languages"):
        if lowered_path.endswith(suffix):
            path = path[: -len(suffix)]
            break
    normalized = parsed._replace(path=path, query="", fragment="")
    return urllib.parse.urlunsplit(normalized).rstrip("/")


def libretranslate_translate_url(base_url: str) -> str:
    normalized = normalize_libretranslate_url(base_url)
    if not normalized:
        return ""
    return f"{normalized}/translate"


def libretranslate_languages_url(base_url: str) -> str:
    normalized = normalize_libretranslate_url(base_url)
    if not normalized:
        return ""
    return f"{normalized}/languages"


def libretranslate_configuration_diagnostic(base_url: str, api_key: str = "") -> ProviderDiagnostic:
    normalized = normalize_libretranslate_url(base_url)
    if not normalized:
        return ProviderDiagnostic(
            provider_id="libretranslate",
            state="error",
            message=(
                "LibreTranslate: укажите адрес сервера, например "
                f"{LIBRETRANSLATE_DEFAULT_URL} или полный endpoint /translate."
            ),
        )

    parsed = urllib.parse.urlsplit(normalized)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ProviderDiagnostic(
            provider_id="libretranslate",
            state="error",
            message=f"LibreTranslate: некорректный адрес сервера: {str(base_url or '').strip() or '—'}.",
        )

    hostname = (parsed.hostname or "").lower()
    if hostname in LIBRETRANSLATE_PUBLIC_HOSTS and not api_key.strip():
        return ProviderDiagnostic(
            provider_id="libretranslate",
            state="error",
            message="LibreTranslate: для libretranslate.com требуется API key. Добавьте ключ или используйте self-hosted сервер.",
        )

    endpoint = libretranslate_translate_url(normalized)
    return ProviderDiagnostic(
        provider_id="libretranslate",
        state="ready",
        message=f"LibreTranslate: endpoint настроен ({endpoint}). Перевод будет выполняться через /translate.",
    )


def yandex_configuration_diagnostic(*, api_key: str = "", folder_id: str = "", iam_token: str = "") -> ProviderDiagnostic:
    if not str(api_key or "").strip() and not str(iam_token or "").strip():
        return ProviderDiagnostic(
            provider_id="yandex",
            state="error",
            message="Yandex Cloud: укажите API key или IAM token.",
        )
    if not str(folder_id or "").strip():
        return ProviderDiagnostic(
            provider_id="yandex",
            state="error",
            message="Yandex Cloud: укажите Folder ID.",
        )
    return ProviderDiagnostic(
        provider_id="yandex",
        state="ready",
        message="Yandex Cloud: ключ авторизации и Folder ID настроены.",
    )


def probe_libretranslate_directions(
    base_url: str,
    api_key: str = "",
    *,
    timeout: int = 8,
    directions: tuple[TranslationDirection, ...] = SUPPORTED_DIRECTIONS,
) -> dict[TranslationDirection, ContextTranslationResult]:
    provider = LibreTranslateContextProvider(base_url, api_key, timeout=timeout)
    samples = {
        EN_RU: "Connection test.",
        RU_EN: "Проверка подключения.",
    }
    results: dict[TranslationDirection, ContextTranslationResult] = {}
    for direction in directions:
        sample_text = samples.get(direction, "Connection test.")
        results[direction] = provider.translate_text(sample_text, direction)
    return results


def _build_libretranslate_json_request(url: str, payload: dict[str, str]) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )


def _build_libretranslate_form_request(url: str, payload: dict[str, str]) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )


def _read_json_response(response) -> dict[str, object]:
    raw_body = response.read()
    if not raw_body:
        return {}
    try:
        body = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("ответ не является JSON") from exc
    if not isinstance(body, dict):
        raise ValueError("ответ имеет неожиданный формат")
    return body


def _extract_error_message(raw_body: bytes, fallback: str = "") -> str:
    text = raw_body.decode("utf-8", errors="replace").strip()
    if not text:
        return fallback
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict):
        for key in ("error", "message", "detail", "details", "description"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return text


def _http_error_message(exc: urllib.error.HTTPError, *, prefix: str) -> str:
    raw_body = b""
    try:
        raw_body = exc.read()
    except Exception:
        raw_body = b""
    details = _extract_error_message(raw_body, fallback=str(exc)).strip()
    if details:
        return f"{prefix} ошибка {exc.code}: {details}"
    return f"{prefix} ошибка {exc.code}"
