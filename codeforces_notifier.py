import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import os
import json
from dotenv import load_dotenv
from common_utils import convert_to_ist, format_datetime, get_snooze_time, format_duration



CACHE_FILE = ".cache/notified_contests.json"


# Load environment variables from .env file
load_dotenv()

TO_EMAIL = os.environ["TO_EMAIL"]
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
APP_PASSWORD = os.environ["APP_PASSWORD"]
TIMEZONE = "Asia/Kolkata"

if not (TO_EMAIL and EMAIL_ADDRESS and APP_PASSWORD):
    raise ValueError("Missing required email environment variables.")

def get_codeforces_upcoming_contests():
    url = "https://codeforces.com/api/contest.list"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"⚠️ Error: Received status code {response.status_code}")
        return []

    data = response.json()
    if data["status"] != "OK":
        print("⚠️ API returned an error status.")
        return []

    contests = data["result"]
    upcoming = [c for c in contests if c["phase"] == "BEFORE"]
    upcoming.sort(key=lambda x: x["startTimeSeconds"])
    return upcoming

def prepare_email_content():
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).date()
    contests = get_codeforces_upcoming_contests()

    if not contests:
        return "No Upcoming Codeforces Contests", "Hey there! There are no upcoming contests scheduled on Codeforces."

    today_contests = []
    next_contest = None

    for contest in contests:
        start_time = convert_to_ist(contest["startTimeSeconds"])
        duration = format_duration(contest["durationSeconds"])
        link = f"https://codeforces.com/contests/{contest['id']}"
        if start_time.date() == today:
            today_contests.append(
                f"\n👉 <b>{contest['name']}</b>\n   🕒 Time: {format_datetime(start_time)} IST\n   🕑 Duration: {duration}\n   🔗 Link: {link}\n   ⏰ Reminder: {get_snooze_time(start_time)} IST"
            )
        elif not next_contest:
            next_contest = (
                f"<b>{contest['name']}</b>\n🗓 Date: {format_datetime(start_time)} IST\n🕑 Duration: {duration}\n🔗 Link: {link}\n⏰ Reminder: {get_snooze_time(start_time)} IST"
            )

    if today_contests:
        subject = "Codeforces Contest(s) Today!"
        body = "Hey there! Here are today's Codeforces contests:\n" + "\n".join(today_contests)
    elif next_contest:
        subject = "Next Codeforces Contest Info"
        body = f"Hey there! No contests today. But here’s the next one:\n\n{next_contest}"
    else:
        subject = "No Upcoming Codeforces Contests"
        body = "Hey there! There are no upcoming contests scheduled on Codeforces."

    return subject, body

def send_email(subject, body, to_email, from_email, app_password):
    msg = MIMEText(body, 'plain')
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, app_password)
        server.sendmail(from_email, [to_email], msg.as_string())

def load_notified_contests():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            # If file is corrupted or not valid JSON, reset it
            return {}
    return {}


def save_notified_contests(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
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


if __name__ == "__main__":
    contests = get_codeforces_upcoming_contests()
    print(contests)
    if not contests:
        print("No contests found.")
        exit()

    for contest in contests:
        contest_id = contest["id"]
        start_time = datetime.fromtimestamp(contest["startTimeSeconds"], pytz.timezone(TIMEZONE))
        now = datetime.now(pytz.timezone(TIMEZONE))
        time_diff = (start_time - now).total_seconds() / 3600  # in hours

        if 11.5 <= time_diff <= 12.5 and should_notify(contest_id, "12h"):
            subject, body = prepare_email_content()
            send_email(subject, body, TO_EMAIL, EMAIL_ADDRESS, APP_PASSWORD)
            print(f"✅ 12-hour reminder sent for Codeforces contest {contest_id}")
            mark_notified(contest_id, "12h")

        elif 0.1 <= time_diff <= 0.5 and should_notify(contest_id, "15min"):
            subject, body = prepare_email_content()
            send_email(subject, body, TO_EMAIL, EMAIL_ADDRESS, APP_PASSWORD)
            print(f"✅ 15-minute reminder sent for Codeforces contest {contest_id}")
            mark_notified(contest_id, "15min")
        else:
            print(f"⏳ No reminder to send for contest '{contest['name']}' ({contest_id}). "
                  f"Time left: {round(time_diff, 2)} hours")


