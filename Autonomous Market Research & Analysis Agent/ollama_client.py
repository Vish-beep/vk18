import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from config import OLLAMA_URL, LLM_MODEL, EMBED_MODEL

def _post(path, payload, timeout=180):
    url = OLLAMA_URL.rstrip("/") + path
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        raise RuntimeError(f"Ollama HTTP error {exc.code}: {body[:300]}")
    except URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama at "
            f"{OLLAMA_URL}. Start Ollama with 'ollama serve'. ({exc})"
        )

def generate_text(prompt, model=None, timeout=180):
    result = _post(
        "/api/generate",
        {"model": model or LLM_MODEL, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    answer = result.get("response", "")
    if not answer.strip():
        raise RuntimeError("Ollama returned an empty response.")
    return answer.strip()

def get_embedding(text, model=None, timeout=180):
    result = _post(
        "/api/embeddings",
        {"model": model or EMBED_MODEL, "prompt": text},
        timeout=timeout,
    )
    embedding = result.get("embedding", [])
    if not embedding:
        raise RuntimeError("Ollama returned no embedding.")
    return embedding

def check_ollama():
    try:
        url = OLLAMA_URL.rstrip("/") + "/api/tags"
        with urlopen(url, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
        names = [m.get("name", "") for m in result.get("models", [])]
        return {"ok": True, "models": names}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "models": []}
