import json
import http.client
from typing import Optional, Dict, Any, List

from .secrets import load_secrets, get_provider_key


def chat_completion(messages: List[Dict[str, str]], model: str, max_tokens: Optional[int] = None, temperature: float = 0.0, seed: Optional[int] = None) -> str:
    secrets = load_secrets()
    key = get_provider_key(secrets, "openai")
    if not key:
        raise RuntimeError("Missing OpenAI API key in secrets.json or OPENAI_API_KEY")

    baseurl = "/v1/chat/completions"
    call: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if seed is not None:
        call["seed"] = seed
    if max_tokens is not None:
        call["max_tokens"] = max_tokens

    calltxt = json.dumps(call)
    host = "api.openai.com"
    conn = http.client.HTTPSConnection(host)
    conn.request("POST", baseurl, calltxt, headers={
        "Host": host,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    })
    response = conn.getresponse()
    if response.status != 200 or response.reason != "OK":
        try:
            data = json.loads(response.read())
            message = data.get("error", {}).get("message", "")
        except Exception:
            message = ""
        raise RuntimeError(f"OpenAI error {response.status} {response.reason}: {message}")

    rawdata = response.read()
    try:
        data = json.loads(rawdata)
    except Exception:
        raise RuntimeError(f"OpenAI response is not JSON: {rawdata}")
    if "choices" not in data:
        raise RuntimeError("OpenAI response missing 'choices'")
    res = ""
    for ch in data["choices"]:
        if "message" in ch and "content" in ch["message"]:
            res += ch["message"]["content"]
        elif "text" in ch:
            if res:
                res += "\n"
            res += ch["text"].strip()
    conn.close()
    return res


