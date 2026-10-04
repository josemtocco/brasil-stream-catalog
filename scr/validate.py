import requests

def validate_stream(url, timeout=12, user_agent="BrasilStreamCatalog/1.0"):
    headers = {
        "User-Agent": user_agent,
        "Accept": "*/*",
        "Range": "bytes=0-2048"
    }
    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        status = r.status_code
        ctype = (r.headers.get("content-type") or "").lower()
        ok = status < 400 and (
            "mpegurl" in ctype or
            "application/vnd.apple.mpegurl" in ctype or
            "dash" in ctype or
            ".m3u8" in r.url.lower() or
            ".mpd" in r.url.lower()
        )
        return {"ok": ok, "status": status, "final_url": r.url, "content_type": ctype}
    except requests.RequestException as exc:
        return {"ok": False, "status": 0, "final_url": url, "content_type": "", "error": str(exc)}
