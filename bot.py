import requests
import time
import os
from groq import Groq

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are an expert business idea consultant who helps people develop their business ideas through conversation.

Your conversational style:
- Never analyze everything at once. Instead, ask ONE focused question at a time to understand the idea better.
- Listen carefully to the answers and build on them in the next question.
- Be encouraging but honest — if there's a problem, mention it gently.
- Keep your responses concise and conversational, not like a report.

Follow this natural flow:
1. First, make sure you understand the core idea. Ask what problem it solves.
2. Then explore the target audience — who exactly would use this?
3. Then dig into competition — are there similar solutions out there?
4. Then talk about monetization — how would it make money?
5. Then discuss risks — what could go wrong?
6. Finally, give a brief honest summary of the idea's potential.

Important rules:
- Ask only ONE question per message.
- Never dump a list of questions or a long analysis all at once.
- If the user seems stuck, give a short example to help them think.
- Always respond in English."""

conversation_histories = {}

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except:
        return {"result": []}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_typing(chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
    requests.post(url, json={"chat_id": chat_id, "action": "typing"})

def chat_with_groq(user_id, user_message):
    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_histories[user_id],
        max_tokens=1024
    )

    reply = response.choices[0].message.content

    conversation_histories[user_id].append({
        "role": "assistant",
        "content": reply
    })

    return reply

def main():
    print("✅ Bot started! Press CTRL+C to stop.")
    offset = None

    while True:
        updates = get_updates(offset)

        if updates.get("result"):
            for update in updates["result"]:
                offset = update["update_id"] + 1

                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    user_id = update["message"]["from"]["id"]
                    user_text = update["message"]["text"]

                    print(f"📩 Message ({user_id}): {user_text}")

                    if user_text == "/start":
                        send_message(chat_id,
                            "Hello! I'm your business idea consultant 💡\n\n"
                            "Share your business idea with me and let's analyze it together!\n"
                            "Strengths, risks, market opportunities — let's talk about everything.\n\n"
                            "Type /reset anytime to start a fresh conversation.")
                        continue

                    if user_text == "/reset":
                        conversation_histories.pop(user_id, None)
                        send_message(chat_id, "🔄 Conversation reset. Tell me a new idea!")
                        continue

                    if user_text == "/help":
                        send_message(chat_id,
                            "Here's what I can do:\n\n"
                            "💡 Analyze your business idea\n"
                            "📊 Evaluate market opportunities\n"
                            "⚠️ Identify risks and challenges\n"
                            "🎯 Suggest target audience\n"
                            "💰 Propose monetization strategies\n\n"
                            "Just type your idea and we'll dive in!\n\n"
                            "/reset — Start a new conversation\n"
                            "/help — Show this message")
                        continue

                    send_typing(chat_id)

                    try:
                        reply = chat_with_groq(user_id, user_text)
                        send_message(chat_id, reply)
                    except Exception as e:
                        print(f"Error: {e}")
                        send_message(chat_id, "⚠️ Something went wrong, please try again.")

        time.sleep(1)

if __name__ == "__main__":
    main()