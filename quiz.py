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
SEND_HOUR = 18  # 7 PM Nepal time
MORNING_HOUR = 5  # 7 AM Nepal time


def fingerprint(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_progress():
    progress = {
        "next_number": 1,      # permanent serial number
        "list_pos": 0,         # position inside the current QUESTIONS list
        "first_hash": "",      # identifies which list we are on
        "last_sent_date": "",  # Nepal date of the last successful post
        "last_sent_key": "",
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

    # Decide which slot this run belongs to (Nepal time).
    if now.hour >= SEND_HOUR:
        slot = "evening"
    elif now.hour >= MORNING_HOUR:
        slot = "morning"
    else:
        print("Too early. Skipping.")
        return

    # Never post twice in the same slot on the same day.
    slot_key = f"{today}-{slot}"
    if progress["last_sent_key"] == slot_key:
        print(f"Already sent for {slot_key}. Skipping.")
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
    progress["last_sent_key"] = slot_key
    save_progress(progress)
    print(f"Question #{number} sent.")


if __name__ == "__main__":
    main()
