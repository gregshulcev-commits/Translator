import pytest
from defusedxml.common import DefusedXmlException

from pathlib import Path

from pdf_word_translator.plugins.dictionary_sqlite import SQLiteDictionaryPlugin
from pdf_word_translator.utils.freedict_importer import build_dictionary_from_freedict_tei, download_freedict_tei


SAMPLE_TEI = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <text>
    <body>
      <entry>
        <form>
          <orth>driver</orth>
          <pron>ˈdraɪvə</pron>
        </form>
        <sense>
          <cit type='trans'>
            <quote>драйвер</quote>
          </cit>
        </sense>
      </entry>
      <entry>
        <form>
          <orth>driver</orth>
        </form>
        <sense>
          <cit type='trans'>
            <quote>водитель</quote>
          </cit>
        </sense>
      </entry>
      <entry>
        <form>
          <orth>configuration</orth>
          <pron>kənˌfɪɡjʊˈreɪʃən</pron>
        </form>
        <sense>
          <cit type='trans'>
            <quote>конфигурация</quote>
          </cit>
        </sense>
      </entry>
    </body>
  </text>
</TEI>
"""


def test_freedict_tei_builds_sqlite_dictionary(tmp_path: Path) -> None:
    tei_path = tmp_path / "sample.tei"
    tei_path.write_text(SAMPLE_TEI, encoding="utf-8")
    db_path = tmp_path / "freedict.sqlite"

    build_dictionary_from_freedict_tei(tei_path, db_path)
    plugin = SQLiteDictionaryPlugin(db_path)

    driver = plugin.lookup("driver")
    assert driver.found
    assert driver.entry is not None
    assert driver.entry.best_translation == "драйвер"
    assert "водитель" in driver.entry.alternative_translations
    assert driver.entry.transcription == "ˈdraɪvə"

    config = plugin.lookup("configurations")
    assert config.found
    assert config.entry is not None
    assert config.entry.best_translation == "конфигурация"


def test_freedict_tei_rejects_xml_entities(tmp_path: Path) -> None:
    tei_path = tmp_path / "malicious.tei"
    tei_path.write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE TEI [
  <!ENTITY xxe "boom">
]>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <text>
    <body>
      <entry>
        <form><orth>driver</orth></form>
        <sense><cit type='trans'><quote>&xxe;</quote></cit></sense>
      </entry>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    db_path = tmp_path / "malicious.sqlite"

    with pytest.raises(DefusedXmlException):
        build_dictionary_from_freedict_tei(tei_path, db_path)


def test_freedict_download_rejects_unsupported_url_schemes(tmp_path: Path) -> None:
    destination = tmp_path / "sample.tei"

    with pytest.raises(RuntimeError, match="Unsupported FreeDict download URL"):
        download_freedict_tei(destination, ["file:///etc/passwd"])

    assert not destination.exists()
