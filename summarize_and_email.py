import os, sys, re
from pathlib import Path
from typing import List, Dict, Tuple
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
from rss_fetcher import parse_feed, within_window, NewsItem
from timeutils import kst_window
from summarizer import simple_bullets, llm_bullets
from emailer import send_email

KR_KEYS = ["yonhap", "chosun", "hankyung", "maeil", "mk.", "etnews", "the bell", "kdi"]
JP_KEYS = ["nikkei", "nhk", "asahi", "yomiuri", "joneslanglasalle", "realestate.nikkei"]

def load_config(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    out = []
    for p in patterns:
        try:
            out.append(re.compile(p))
        except re.error as e:
            print(f"[WARN] bad regex pattern: {p} ({e})", file=sys.stderr)
    return out

def matches_sections(title: str, desc: str, regexes: List[re.Pattern]) -> bool:
    t = (title or "").strip()
    d = (desc or "").strip()
    hay = t + "\n" + d
    return any(r.search(hay) for r in regexes)

def region_for_source(source: str) -> str:
    s = (source or "").lower()
    if any(k in s for k in KR_KEYS):
        return "Korea"
    if any(k in s for k in JP_KEYS):
        return "Japan"
    return "Other"

def render_email(env, subject: str, grouped: Dict[str, Dict[str, List[Dict]]], window_str: str) -> str:
    tmpl = env.get_template("email.html.j2")
    return tmpl.render(subject=subject, grouped=grouped, window_str=window_str)

def main():
    root = Path(__file__).resolve().parent
    cfg = load_config(root / "config.yaml")

    tz_name = cfg.get("timezone", "Asia/Seoul")
    start_dt, end_dt, local_tz = kst_window(tz_name=tz_name)
    window_str = f"{start_dt.strftime('%Y-%m-%d %H:%M')} ~ {end_dt.strftime('%Y-%m-%d %H:%M')} ({tz_name})"

    filters = cfg.get("filters", {})
    min_title_len = int(filters.get("min_title_len", 12))

    include_patterns = cfg.get("include_sections", [])
    include_regexes = compile_patterns(include_patterns)

    feeds = cfg.get("feeds", [])
    all_items: List[NewsItem] = []
    for f in feeds:
        try:
            items = parse_feed(f["url"], f.get("name", f["url"]))
            for it in items:
                if len(it.title or "") < min_title_len:
                    continue
                if not within_window(it.published, start_dt, end_dt, local_tz):
                    continue
                if not matches_sections(it.title, it.description or "", include_regexes):
                    continue
                all_items.append(it)
        except Exception as e:
            print(f"[WARN] feed {f}: {e}", file=sys.stderr)

    # Deduplicate by link/title
    seen = set()
    deduped: List[NewsItem] = []
    for it in sorted(all_items, key=lambda x: (x.published or ""), reverse=True):
        key = (it.link or "").split("?")[0] + "|" + (it.title or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    # Summaries
    sum_cfg = cfg.get("summarization", {})
    mode = (sum_cfg.get("mode") or "none").lower()
    sys_prompt = sum_cfg.get("llm_prompt", "Summarize in 1-2 Korean bullet points.")

    enriched = []
    for it in deduped:
        bullets = llm_bullets(it.title, it.description or "", it.source, sys_prompt) if mode == "llm"                   else simple_bullets(it.title, it.description or "", it.source)
        when = it.published or ""
        enriched.append({
            "title": it.title,
            "link": it.link,
            "source": it.source,
            "when": when,
            "bullets": bullets,
        })

    # Group by region -> feed name
    grouped: Dict[str, Dict[str, List[Dict]]] = {}
    for it in enriched:
        region = region_for_source(it["source"])
        grouped.setdefault(region, {})
        grouped[region].setdefault(it["source"], []).append(it)

    env = Environment(
        loader=FileSystemLoader(str(root / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    today_str = end_dt.strftime("%Y-%m-%d")
    subj_tmpl = cfg.get("email", {}).get("subject_template", "Daily News {{ date_str }}")
    subject = subj_tmpl.replace("{{ date_str }}", today_str)

    html = render_email(env, subject, grouped, window_str)
    text_fallback = f"{subject}\n\n(HTML 메일에서 보세요.)"

    send_email(subject, html, text_fallback)
    print(f"Sent email with {sum(len(v2) for v in grouped.values() for v2 in v.values())} items. Window: {window_str}")

if __name__ == "__main__":
    main()
