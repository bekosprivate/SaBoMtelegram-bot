import requests
import time
import os
from groq import Groq
from serpapi import GoogleSearch

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are an expert business idea consultant who helps people develop their business ideas through conversation.

You have access to real-time data — when needed, the system will provide you with current trends, news, and competitor information. Use this data naturally in your responses.

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

Special commands the user can use:
- /trends [topic] — find viral trends about a topic
- /news [topic] — find latest news about a topic
- /competitors [topic] — find competitors in a market

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

def get_trends(topic):
    try:
        search = GoogleSearch({
            "engine": "google_trends",
            "q": topic,
            "api_key": SERPAPI_KEY
        })
        results = search.get_dict()
        interest = results.get("interest_over_time", {}).get("timeline_data", [])
        if not interest:
            return f"No trend data found for '{topic}'."
        latest = interest[-1]
        value = latest.get("values", [{}])[0].get("value", "N/A")
        return f"📈 Google Trends interest for '{topic}': {value}/100 (latest data)"
    except Exception as e:
        return f"Could not fetch trends: {e}"

def get_news(topic):
    try:
        search = GoogleSearch({
            "engine": "google",
            "q": topic,
            "tbm": "nws",
            "num": 5,
            "api_key": SERPAPI_KEY
        })
        results = search.get_dict()
        news_results = results.get("news_results", [])
        if not news_results:
            return f"No news found for '{topic}'."
        news_text = f"📰 Latest news about '{topic}':\n\n"
        for i, item in enumerate(news_results[:5], 1):
            title = item.get("title", "No title")
            source = item.get("source", "Unknown")
            date = item.get("date", "")
            news_text += f"{i}. {title}\n   📌 {source} {date}\n\n"
        return news_text
    except Exception as e:
        return f"Could not fetch news: {e}"

def get_competitors(topic):
    try:
        search = GoogleSearch({
            "engine": "google",
            "q": f"top companies {topic} startups",
            "num": 5,
            "api_key": SERPAPI_KEY
        })
        results = search.get_dict()
        organic = results.get("organic_results", [])
        if not organic:
            return f"No competitor data found for '{topic}'."
        comp_text = f"🏢 Competitors in '{topic}':\n\n"
        for i, item in enumerate(organic[:5], 1):
            title = item.get("title", "No title")
            snippet = item.get("snippet", "")[:120]
            comp_text += f"{i}. {title}\n   {snippet}...\n\n"
        return comp_text
    except Exception as e:
        return f"Could not fetch competitors: {e}"

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
                            "Share your business idea and let's build it together!\n\n"
                            "I can also help you with real-time data:\n"
                            "🔥 /trends [topic] — e.g. /trends coffee shop\n"
                            "📰 /news [topic] — e.g. /news electric cars\n"
                            "🏢 /competitors [topic] — e.g. /competitors food delivery\n\n"
                            "Type /reset to start a fresh conversation.")
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
                            "Real-time data commands:\n"
                            "🔥 /trends [topic]\n"
                            "📰 /news [topic]\n"
                            "🏢 /competitors [topic]\n\n"
                            "/reset — Start a new conversation\n"
                            "/help — Show this message")
                        continue

                    if user_text.startswith("/trends "):
                        topic = user_text[8:].strip()
                        send_typing(chat_id)
                        result = get_trends(topic)
                        send_message(chat_id, result)
                        continue

                    if user_text.startswith("/news "):
                        topic = user_text[6:].strip()
                        send_typing(chat_id)
                        result = get_news(topic)
                        send_message(chat_id, result)
                        continue

                    if user_text.startswith("/competitors "):
                        topic = user_text[13:].strip()
                        send_typing(chat_id)
                        result = get_competitors(topic)
                        send_message(chat_id, result)
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