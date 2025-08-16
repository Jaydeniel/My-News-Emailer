from dataclasses import dataclass
from typing import List, Optional
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

def parse_feed(url: str, source_name: str) -> List[NewsItem]:
    feed = feedparser.parse(url)
    items: List[NewsItem] = []
    for e in feed.entries:
        title = getattr(e, "title", "").strip()
        link = getattr(e, "link", "").strip()
        published = getattr(e, "published", None) or getattr(e, "updated", None)
        description = getattr(e, "summary", None)
        items.append(NewsItem(title=title, link=link, source=source_name, published=published, description=description))
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
