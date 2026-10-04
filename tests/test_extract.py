from src.extract import direct_streams, youtube_urls, page_name

HTML = """
<html><head><meta property="og:title" content="TV Exemplo"></head>
<body><iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>
<script>var stream="https://example.com/live/index.m3u8";</script></body></html>
"""

def test_extract_direct():
    assert direct_streams(HTML,"https://example.com/") == ["https://example.com/live/index.m3u8"]

def test_extract_youtube():
    assert youtube_urls(HTML,"https://example.com/") == ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]

def test_name():
    assert page_name(HTML,"https://example.com/tv-exemplo") == "TV Exemplo"
