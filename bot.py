import os
import logging
import tempfile
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, BOT_NAME, BOT_DEVELOPER, FORCE_SUBSCRIBE_CHANNEL_ID, FORCE_SUBSCRIBE_CHANNEL_URL
from groq_service import analyze_image, chat_with_ai
from image_processor import enhance_image_quality_legendary
from subscription import check_user_subscription, send_subscription_prompt, subscription_button_callback

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# قاموس لتخزين آخر صورة مرسلة من كل مستخدم (لتحسين الصور بالإشارة)
user_last_photo = {}

async def start(update: Update, context: CallbackContext):
    """الرد على أمر /start"""
    user_id = update.effective_user.id
    logger.info(f"🚀 مستخدم جديد بدأ البوت: {user_id}")

    # التحقق من الاشتراك الإجباري أولاً
    if not await check_user_subscription(update, context, FORCE_SUBSCRIBE_CHANNEL_ID):
        await send_subscription_prompt(update, context, FORCE_SUBSCRIBE_CHANNEL_URL)
        return

    # المستخدم مشترك، أرسل رسالة الترحيب الكاملة
    await update.message.reply_text(
        f"👋 **مرحباً بك في {BOT_NAME}!**\n"
        f"تم تطويري بواسطة **{BOT_DEVELOPER}**.\n\n"
        "🎭 **أرسل صورة** وسأقوم بتحليلها والتعرف على محتواها بدقة أسطورية.\n\n"
        "💬 **تحدث معي بشكل طبيعي**، يمكنني:\n"
        "   • الإجابة على أسئلتك.\n"
        "   • مساعدتك في البرمجة وإنشاء الملفات.\n"
        "   • **تحسين جودة الصور** (فقط أرسل صورة ثم قل 'حسن الصورة' أو 'حسن هذه الصورة').\n\n"
        "استمتع! 🚀",
        parse_mode=ParseMode.MARKDOWN
    )


