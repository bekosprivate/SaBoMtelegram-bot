import requests
import time
import os
import json
from datetime import datetime
from groq import Groq
from serpapi import GoogleSearch

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

client = Groq(api_key=GROQ_API_KEY)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current information about monetization tools, platforms, affiliate programs, SEO strategies, traffic methods, or any online business topic. Use this before recommending any tool or platform.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query. Be specific. Example: 'best affiliate programs for recipe blogs 2026'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": "Find the latest news about a topic. Use this to find trending topics the user can write about to get SEO traffic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The news search query. Example: 'recipe trends 2026'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_trends",
            "description": "Find Google Trends data for a topic to understand if it's growing or declining in popularity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to check trends for. Example: 'keto diet' or 'AI tools'"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

SYSTEM_PROMPT = f"""Today's date is {datetime.now().strftime("%B %d, %Y")}. Always use this date as reference. Never mention 2024 or any outdated year. Always refer to current year when discussing trends, tools, or strategies.

You are an expert online income consultant and digital marketing advisor. Your job is to help people make real money online.

VERY IMPORTANT: Before recommending ANY tool, platform, affiliate program, or strategy, you MUST use your search tools to research it first. Never recommend something without searching for it first. Always search with the current year in your query.

When a user comes to you, follow this flow:

STEP 1 - UNDERSTAND THEIR SITUATION:
Ask ONE question at a time to understand:
- Do they have a website, blog, YouTube, or social media?
- What is their niche/topic?
- How much traffic do they get?
- Have they tried making money before?

STEP 2 - RESEARCH THEN RECOMMEND:
For every monetization method you want to suggest:
1. First search for it: "best [method] for [their niche] {datetime.now().year}"
2. Check if it's still working well
3. Then recommend it with specific realistic earnings

STEP 3 - SEO & TRAFFIC:
When they need more traffic:
1. Search for trending topics in their niche
2. Search for latest news in their niche
3. Suggest specific article titles they can write

STEP 4 - PROACTIVE THINKING:
Always think ahead:
- If a tool has downsides, search for better alternatives
- If their niche is competitive, search for micro-niches
- Always verify earning claims by searching current data

RULES:
- Ask only ONE question at a time
- ALWAYS search before recommending
- Give specific realistic earnings estimates
- Mention free tools before paid ones
- Be honest if something won't work
- Always use current year {datetime.now().year} in searches and responses
- Always respond in English"""

conversation_histories = {}

def search_web(query):
    try:
        search = GoogleSearch({
            "engine": "google",
            "q": query,
            "num": 5,
            "api_key": SERPAPI_KEY
        })
        results = search.get_dict()
        organic = results.get("organic_results", [])
        if not organic:
            return f"No results found for '{query}'."
        text = f"Search results for '{query}':\n\n"
        for i, item in enumerate(organic[:5], 1):
            title = item.get("title", "")
            snippet = item.get("snippet", "")[:150]
            text += f"{i}. {title}\n   {snippet}\n\n"
        return text
    except Exception as e:
        return f"Search failed: {e}"

def search_news(query):
    try:
        search = GoogleSearch({
            "engine": "google",
            "q": query,
            "tbm": "nws",
            "num": 5,
            "api_key": SERPAPI_KEY
        })
        results = search.get_dict()
        news = results.get("news_results", [])
        if not news:
            return f"No news found for '{query}'."
        text = f"Latest news for '{query}':\n\n"
        for i, item in enumerate(news[:5], 1):
            title = item.get("title", "")
            source = item.get("source", "")
            date = item.get("date", "")
            text += f"{i}. {title}\n   📌 {source} — {date}\n\n"
        return text
    except Exception as e:
        return f"News search failed: {e}"

def search_trends(query):
    try:
        search = GoogleSearch({
            "engine": "google_trends",
            "q": query,
            "api_key": SERPAPI_KEY
        })
        results = search.get_dict()
        interest = results.get("interest_over_time", {}).get("timeline_data", [])
        if not interest:
            return f"No trend data found for '{query}'."
        latest = interest[-1]
        value = latest.get("values", [{}])[0].get("value", "N/A")
        return f"Google Trends interest for '{query}': {value}/100"
    except Exception as e:
        return f"Trends search failed: {e}"

def run_tool(tool_name, tool_args):
    if tool_name == "search_web":
        return search_web(tool_args["query"])
    elif tool_name == "search_news":
        return search_news(tool_args["query"])
    elif tool_name == "search_trends":
        return search_trends(tool_args["query"])
    return "Unknown tool."

def chat_with_groq(user_id, user_message):
    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_histories[user_id]

    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        try:
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=1024
            )
        except Exception as e:
            print(f"Tool call failed, retrying without tools: {e}")
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                max_tokens=1024
            )
            reply = response.choices[0].message.content
            conversation_histories[user_id].append({
                "role": "assistant",
                "content": reply
            })
            return reply

        message = response.choices[0].message

        if message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            })

            for tool_call in message.tool_calls:
                try:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    print(f"🔍 Bot searching: {tool_name}({tool_args})")
                    result = run_tool(tool_name, tool_args)
                except Exception as e:
                    result = f"Search failed: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            reply = message.content
            conversation_histories[user_id].append({
                "role": "assistant",
                "content": reply
            })
            return reply

    return "I had trouble researching that. Could you rephrase your question?"

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
                            "Hello! I'm your online income consultant 💰\n\n"
                            "I help you make real money from your website, blog, or online presence.\n\n"
                            "I research tools and strategies in real-time before recommending anything — so my advice is always current and accurate.\n\n"
                            "Tell me about your website or idea and let's get started!\n\n"
                            "/reset — Start a new conversation\n"
                            "/help — What I can do")
                        continue

                    if user_text == "/reset":
                        conversation_histories.pop(user_id, None)
                        send_message(chat_id, "🔄 Conversation reset. Tell me about your site or idea!")
                        continue

                    if user_text == "/help":
                        send_message(chat_id,
                            "Here's what I can do:\n\n"
                            "💰 Find the best monetization methods for your niche\n"
                            "📈 Research trending topics you can write about\n"
                            "🔍 Find affiliate programs in your niche\n"
                            "🚦 Give you SEO and traffic strategies\n"
                            "🛠 Recommend tools (always researched, never guessed)\n\n"
                            "/reset — Start fresh\n"
                            "/help — This message")
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