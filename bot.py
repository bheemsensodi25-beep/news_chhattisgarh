import os
import logging
import urllib.request
import xml.etree.ElementTree as ET
import json
import datetime
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if TOKEN:
    # SUPER CLEAN: Remove ALL whitespace, newlines, and non-printable characters
    TOKEN = re.sub(r'[\s\n\r\t]+', '', TOKEN)
    # Also remove any hidden non-ASCII characters that might be present
    TOKEN = re.sub(r'[^\x20-\x7E]', '', TOKEN)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Store subscribers (In-memory for simplicity)
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subscribers), f)

subscribers = load_subscribers()

def translate_to_hindi(text):
    """Simple translation using Google Translate public API."""
    try:
        safe_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=hi&dt=t&q={safe_text}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data[0][0][0]
    except Exception as e:
        logging.error(f"Translation Error: {e}")
        return "Hindi translation unavailable."

def get_news_message():
    """Fetch and format news message."""
    cg_news = get_news("Chhattisgarh")
    india_news = get_news("India")
    
    if not cg_news and not india_news:
        return None

    response = "📰 **DAILY NEWS UPDATES (8:00 AM)**\n\n"
    
    if cg_news:
        response += "📍 **CHHATTISGARH**\n"
        for item in cg_news:
            response += f"🔹 **English:** {item['english']}\n"
            response += f"🔸 **Hindi:** {item['hindi']}\n"
            response += f"🔗 [Read More]({item['link']})\n\n"
        
    if india_news:
        response += "🇮🇳 **INDIA**\n"
        for item in india_news:
            response += f"🔹 **English:** {item['english']}\n"
            response += f"🔸 **Hindi:** {item['hindi']}\n"
            response += f"🔗 [Read More]({item['link']})\n\n"
        
    response += "Subscribe for more! /news"
    return response

def get_news(topic="Chhattisgarh"):
    """Fetch news from Google News RSS using standard libraries."""
    query = topic.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    news_items = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall(".//item")[:3]:
                title = item.find("title").text
                link = item.find("link").text
                clean_title = title.split(" - ")[0]
                
                hindi_explanation = translate_to_hindi(clean_title)
                
                news_items.append({
                    "english": clean_title,
                    "hindi": hindi_explanation,
                    "link": link
                })
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        
    return news_items

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    
    welcome_text = (
        "👋 **Namaste! I am your Daily News Bot.**\n\n"
        "Ab aapko daily subah **8:00 AM** baje Chhattisgarh aur India ki latest news milenge.\n\n"
        "Commands:\n"
        "🚀 /news - Get news instantly"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Fetching latest news... Please wait.")
    message = get_news_message()
    if message:
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        await update.message.reply_text("Sorry, news fetch nahi ho pa raha hai.")

async def daily_news_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to send daily news to all subscribers."""
    message = get_news_message()
    if message:
        for chat_id in list(subscribers):
            try:
                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
            except Exception as e:
                logging.error(f"Error sending to {chat_id}: {e}")

if __name__ == '__main__':
    # Log the status of environment variables (without showing the token)
    if not TOKEN or TOKEN == "YOUR_TOKEN_HERE":
        print("❌ Error: TELEGRAM_BOT_TOKEN is missing or not set!")
        print("Required: Go to Render Dashboard -> Environment -> Add 'TELEGRAM_BOT_TOKEN'")
    else:
        try:
            # Masked token for logging
            masked = TOKEN[:5] + "..." + TOKEN[-5:] if len(TOKEN) > 10 else "SHORT_TOKEN"
            print(f"✅ Starting bot with cleaned token: {masked}")
            
            application = ApplicationBuilder().token(TOKEN).build()
            
            application.add_handler(CommandHandler('start', start) )
            application.add_handler(CommandHandler('news', news_command))
            
            # Schedule daily news at 8:00 AM
            target_time = datetime.time(hour=8, minute=0, second=0)
            application.job_queue.run_daily(daily_news_job, time=target_time)
            
            print("🚀 Bot is running... Daily news scheduled at 8:00 AM")
            application.run_polling()
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            print("Make sure you installed dependencies with: pip install python-telegram-bot[job-queue]")
