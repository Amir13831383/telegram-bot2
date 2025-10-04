import os
import socket
import threading
import asyncio
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ لطفاً TELEGRAM_TOKEN و GEMINI_API_KEY را در Render تنظیم کنید.")

genai.configure(api_key=GEMINI_API_KEY)
logging.basicConfig(level=logging.INFO)

# --- ربات تلگرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 سلام! من یک ربات هوش مصنوعی هستم. سوال بپرس!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = model.generate_content(
            update.message.text,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("متاسفانه نتوانستم پاسخ بدهم.")

async def main_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling(close_loop=False)

# --- فریب Render: یک پورت را برای 5 ثانیه bind کن ---
def fake_http_server():
    port = int(os.environ.get("PORT", 10000))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", port))
        sock.listen(1)
        print(f"✅ پورت {port} برای Render bind شد.")
        # فقط 5 ثانیه باز بمان تا Render متوجه شود
        import time
        time.sleep(5)
    except Exception as e:
        print(f"⚠️ خطا در bind کردن پورت: {e}")
    finally:
        sock.close()

# --- اجرا ---
if __name__ == "__main__":
    # مرحله 1: پورت را bind کن (برای Render)
    fake_http_server()
    
    # مرحله 2: ربات را اجرا کن
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("🤖 ربات تلگرام در حال اجراست...")
    asyncio.run(main_bot())
