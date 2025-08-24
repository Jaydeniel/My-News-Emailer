import os
import requests
from typing import List

def simple_bullets(title: str, summary: str, source: str) -> List[str]:
    base = (summary or title or "").strip().replace("\n", " ")
    if len(base) > 300:
        base = base[:297] + "..."
    bullets = [base]
    if source:
        bullets.append(f"출처: {source}")
    return bullets

def llm_bullets(title: str, summary: str, source: str, system_prompt: str) -> List[str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.environ.get("OPENAI_BASE", "https://api.openai.com/v1")
    if not api_key:
        return simple_bullets(title, summary, source)

    text = f"제목: {title}\n요약/설명: {summary}\n출처: {source}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
    }
    try:
        resp = requests.post(f"{base_url}/chat/completions", json=payload, timeout=30, headers=headers)
        resp.raise_for_status()
        out = resp.json()
        # 응답 구조 확인 및 디버깅 메시지 추가
        if "choices" not in out or not out["choices"]:
            print("OpenAI 응답에 choices가 없습니다:", out)
            return simple_bullets(title, summary, source)
        content = out["choices"][0]["message"]["content"].strip()
        bullets = [line.strip("•- ").strip() for line in content.splitlines() if line.strip()]
        return bullets[:3] if bullets else simple_bullets(title, summary, source)
    except Exception as e:
        print("llm_bullets 예외:", e)
        return simple_bullets(title, summary, source)
