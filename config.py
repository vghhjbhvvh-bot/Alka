import os
import sys

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "meta-llama/llama-4-scout-17b-16e-instruct")

# مفتاح DeepAI API لتحسين الصور
DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")

BOT_NAME = "Titan AI"
BOT_DEVELOPER = "Cryptonblox"

FORCE_SUBSCRIBE_CHANNEL_ID = "-1003916904381"
FORCE_SUBSCRIBE_CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/+8pspvZiZ6rwyNWZi")

def validate_config():
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN غير موجود في متغيرات البيئة")
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY غير موجود في متغيرات البيئة")
    if not DEEPAI_API_KEY:
        errors.append("DEEPAI_API_KEY غير موجود في متغيرات البيئة. احصل عليه مجاناً من deepai.org")
    if errors:
        print("❌ أخطاء في الإعدادات:")
        for err in errors:
            print(f"   - {err}")
        sys.exit(1)

validate_config()
