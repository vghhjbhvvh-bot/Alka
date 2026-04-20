import os

# قراءة متغيرات البيئة من Railway أو ملف .env محلي
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# نموذج الرؤية الصحيح من Groq (Llama 3.2 Vision)
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.2-90b-vision-preview")
