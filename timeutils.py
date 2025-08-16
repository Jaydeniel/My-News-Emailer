from datetime import datetime, timedelta
from dateutil import tz

def kst_window(now=None, tz_name="Asia/Seoul"):
    local_tz = tz.gettz(tz_name)
    now_local = (now or datetime.now(tz=local_tz)).astimezone(local_tz)
    today_08 = now_local.replace(hour=8, minute=0, second=0, microsecond=0)
    if now_local >= today_08:
        start = today_08 - timedelta(days=1)
        end = today_08
    else:
        start = today_08 - timedelta(days=2)
        end = today_08 - timedelta(days=1)
    return start, end, local_tz
