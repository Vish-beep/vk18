import re
from html import unescape
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

USER_AGENT = "AutonomousMarketResearchAgent/1.0"

def _strip_html(html):
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(html)).strip()

def _search_html(query, max_results=8):
    url = "https://html.duckduckgo.com/html/?q=" + quote(query)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=15) as response:
        html = response.read().decode("utf-8", errors="ignore")
    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        re.I | re.S,
    )
    results = []
    for href, title_html in pattern.findall(html):
        title = _strip_html(title_html)
        if href.startswith("//"):
            href = "https:" + href
        if not href.startswith("http"):
            continue
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue
        results.append({"title": title, "url": href})
        if len(results) >= max_results:
            break
    return results

def validate_url(url):
    try:
        request = Request(
            url,
            headers={"User-Agent": USER_AGENT},
            method="HEAD",
        )
        with urlopen(request, timeout=8) as response:
            return {
                "valid": 200 <= response.status < 400,
                "status": response.status,
                "url": response.geturl(),
            }
    except Exception:
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=8) as response:
                return {
                    "valid": 200 <= response.status < 400,
                    "status": response.status,
                    "url": response.geturl(),
                }
        except HTTPError as exc:
            return {"valid": False, "status": exc.code, "url": url}
        except Exception as exc:
            return {"valid": False, "status": None, "url": url, "error": str(exc)}

def research_topic(topic, max_results=8):
    results = _search_html(topic, max_results=max_results)
    for result in results:
        result["validation"] = validate_url(result["url"])
    return {
        "query": topic,
        "results": results,
        "source_count": len(results),
    }

def format_sources(results):
    lines = []
    for i, item in enumerate(results, start=1):
        lines.append(
            f"[WEB SOURCE {i}] {item['title']}\nURL: {item['url']}\n"
            f"Validated: {item['validation'].get('valid')}"
        )
    return "\n\n".join(lines)
