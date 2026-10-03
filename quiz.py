import os
import json
import hashlib
import requests

from questions import QUESTIONS


PROGRESS_FILE = "progress.json"


def make_hash(questions):
    text = json.dumps(
        questions,
        ensure_ascii=False,
        separators=(",", ":")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_progress():
    with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    question_index = data.get("next_question", 0)

    # Your current file only has next_question.
    # Since Question #2 was just sent, this becomes #3.
    question_number = data.get(
        "question_number",
        question_index + 1
    )

    saved_hash = data.get("sent_prefix_hash")

    # Detect if the question list was replaced.
    if saved_hash is not None and question_index <= len(QUESTIONS):
        current_hash = make_hash(QUESTIONS[:question_index])

        if saved_hash != current_hash:
            print("🔄 New question list detected.")
            question_index = 0

    # If the new list is shorter than the old one,
    # start from the beginning but keep the permanent number.
    if question_index >= len(QUESTIONS):
        question_index = 0

    return question_index, question_number


def save_progress(question_index, question_number):
    data = {
        "next_question": question_index,
        "question_number": question_number,
        "sent_prefix_hash": make_hash(QUESTIONS[:question_index])
    }

    with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


def send_to_discord(question_number, question):
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

    message = (
        "📖 **दैनिक बाइबल क्विज**\n"
        "💭 पहिले आफैं सोच्नुहोस्!\n"
        "🙏 परमेश्वरको वचन सिकौं — "
        "एक प्रश्न प्रतिदिन।\n\n"
        f"📝 **प्रश्न #{question_number}**\n"
        f"## ❓ {question}\n\n"
    )

    response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()


def main():
    question_index, question_number = load_progress()

    question = QUESTIONS[question_index]

    print(f"Sending question #{question_number}")
    print(question)

    send_to_discord(question_number, question)

    save_progress(
        question_index + 1,
        question_number + 1
    )

    print(f"✅ Question #{question_number} sent successfully!")


if __name__ == "__main__":
    main()
