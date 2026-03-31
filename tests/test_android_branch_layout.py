from __future__ import annotations

from pathlib import Path


def test_android_client_branch_files_exist() -> None:
    project_root = Path(__file__).resolve().parents[1]
    android_root = project_root / "android-client"

    assert (android_root / "settings.gradle.kts").exists()
    assert (android_root / "build.gradle.kts").exists()
    assert (android_root / "app" / "build.gradle.kts").exists()
    assert (android_root / "README.md").exists()
    assert (android_root / "app" / "src" / "main" / "AndroidManifest.xml").exists()
    assert (android_root / "app" / "src" / "main" / "java" / "com" / "oai" / "pdfwordtranslator" / "MainActivity.kt").exists()
    assert (android_root / "app" / "src" / "main" / "java" / "com" / "oai" / "pdfwordtranslator" / "DictionaryBridge.kt").exists()
    assert (android_root / "app" / "src" / "main" / "java" / "com" / "oai" / "pdfwordtranslator" / "PdfPageRenderer.kt").exists()


def test_android_client_includes_bundled_sqlite_assets() -> None:
    project_root = Path(__file__).resolve().parents[1]
    assets_dir = project_root / "android-client" / "app" / "src" / "main" / "assets" / "dictionaries"

    assert (assets_dir / "starter_dictionary.sqlite").exists()
    assert (assets_dir / "starter_dictionary_ru_en.sqlite").exists()


def test_android_client_module_uses_chaquopy_and_shared_python_source() -> None:
    project_root = Path(__file__).resolve().parents[1]
    build_gradle = (project_root / "android-client" / "app" / "build.gradle.kts").read_text(encoding="utf-8")

    assert 'id("com.chaquo.python")' in build_gradle
    assert 'srcDir("../../src")' in build_gradle
    assert 'version = "3.11"' in build_gradle
