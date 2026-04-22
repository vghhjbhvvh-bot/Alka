import os
import logging
import tempfile
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, PicklePersistence
from telegram.constants import ParseMode
from config import (
    TELEGRAM_BOT_TOKEN, BOT_NAME, BOT_DEVELOPER,
    FORCE_SUBSCRIBE_CHANNEL_ID, FORCE_SUBSCRIBE_CHANNEL_URL
)
from groq_service import analyze_image, chat_with_ai, analyze_document, analyze_code
from image_processor import enhance_image_quality_legendary
from subscription import check_user_subscription, send_subscription_prompt, subscription_button_callback
from persistence import ChatHistoryManager
from file_handler import extract_text_from_file
from image_generator import generate_image, get_available_models_text

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

persistence = PicklePersistence(filepath="bot_persistence.pkl")
chat_manager = ChatHistoryManager(max_messages=20)
user_last_photo = {}

# --- دوال مساعدة للاشتراك (بدون تغيير) ---
async def require_subscription(update: Update, context: CallbackContext) -> bool:
    if await check_user_subscription(update, context, FORCE_SUBSCRIBE_CHANNEL_ID):
        return True
    await send_subscription_prompt(update, context, FORCE_SUBSCRIBE_CHANNEL_URL)
    return False

# --- أوامر البداية والمسح ---
async def start(update: Update, context: CallbackContext):
    if not await require_subscription(update, context):
        return
    await update.message.reply_text(
        f"👋 **مرحباً بك في {BOT_NAME}!**\n"
        f"تم تطويري بواسطة **{BOT_DEVELOPER}**.\n\n"
        "🎭 **أرسل صورة** لتحليلها.\n"
        "📄 **أرسل ملفاً** (TXT, PDF, DOCX, كود) لتحليله.\n"
        "💬 **تحدث معي** وأنا أتذكر سياق المحادثة.\n"
        "🪄 **اطلب تحسين صورة** بقولك 'حسن الصورة'.\n"
        "🎨 **ارسم صورة** باستخدام الأمر:\n"
        "`/draw وصف الصورة بالعربية أو الإنجليزية`\n\n"
        "استمتع! 🚀",
        parse_mode=ParseMode.MARKDOWN
    )

async def about(update: Update, context: CallbackContext):
    if not await require_subscription(update, context):
        return
    await update.message.reply_text(
        f"🤖 **{BOT_NAME}**\nمطور البوت: **{BOT_DEVELOPER}**\n\n"
        "إمكانياتي:\n"
        "• تحليل الصور والملفات\n"
        "• محادثة ذكية مع ذاكرة للسياق\n"
        "• تحليل الأكواد البرمجية\n"
        "• تحسين جودة الصور\n"
        "• رسم الصور باستخدام الذكاء الاصطناعي 🎨\n\n"
        "استمتع! 💪",
        parse_mode=ParseMode.MARKDOWN
    )

async def clear_history(update: Update, context: CallbackContext):
    if not await require_subscription(update, context):
        return
    user_id = update.effective_user.id
    chat_manager.clear_history(user_id)
    await update.message.reply_text("🧹 تم مسح تاريخ المحادثة.")

