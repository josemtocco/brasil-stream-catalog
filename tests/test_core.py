import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gerar_m3u


def test_no_src_dependency():
    assert not (ROOT / "src").exists()
    assert hasattr(gerar_m3u, "run")


def test_bad_name_is_rejected():
    assert gerar_m3u.clean_name("PG Não Informado", "TV Cultura") == "TV Cultura"


def test_channel_name_is_kept():
    assert gerar_m3u.clean_name("TV Cultura") == "TV Cultura"


def test_canonical():
    assert gerar_m3u.canonical("TV Cultura!") == "tvcultura"


def test_m3u_writer(tmp_path, monkeypatch):
    target = tmp_path / "canais.m3u"
    monkeypatch.setattr(gerar_m3u, "PLAYLIST_FILE", target)

    gerar_m3u.write_m3u([{
        "name": "TV Cultura",
        "category": "Cultura",
        "stream": "https://example.com/live.m3u8"
    }])

    content = target.read_text(encoding="utf-8")
    assert "#EXTM3U" in content
    assert 'tvg-name="TV Cultura"' in content
    assert 'group-title="Cultura"' in content
    assert ",TV Cultura" in content
    assert "https://example.com/live.m3u8" in content