async def about(update: Update, context: CallbackContext):
    """الرد على أمر /about"""
    user_id = update.effective_user.id

    # التحقق من الاشتراك الإجباري أولاً
    if not await check_user_subscription(update, context, FORCE_SUBSCRIBE_CHANNEL_ID):
        await send_subscription_prompt(update, context, FORCE_SUBSCRIBE_CHANNEL_URL)
        return

    await update.message.reply_text(
        f"🤖 **{BOT_NAME}**\n"
        f"مطور البوت: **{BOT_DEVELOPER}**\n\n"
        "إمكانياتي:\n"
        "• تحليل الصور والتعرف على الشخصيات والألعاب والمعالم.\n"
        "• محادثة ذكية ومساعدة في البرمجة.\n"
        "• تحسين جودة الصور بشكل أسطوري (فقط أرسل صورة ثم اطلب تحسينها).\n\n"
        "استمتع باستخدامي! 💪",
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_photo(update: Update, context: CallbackContext):
    """معالجة الصور المرسلة من المستخدم"""
    user_id = update.effective_user.id

    # التحقق من الاشتراك الإجباري أولاً
    if not await check_user_subscription(update, context, FORCE_SUBSCRIBE_CHANNEL_ID):
        await send_subscription_prompt(update, context, FORCE_SUBSCRIBE_CHANNEL_URL)
        return

    # تخزين معرف الصورة لاستخدامه لاحقاً في التحسين
    user_last_photo[user_id] = update.message.photo[-1].file_id

    logger.info(f"📸 تم استلام صورة من المستخدم {user_id}")
    processing_msg = await update.message.reply_text("🔍 جاري تحليل الصورة بعمق...")

    photo_file = await update.message.photo[-1].get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        photo_path = tmp_file.name
        await photo_file.download_to_drive(photo_path)

    try:
        analysis = analyze_image(photo_path)
        await processing_msg.edit_text(analysis, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"❌ فشل تحليل الصورة: {e}", exc_info=True)
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء تحليل الصورة.")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)


async def handle_text(update: Update, context: CallbackContext):
    """معالجة الرسائل النصية"""
    user_message = update.message.text.strip()
    user_id = update.effective_user.id

    # التحقق من الاشتراك الإجباري أولاً
    if not await check_user_subscription(update, context, FORCE_SUBSCRIBE_CHANNEL_ID):
        await send_subscription_prompt(update, context, FORCE_SUBSCRIBE_CHANNEL_URL)
        return

    # التحقق مما إذا كان المستخدم يطلب تحسين صورة
    enhance_keywords = ["حسن الصورة", "حسن هذه الصورة", "حسن الصوره", "تحسين الصورة", "تحسين جودة الصورة", "حسن جودة الصورة", "improve image", "enhance image"]
    if any(keyword in user_message.lower() for keyword in enhance_keywords):
        await handle_enhance_request(update, context)
        return

    logger.info(f"💬 رسالة نصية من {user_id}: {user_message[:50]}...")
    processing_msg = await update.message.reply_text("💬 جاري التفكير...")

    try:
        response = chat_with_ai(user_message)
        file_created = await handle_potential_file_creation(update, response)
        if not file_created:
            await processing_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
        else:
            await processing_msg.delete()
    except Exception as e:
        logger.error(f"❌ فشل الرد: {e}", exc_info=True)
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء معالجة طلبك.")


async def handle_enhance_request(update: Update, context: CallbackContext):
    """معالجة طلب تحسين الصورة من خلال المحادثة النصية."""
    user_id = update.effective_user.id
    reply_to_message = update.message.reply_to_message

    # الحصول على الصورة المراد تحسينها
    photo_to_enhance = None

    if reply_to_message and reply_to_message.photo:
        # المستخدم رد على صورة
        photo_to_enhance = reply_to_message.photo[-1].file_id
    elif user_id in user_last_photo:
        # استخدام آخر صورة أرسلها المستخدم
        photo_to_enhance = user_last_photo[user_id]
    else:
        await update.message.reply_text(
            "🪄 **لتحسين صورة:**\n"
            "• أرسل الصورة أولاً.\n"
            "• ثم اكتب 'حسن الصورة' (أو رد على الصورة التي تريد تحسينها بهذه العبارة).",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    processing_msg = await update.message.reply_text("🪄 جاري تحسين الصورة بجودة أسطورية... قد يستغرق بضع ثوانٍ.")

    try:
        photo_file = await context.bot.get_file(photo_to_enhance)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            photo_path = tmp_file.name
            await photo_file.download_to_drive(photo_path)

        enhanced_image = enhance_image_quality_legendary(photo_path)

        await update.message.reply_document(
            document=enhanced_image,
            filename="Titan_AI_Enhanced.jpg",
            caption="✨ **تم تحسين الصورة بجودة أسطورية!**\n(تم تكبير الصورة 2x مع تحسينات فائقة)",
            parse_mode=ParseMode.MARKDOWN
        )
        await processing_msg.delete()
        logger.info(f"✅ تم تحسين الصورة للمستخدم {user_id}")
    except Exception as e:
        logger.error(f"❌ فشل تحسين الصورة: {e}", exc_info=True)
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء تحسين الصورة.")
    finally:
        if 'photo_path' in locals() and os.path.exists(photo_path):
            os.remove(photo_path)


async def handle_potential_file_creation(update: Update, response: str) -> bool:
    """تحليل الرد لاكتشاف ما إذا كان يحتوي على أمر لإنشاء ملف."""
    code_block_pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    if not matches:
        return False
    for i, (lang, code) in enumerate(matches):
        if not code.strip():
            continue
        file_extension = f".{lang}" if lang else ".txt"
        filename = f"Titan_AI_generated_{i}{file_extension}"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=file_extension, encoding='utf-8') as tmp_file:
            tmp_file.write(code.strip())
            tmp_file_path = tmp_file.name
        try:
            with open(tmp_file_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"📄 ملف من {BOT_NAME}",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"فشل إرسال الملف: {e}")
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    text_response = re.sub(code_block_pattern, '', response, flags=re.DOTALL).strip()
    if text_response:
        await update.message.reply_text(text_response, parse_mode=ParseMode.MARKDOWN)
    return True


async def button_callback(update: Update, context: CallbackContext):
    """معالجة ضغطات الأزرار."""
    query = update.callback_query
    if query.data == "check_subscription":
        await subscription_button_callback(update, context, FORCE_SUBSCRIBE_CHANNEL_ID)


def main():
    """تشغيل البوت"""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ لم يتم العثور على TELEGRAM_BOT_TOKEN")
    if not GROQ_API_KEY:
        logger.warning("⚠️ GROQ_API_KEY غير موجود.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CallbackQueryHandler(button_callback, pattern="check_subscription"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info(f"🤖 {BOT_NAME} قيد التشغيل...")
    application.run_polling()


if __name__ == "__main__":
    from config import GROQ_API_KEY
    main()
