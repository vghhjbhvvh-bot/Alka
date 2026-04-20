import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TELEGRAM_BOT_TOKEN
from groq_service import analyze_image

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    """الرد على أمر /start"""
    await update.message.reply_text(
        "👋 مرحباً! أرسل لي صورة وسأقوم بتحليلها لك باستخدام Groq AI.\n\n"
        "📸 الصور المدعومة: JPEG, PNG, WEBP"
    )

async def handle_photo(update: Update, context: CallbackContext):
    """معالجة الصور المرسلة من المستخدم"""
    # إعلام المستخدم بأن التحليل جارٍ
    processing_msg = await update.message.reply_text("🔍 جاري تحليل الصورة... انتظر لحظة.")

    # تنزيل الصورة في ملف مؤقت (متوافق مع Railway)
    photo_file = await update.message.photo[-1].get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        photo_path = tmp_file.name
        await photo_file.download_to_drive(photo_path)

    try:
        # تحليل الصورة عبر Groq
        analysis = analyze_image(photo_path)
        await processing_msg.edit_text(f"📷 تحليل الصورة:\n\n{analysis}")
    except Exception as e:
        logger.error(f"خطأ أثناء تحليل الصورة: {e}")
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء تحليل الصورة. يرجى المحاولة لاحقاً.")
    finally:
        # حذف الملف المؤقت
        if os.path.exists(photo_path):
            os.remove(photo_path)

def main():
    """تشغيل البوت"""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("لم يتم العثور على TELEGRAM_BOT_TOKEN في متغيرات البيئة")

    # بناء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # بدء الاستماع (Polling)
    logger.info("🤖 البوت يعمل الآن...")
    application.run_polling()

if __name__ == "__main__":
    main()
