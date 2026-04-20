import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "meta-llama/llama-4-scout-17b-16e-instruct")

# هوية البوت
BOT_NAME = "Titan AI"
BOT_DEVELOPER = "Cryptonblox"

# إعدادات القناة الإجبارية
FORCE_SUBSCRIBE_CHANNEL_ID = "-1003916904381"  # معرف القناة
FORCE_SUBSCRIBE_CHANNEL_URL = "https://t.me/+8pspvZiZ6rwyNWZi"  # استبدل برابط الدعوة لقناتك
