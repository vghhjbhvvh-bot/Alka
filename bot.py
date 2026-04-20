import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TELEGRAM_BOT_TOKEN
from groq_service import analyze_image

# إعداد التسجيل التفصيلي
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    """الرد على أمر /start"""
    await update.message.reply_text(
        "👋 مرحباً! أرسل لي صورة وسأقوم بتحليلها لك باستخدام Groq AI.\n\n"
        "📸 الصور المدعومة: JPEG, PNG, WEBP\n"
        "💬 التحليل باللغة العربية."
    )

async def handle_photo(update: Update, context: CallbackContext):
    """معالجة الصور المرسلة من المستخدم"""
    user_id = update.effective_user.id
    logger.info(f"تم استلام صورة من المستخدم {user_id}")

    # إعلام المستخدم بأن التحليل جارٍ
    processing_msg = await update.message.reply_text("🔍 جاري تحليل الصورة... انتظر لحظة.")

    # تنزيل الصورة في ملف مؤقت (متوافق مع Railway)
    try:
        photo_file = await update.message.photo[-1].get_file()
    except Exception as e:
        logger.error(f"فشل الحصول على ملف الصورة من تلجرام: {e}")
        await processing_msg.edit_text("❌ لم نتمكن من استلام الصورة. أعد المحاولة.")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        photo_path = tmp_file.name
        try:
            await photo_file.download_to_drive(photo_path)
        except Exception as e:
            logger.error(f"فشل تنزيل الصورة إلى الملف المؤقت: {e}")
            await processing_msg.edit_text("❌ فشل حفظ الصورة مؤقتاً. حاول مرة أخرى.")
            return

    try:
        # تحليل الصورة عبر Groq
        logger.info(f"بدء تحليل الصورة {photo_path} باستخدام النموذج {GROQ_MODEL_NAME}")
        analysis = analyze_image(photo_path)
        await processing_msg.edit_text(f"📷 تحليل الصورة:\n\n{analysis}")
        logger.info(f"تم تحليل الصورة بنجاح للمستخدم {user_id}")
    except Exception as e:
        # طباعة تفاصيل الخطأ في سجلات Railway
        logger.error(f"فشل تحليل الصورة للمستخدم {user_id} - الخطأ: {type(e).__name__} - {str(e)}", exc_info=True)
        # إرسال رسالة مناسبة للمستخدم
        error_message = "❌ عذراً، حدث خطأ أثناء تحليل الصورة."
        if "مفتاح" in str(e) or "API" in str(e):
            error_message += "\n(مشكلة في مفتاح Groq API)"
        elif "نموذج" in str(e):
            error_message += "\n(النموذج غير متاح حالياً)"
        elif "حد الاستخدام" in str(e) or "Rate" in str(e):
            error_message += "\n(تجاوزنا حد الاستخدام المجاني - حاول لاحقاً)"
        elif "اتصال" in str(e) or "Connection" in str(e):
            error_message += "\n(مشكلة في الاتصال بالخادم)"
        await processing_msg.edit_text(error_message)
    finally:
        # حذف الملف المؤقت
        if os.path.exists(photo_path):
            os.remove(photo_path)
            logger.debug(f"تم حذف الملف المؤقت {photo_path}")

def main():
    """تشغيل البوت"""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("لم يتم العثور على TELEGRAM_BOT_TOKEN في متغيرات البيئة")
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY غير موجود. تحليل الصور لن يعمل.")

    # بناء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # بدء الاستماع (Polling)
    logger.info("🤖 البوت يعمل الآن في وضع Polling...")
    application.run_polling()

if __name__ == "__main__":
    # استيراد config هنا لتجنب مشاكل الاستيراد الدائري
    from config import GROQ_MODEL_NAME, GROQ_API_KEY
    main()
