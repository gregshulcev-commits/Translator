import pytest
from defusedxml.common import DefusedXmlException

from pathlib import Path

from pdf_word_translator.plugins.document_fb2 import Fb2DocumentPlugin
from pdf_word_translator.plugins.document_txt import PlainTextDocumentPlugin


def test_txt_plugin_tokens_search_and_sentence(tmp_path: Path) -> None:
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text(
        "Driver configuration window.\n\nThe system stores configuration values for each device.",
        encoding="utf-8",
    )

    session = PlainTextDocumentPlugin().open(txt_path)
    assert session.page_count() >= 1
    token = next(token for token in session.get_tokens(0) if token.normalized_text == "configuration")
    sentence = session.get_sentence_for_token(token)
    assert "configuration" in sentence.text.lower()
    assert session.search("system")


def test_fb2_plugin_extracts_title_and_body(tmp_path: Path) -> None:
    fb2_path = tmp_path / "book.fb2"
    fb2_path.write_text(
        """<?xml version='1.0' encoding='utf-8'?>
<FictionBook xmlns='http://www.gribuser.ru/xml/fictionbook/2.0'>
  <description>
    <title-info>
      <book-title>Test Manual</book-title>
    </title-info>
  </description>
  <body>
    <section>
      <title><p>Configuration</p></title>
      <p>Driver configuration is described here.</p>
      <p>The system interface is shown below.</p>
    </section>
  </body>
</FictionBook>
""",
        encoding="utf-8",
    )

    session = Fb2DocumentPlugin().open(fb2_path)
    tokens = session.get_tokens(0)
    assert any(token.normalized_text == "configuration" for token in tokens)
    assert session.search("interface")


def test_fb2_plugin_rejects_xml_entities(tmp_path: Path) -> None:
    fb2_path = tmp_path / "malicious.fb2"
    fb2_path.write_text(
        """<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE FictionBook [
  <!ENTITY xxe "boom">
]>
<FictionBook xmlns='http://www.gribuser.ru/xml/fictionbook/2.0'>
  <body>
    <section>
      <p>&xxe;</p>
    </section>
  </body>
</FictionBook>
""",
        encoding="utf-8",
    )

    with pytest.raises(DefusedXmlException):
        Fb2DocumentPlugin().open(fb2_path)
