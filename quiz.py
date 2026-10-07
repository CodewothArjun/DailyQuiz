import os
import sys
import json
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from questions import QUESTIONS

PROGRESS_FILE = "progress.json"
NEPAL = ZoneInfo("Asia/Kathmandu")
SEND_HOUR = 19  # 7 PM Nepal time


def fingerprint(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_progress():
    progress = {
        "next_number": 1,      # permanent serial number
        "list_pos": 0,         # position inside the current QUESTIONS list
        "first_hash": "",      # identifies which list we are on
        "last_sent_date": "",  # Nepal date of the last successful post
    }
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            progress.update(json.load(f))
    except FileNotFoundError:
        pass
    return progress


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=4)


def build_message(number, question):
    return (
        "📖 **दैनिक बाइबल क्विज**\n"
        "💭 पहिले आफैं सोच्नुहोस्!\n"
        "🙏 परमेश्वरको वचन सिकौं — एक प्रश्न प्रतिदिन।\n\n"
         f"📝 **प्रश्न #{number}**\n"
        f"## ❓ {question}\n\n"
    )


def send_to_discord(message):
    url = os.environ["DISCORD_WEBHOOK_URL"]
    response = requests.post(url, json={"content": message}, timeout=30)
    response.raise_for_status()


def main():
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    dry_run = os.environ.get("DRY_RUN", "").lower() == "true"
    now = datetime.now(NEPAL)
    today = now.date().isoformat()

    progress = load_progress()

    # Scheduled runs only after 7 PM Nepal time.
    if event == "schedule" and now.hour < SEND_HOUR:
        print("Before 7 PM Nepal time. Skipping.")
        return

    # Never post twice on the same Nepal date.
    if progress["last_sent_date"] == today:
        print("Already sent today. Skipping.")
        return

    if not QUESTIONS:
        print("ERROR: QUESTIONS is empty.")
        sys.exit(1)

    # Detect a replaced list: its first question differs from the saved one.
    # Appending or fixing typos in later questions does NOT trigger this.
    current_first = fingerprint(QUESTIONS[0])
    if progress["first_hash"] and progress["first_hash"] != current_first:
        print("New question list detected. Starting from the top, keeping the serial number.")
        progress["list_pos"] = 0
    progress["first_hash"] = current_first

    if progress["list_pos"] >= len(QUESTIONS):
        print("ERROR: All questions used. Add more questions to questions.py.")
        sys.exit(1)

    number = progress["next_number"]
    question = QUESTIONS[progress["list_pos"]]
    message = build_message(number, question)

    print(f"Question #{number}:\n{message}")

    if dry_run:
        print("Dry run: nothing sent, nothing saved.")
        return

    send_to_discord(message)  # raises on failure, so progress is NOT saved

    progress["next_number"] = number + 1
    progress["list_pos"] += 1
    progress["last_sent_date"] = today
    save_progress(progress)
    print(f"Question #{number} sent.")


if __name__ == "__main__":
    main()
