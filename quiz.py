import os
import json
import requests

from questions import QUESTIONS


PROGRESS_FILE = "progress.json"


def load_progress():
    with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["next_question"]


def save_progress(next_question):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {"next_question": next_question},
            file,
            ensure_ascii=False,
            indent=4
        )


def send_to_discord(question_number, question):
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

    message = (
        "📖 **दैनिक बाइबल क्विज**\n\n"
        f"📝 **प्रश्न #{question_number}**\n\n"
        f"❓ {question}\n\n"
        "💭 पहिले आफैं सोच्नुहोस्!\n\n"
        "🙏 परमेश्वरको वचन सिकौं — "
        "एक प्रश्न प्रतिदिन।"
    )

    response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()


def main():
    question_index = load_progress()

    if question_index >= len(QUESTIONS):
        print("🎉 All questions have been completed!")
        return

    question_number = question_index + 1
    question = QUESTIONS[question_index]

    print(f"Sending question #{question_number}")
    print(question)

    # Send first.
    send_to_discord(question_number, question)

    # Only update progress AFTER Discord successfully accepts it.
    save_progress(question_index + 1)

    print(f"✅ Question #{question_number} sent successfully!")


if __name__ == "__main__":
    main()