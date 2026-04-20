import os
import logging
import tempfile
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN
from groq_service import analyze_image, chat_with_ai
from image_processor import enhance_image_quality

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# حالات المحادثة
ASK_OPTION, HANDLE_RESPONSE = range(2)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "👋 **مرحباً بك في البوت الأسطوري!**\n\n"
        "🎭 **أرسل صورة** وسأقوم بتحليلها والتعرف على محتواها بدقة أسطورية.\n\n"
        "💬 **أرسل رسالة نصية** للتحدث معي. يمكنني مساعدتك في:\n"
        "   • الإجابة على الأسئلة العامة.\n"
        "   • المساعدة في البرمجة وكتابة الأكواد.\n"
        "   • إنشاء ملفات (مثل `.py`, `.txt`, `.html`).\n\n"
        "🪄 **أرسل صورة مع تعليق** `/enhance` لتحسين جودتها.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    logger.info(f"📸 تم استلام صورة من المستخدم {user_id}")
    processing_msg = await update.message.reply_text("🔍 جاري تحليل الصورة بعمق... قد يستغرق الأمر بضع ثوانٍ.")

    photo_file = await update.message.photo[-1].get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        photo_path = tmp_file.name
        await photo_file.download_to_drive(photo_path)

    try:
        analysis = analyze_image(photo_path)
        await processing_msg.edit_text(analysis, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"✅ تم تحليل الصورة بنجاح للمستخدم {user_id}")
    except Exception as e:
        logger.error(f"❌ فشل تحليل الصورة: {e}", exc_info=True)
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء تحليل الصورة.")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

async def handle_text(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.effective_user.id
    logger.info(f"💬 تم استلام رسالة نصية من المستخدم {user_id}: {user_message[:50]}...")
    processing_msg = await update.message.reply_text("💬 جاري التفكير...")

    try:
        response = chat_with_ai(user_message)
        
        # محاولة اكتشاف ما إذا كان الرد يحتوي على كود لإنشاء ملف
        file_created = await handle_potential_file_creation(update, response)
        
        if not file_created:
            # إذا لم يتم إنشاء ملف، نرسل الرد كنص عادي مع دعم Markdown
            await processing_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
        else:
            await processing_msg.delete()
            
        logger.info(f"✅ تم الرد على المستخدم {user_id} بنجاح")
    except Exception as e:
        logger.error(f"❌ فشل الرد على المستخدم {user_id}: {e}", exc_info=True)
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء معالجة طلبك.")

async def handle_potential_file_creation(update: Update, response: str) -> bool:
    """
    تحليل الرد لاكتشاف ما إذا كان يحتوي على أمر لإنشاء ملف.
    """
    # نمط للبحث عن كتل الأكواد البرمجية
    code_block_pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    
    if not matches:
        return False
    
    for i, (lang, code) in enumerate(matches):
        if not code.strip():
            continue
            
        # تحديد اسم وامتداد الملف
        file_extension = ".txt"
        if lang:
            file_extension = f".{lang}"
        
        filename = f"generated_file_{i}{file_extension}"
        
        # إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=file_extension, encoding='utf-8') as tmp_file:
            tmp_file.write(code.strip())
            tmp_file_path = tmp_file.name
        
        # إرسال الملف للمستخدم
        try:
            with open(tmp_file_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"📄 تم إنشاء الملف: `{filename}`",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"فشل إرسال الملف: {e}")
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    # إرسال الرد النصي بعد الملفات
    text_response = re.sub(code_block_pattern, '', response, flags=re.DOTALL).strip()
    if text_response:
        await update.message.reply_text(text_response, parse_mode=ParseMode.MARKDOWN)
    
    return True

async def handle_enhance_command(update: Update, context: CallbackContext):
    """معالجة أمر /enhance لتحسين جودة الصورة"""
    user_id = update.effective_user.id
    
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(
            "🪄 **استخدام الأمر `/enhance`:**\n"
            "1. قم بالرد على صورة موجودة باستخدام الأمر `/enhance`.\n"
            "2. أو أرسل صورة جديدة مع تعليق `/enhance`.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    processing_msg = await update.message.reply_text("🪄 جاري تحسين جودة الصورة...")
    photo_file = await update.message.reply_to_message.photo[-1].get_file()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        photo_path = tmp_file.name
        await photo_file.download_to_drive(photo_path)

    try:
        enhanced_image = enhance_image_quality(photo_path)
        await update.message.reply_document(
            document=enhanced_image,
            filename="enhanced_image.jpg",
            caption="✨ تم تحسين جودة الصورة بنجاح!"
        )
        await processing_msg.delete()
        logger.info(f"✅ تم تحسين الصورة للمستخدم {user_id}")
    except Exception as e:
        logger.error(f"❌ فشل تحسين الصورة: {e}")
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء تحسين الصورة.")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ لم يتم العثور على TELEGRAM_BOT_TOKEN في متغيرات البيئة")
    if not GROQ_API_KEY:
        logger.warning("⚠️ GROQ_API_KEY غير موجود. تحليل الصور والمحادثة لن يعملا.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("enhance", handle_enhance_command))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.CaptionRegex(r'^/enhance'), handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # معالج للمحادثات متعددة الخطوات (للأسئلة المخصصة)
    conv_handler = ConversationHandler(
        entry_points=[],
        states={},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    logger.info("🤖 البوت الأسطوري يعمل الآن...")
    application.run_polling()

if __name__ == "__main__":
    from config import GROQ_API_KEY
    main()
