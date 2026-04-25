import os
import sys
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env إذا وجد
load_dotenv()

# التوكنات الأساسية
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# استخدام نموذج قوي من Groq
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

# مفتاح Hugging Face API للرسم (الخيار الأساسي والوحيد حالياً)
HF_API_KEY = os.getenv("HF_API_KEY")

# إعدادات البوت
BOT_NAME = "Titan AI"
BOT_DEVELOPER = "Cryptonblox"

# إعدادات الاشتراك الإجباري
FORCE_SUBSCRIBE_CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003916904381")
FORCE_SUBSCRIBE_CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/+8pspvZiZ6rwyNWZi")

def validate_config():
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN غير موجود في متغيرات البيئة")
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY غير موجود في متغيرات البيئة")
    if not HF_API_KEY:
        errors.append("HF_API_KEY غير موجود. يرجى توفيره لاستخدام ميزة الرسم عبر Hugging Face")
    
    if errors:
        print("❌ أخطاء في الإعدادات:")
        for err in errors:
            print(f"   - {err}")
        # في بيئة التطوير قد لا نرغب في إيقاف البرنامج فوراً
        # sys.exit(1)
        return False
    return True

validate_config()
