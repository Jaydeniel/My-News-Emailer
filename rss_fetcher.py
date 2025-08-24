from dataclasses import dataclass
from typing import List, Optional, Callable, Dict
import feedparser
from dateutil import parser as dtparser
from dateutil import tz

@dataclass
class NewsItem:
    title: str
    link: str
    source: str
    published: Optional[str]
    description: Optional[str]

# 언론사별 파서 함수 정의
def parse_default(e, source_name: str) -> NewsItem:
    title = getattr(e, "title", "").strip()
    link = getattr(e, "link", "").strip()
    published = getattr(e, "published", None) or getattr(e, "updated", None)
    description = getattr(e, "summary", None)
    return NewsItem(title=title, link=link, source=source_name, published=published, description=description)

def parse_example_news(e, source_name: str) -> NewsItem:
    # 예시: 특정 언론사에서만 필요한 필드 처리
    title = getattr(e, "title", "").strip()
    link = getattr(e, "link", "").strip()
    published = getattr(e, "pubDate", None) or getattr(e, "published", None)
    description = getattr(e, "description", None)
    return NewsItem(title=title, link=link, source=source_name, published=published, description=description)

# 언론사별 파서 매핑
PARSER_MAP: Dict[str, Callable] = {
    "example_news": parse_example_news,
    # 추가 언론사별 파서 등록
}

def parse_feed(url: str, source_name: str) -> List[NewsItem]:
    feed = feedparser.parse(url)
    items: List[NewsItem] = []
    parser = PARSER_MAP.get(source_name, parse_default)
    for e in feed.entries:
        items.append(parser(e, source_name))
    return items

def within_window(dt_str: Optional[str], start_dt, end_dt, local_tz):
    if not dt_str:
        return False
    try:
        dt = dtparser.parse(dt_str)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=tz.UTC)
        dt_local = dt.astimezone(local_tz)
        return start_dt <= dt_local < end_dt
    except Exception:
        return False
