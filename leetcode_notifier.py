import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
import os
import pytz
from dotenv import load_dotenv
from common_utils import convert_to_ist, format_datetime, get_snooze_time, format_duration

# Caching functions
CACHE_FILE = ".cache/notified_contests.json"

def load_notified_contests():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            import json
            return json.load(f)
    return {}

def save_notified_contests(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        import json
        json.dump(data, f, indent=4)

def should_notify(contest_id, when):
    cache = load_notified_contests()
    key = f"{contest_id}_{when}"
    return key not in cache

def mark_notified(contest_id, when):
    cache = load_notified_contests()
    key = f"{contest_id}_{when}"
    cache[key] = True
    save_notified_contests(cache)

# Load secrets from .env
load_dotenv()
TO_EMAIL = os.getenv("TO_EMAIL")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("APP_PASSWORD")
TIMEZONE = "Asia/Kolkata"

def fetch_upcoming_leetcode_contests():
    url = "https://leetcode.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0"
    }
    query = {
        "operationName": "upcomingContests",
        "query": """
            query upcomingContests {
                upcomingContests {
                    title
                    titleSlug
                    startTime
                    duration
                }
            }
        """,
        "variables": {}
    }

    res = requests.post(url, json=query, headers=headers)
    print("Status Code:", res.status_code)

    try:
        data = res.json()
    except Exception as e:
        print("Error parsing JSON:", e)
        print("Raw text response:", res.text)
        return []

    if "data" not in data or "upcomingContests" not in data["data"]:
        print("⚠️ LeetCode did not return contest data.")
        return []

    return data["data"]["upcomingContests"]

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, APP_PASSWORD)
        server.send_message(msg)
        print("✅ Email sent!")

def main():
    contests = fetch_upcoming_leetcode_contests()
    if not contests:
        print("No contests found.")
        return

    for contest in contests:
        contest_id = contest["titleSlug"]
        start_utc = datetime.fromtimestamp(contest["startTime"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff_hours = (start_utc - now).total_seconds() / 3600

        start_ist = convert_to_ist(contest["startTime"])
        duration = format_duration(contest["duration"])
        link = f"https://leetcode.com/contest/{contest['titleSlug']}"
        formatted_time = format_datetime(start_ist)

        subject = f"LeetCode Contest Reminder: {contest['title']}"
        body = (
            f"🔹 {contest['title']}\n"
            f"📅 Starts at: {formatted_time} IST\n"
            f"⏳ Duration: {duration}\n"
            f"🔗 Link: {link}\n"
        )

        if 11.9 <= time_diff_hours <= 12.1 and should_notify(contest_id, "12h"):
            send_email(subject + " (12 Hour Notice)", body)
            mark_notified(contest_id, "12h")
            print(f"✅ Sent 12h reminder for {contest_id}")

        elif 0.2 <= time_diff_hours <= 0.3 and should_notify(contest_id, "15min"):
            send_email(subject + " (15 Minute Notice)", body)
            mark_notified(contest_id, "15min")
            print(f"✅ Sent 15min reminder for {contest_id}")

        else:
            print(f"⏳ No reminder to send for '{contest['title']}' ({contest_id}). "
                  f"Time left: {round(time_diff_hours, 2)} hours")

if __name__ == "__main__":
    main()
