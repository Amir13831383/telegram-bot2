import os
import threading
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ لطفاً TELEGRAM_TOKEN و GEMINI_API_KEY را در Render تنظیم کنید.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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
    # غیرفعال کردن stop_signals برای جلوگیری از خطا در thread غیر اصلی
    await app.run_polling(stop_signals=None)

# --- سرور HTTP ساده (در thread جداگانه) ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# --- اجرا ---
if __name__ == "__main__":
    # راه‌اندازی سرور HTTP در یک thread جداگانه
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    print("✅ سرور HTTP در حال اجراست...")
    
    # راه‌اندازی ربات در thread اصلی (که event loop دارد)
    asyncio.run(main_bot())
