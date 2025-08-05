from datetime import datetime, timedelta
import pytz
from zoneinfo import ZoneInfo

def convert_to_ist(timestamp_seconds):
    ist = pytz.timezone("Asia/Kolkata")
    dt = datetime.fromtimestamp(timestamp_seconds, pytz.utc)
    return dt.astimezone(ist)

def format_datetime(dt):
    return dt.strftime("%A, %d %B %Y at %I:%M %p")

def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def get_snooze_time(start_time):
    reminder_time = start_time - timedelta(minutes=15)
    return reminder_time.strftime("%I:%M %p")

def should_notify(start_time_ist: datetime, hours_before: int) -> bool:
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    diff = start_time_ist - now
    return timedelta(minutes=0) <= diff <= timedelta(hours=hours_before, minutes=1)

def get_notification_window(start_time_ist):
    """Returns True if we're either 12 hours or 15 minutes before start time"""
    return should_notify(start_time_ist, 12) or should_notify(start_time_ist, 0.25)