# --- أمر الرسم (draw فقط) ---
async def draw_command(update: Update, context: CallbackContext):
    """معالج الأمر /draw"""
    if not await require_subscription(update, context):
        return
    
    # استخراج وصف الصورة من الأمر
    if not context.args:
        await update.message.reply_text(
            "🎨 **استخدام أمر الرسم:**\n"
            "`/draw وصف الصورة التي تريد رسمها`\n\n"
            "**مثال:**\n"
            "`/draw قطة ترتدي قبعة ساحر في غابة سحرية`\n"
            "`/draw a cute cat wearing a wizard hat`\n\n"
            f"{get_available_models_text()}",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    prompt = " ".join(context.args)
    user_id = update.effective_user.id
    logger.info(f"🎨 طلب رسم من المستخدم {user_id}: {prompt[:100]}...")
    
    # إرسال رسالة انتظار
    processing_msg = await update.message.reply_text(
        "🎨 جاري رسم الصورة... قد يستغرق الأمر 10-30 ثانية.\n"
        "*(نستخدم نموذج Flux للحصول على أفضل جودة)* ⏳"
    )
    
    try:
        # توليد الصورة
        image_data = await generate_image(prompt, model="flux")
        
        if image_data is None:
            await processing_msg.edit_text(
                "❌ عذراً، فشل توليد الصورة. قد يكون الخادم مشغولاً.\n"
                "حاول مرة أخرى بعد قليل."
            )
            return
        
        # إرسال الصورة
        await update.message.reply_photo(
            photo=image_data,
            caption=f"🎨 **تم رسم الصورة!**\n📝 الوصف: `{prompt[:200]}`",
            parse_mode=ParseMode.MARKDOWN
        )
        await processing_msg.delete()
        
        # حفظ في تاريخ المحادثة
        chat_manager.add_message(user_id, "user", f"/draw {prompt}")
        chat_manager.add_message(user_id, "assistant", "[تم رسم الصورة المطلوبة]")
        
    except Exception as e:
        logger.error(f"❌ فشل رسم الصورة: {e}", exc_info=True)
        await processing_msg.edit_text("❌ حدث خطأ غير متوقع أثناء رسم الصورة.")

# --- باقي المعالجات كما هي بدون تغيير ---
async def handle_photo(update: Update, context: CallbackContext):
    if not await require_subscription(update, context):
        return
    user_id = update.effective_user.id
    user_last_photo[user_id] = update.message.photo[-1].file_id
    processing_msg = await update.message.reply_text("🔍 جاري تحليل الصورة...")
    photo_file = await update.message.photo[-1].get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        photo_path = tmp.name
        await photo_file.download_to_drive(photo_path)
    try:
        analysis = analyze_image(photo_path)
        await processing_msg.edit_text(analysis, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"❌ فشل تحليل الصورة: {e}", exc_info=True)
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء تحليل الصورة.")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)

async def handle_enhance_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    reply_to_message = update.message.reply_to_message
    photo_to_enhance = None
    if reply_to_message and reply_to_message.photo:
        photo_to_enhance = reply_to_message.photo[-1].file_id
    elif user_id in user_last_photo:
        photo_to_enhance = user_last_photo[user_id]
    else:
        await update.message.reply_text("🪄 أرسل صورة أولاً ثم اطلب تحسينها.")
        return
    processing_msg = await update.message.reply_text("🪄 جاري تحسين الصورة بجودة أسطورية باستخدام DeepAI...")
    try:
        photo_file = await context.bot.get_file(photo_to_enhance)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            photo_path = tmp.name
            await photo_file.download_to_drive(photo_path)
        enhanced_image = enhance_image_quality_legendary(photo_path)
        await update.message.reply_document(
            document=enhanced_image,
            filename="Titan_AI_Enhanced.jpg",
            caption="✨ **تم تحسين الصورة بجودة أسطورية!**",
            parse_mode=ParseMode.MARKDOWN
        )
        await processing_msg.delete()
    except Exception as e:
        logger.error(f"❌ فشل تحسين الصورة: {e}", exc_info=True)
        await processing_msg.edit_text("❌ حدث خطأ أثناء تحسين الصورة.")
    finally:
        if 'photo_path' in locals() and os.path.exists(photo_path): os.remove(photo_path)

async def handle_document(update: Update, context: CallbackContext):
    if not await require_subscription(update, context): return
    user_id = update.effective_user.id
    document = update.message.document
    file_name = document.file_name or "unknown"
    processing_msg = await update.message.reply_text(f"📄 جاري قراءة الملف `{file_name}`...", parse_mode=ParseMode.MARKDOWN)

    try:
        file = await document.get_file()
        text, is_code = await extract_text_from_file(file)
        if text is None:
            await processing_msg.edit_text("❌ لم نتمكن من قراءة الملف. تأكد من صيغة مدعومة.")
            return
        if len(text) > 6000: text = text[:6000] + "... (تم اقتطاع النص)"
        
        if is_code:
            await processing_msg.edit_text(f"💻 جاري تحليل الكود البرمجي (`{file_name}`)...", parse_mode=ParseMode.MARKDOWN)
            analysis = analyze_code(text, file_name)
            chat_manager.add_message(user_id, "user", f"[ملف كود: {file_name}]\n{text[:500]}")
        else:
            analysis = analyze_document(text)
            chat_manager.add_message(user_id, "user", f"[ملف: {file_name}]\n{text[:500]}")
            
        chat_manager.add_message(user_id, "assistant", analysis)
        await processing_msg.edit_text(f"📑 **تحليل الملف:**\n\n{analysis}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"❌ فشل معالجة الملف: {e}", exc_info=True)
        await processing_msg.edit_text("❌ حدث خطأ أثناء معالجة الملف.")

async def handle_text(update: Update, context: CallbackContext):
    if not await require_subscription(update, context): return
    user_id = update.effective_user.id
    user_message = update.message.text.strip()
    enhance_keywords = ["حسن الصورة", "حسن هذه الصورة", "تحسين الصورة", "تحسين جودة الصورة"]
    if any(kw in user_message.lower() for kw in enhance_keywords):
        await handle_enhance_request(update, context); return
    processing_msg = await update.message.reply_text("💬 جاري التفكير...")
    try:
        history = chat_manager.get_history(user_id)
        response = chat_with_ai(user_id, user_message, history)
        chat_manager.add_message(user_id, "user", user_message)
        chat_manager.add_message(user_id, "assistant", response)
        file_created = await handle_potential_file_creation(update, response)
        if not file_created:
            await processing_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
        else:
            await processing_msg.delete()
    except Exception as e:
        logger.error(f"❌ فشل الرد: {e}", exc_info=True)
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء معالجة طلبك.")

async def handle_potential_file_creation(update: Update, response: str) -> bool:
    code_block_pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    if not matches: return False
    for i, (lang, code) in enumerate(matches):
        if not code.strip(): continue
        file_extension = f".{lang}" if lang else ".txt"
        filename = f"Titan_AI_generated_{i}{file_extension}"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=file_extension, encoding='utf-8') as tmp:
            tmp.write(code.strip()); tmp_path = tmp.name
        try:
            with open(tmp_path, 'rb') as f:
                await update.message.reply_document(document=f, filename=filename, caption=f"📄 ملف من {BOT_NAME}")
        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)
    text_response = re.sub(code_block_pattern, '', response, flags=re.DOTALL).strip()
    if text_response: await update.message.reply_text(text_response, parse_mode=ParseMode.MARKDOWN)
    return True

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "check_subscription":
        await subscription_button_callback(update, context, FORCE_SUBSCRIBE_CHANNEL_ID, FORCE_SUBSCRIBE_CHANNEL_URL)

def main():
    if not TELEGRAM_BOT_TOKEN: raise ValueError("❌ TELEGRAM_BOT_TOKEN غير موجود")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).persistence(persistence).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(CommandHandler("draw", draw_command))
    # تم إزالة السطر الذي كان يسبب الخطأ: application.add_handler(CommandHandler("تخيل", draw_command))
    application.add_handler(CallbackQueryHandler(button_callback, pattern="check_subscription"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info(f"🤖 {BOT_NAME} قيد التشغيل...")
    application.run_polling()

if __name__ == "__main__":
    main()
