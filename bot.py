import logging
import os
import re
import tempfile
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, CallbackContext, CallbackQueryHandler, ContextTypes, PicklePersistence
)
from config import (
    TELEGRAM_BOT_TOKEN, BOT_NAME, BOT_DEVELOPER, 
    FORCE_SUBSCRIBE_CHANNEL_ID, FORCE_SUBSCRIBE_CHANNEL_URL
)
from groq_service import (
    chat_with_ai, analyze_image, analyze_code, 
    analyze_document, enhance_image_prompt
)
from image_generator import generate_image
from file_handler import extract_text_from_file
from persistence import ChatHistoryManager
from rate_limiter import RateLimiter
from subscription import check_user_subscription, send_subscription_prompt, subscription_button_callback

# إعداد السجلات
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# تهيئة Persistence و ChatHistoryManager
bot_persistence = PicklePersistence(filepath="bot_data.pickle")
chat_manager = ChatHistoryManager()

# محدد معدل الطلبات
rate_limiter = RateLimiter(max_requests=15, time_window=60)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 أهلاً بك {user.first_name} في {BOT_NAME}!\n\n"
        f"أنا مساعدك الذكي المطور بواسطة {BOT_DEVELOPER}. "
        "أتميز بقدرات متطورة في البرمجة، تحليل الملفات، توليد الصور، والبحث في الإنترنت.\n\n"
        "🚀 **ماذا يمكنني أن أفعل؟**\n"
        "• 💻 برمجة وتحليل أكواد معقدة.\n"
        "• 📄 تحليل وتلخيص ملفات PDF و Word.\n"
        "• 🎨 رسم صور مذهلة (اكتب 'ارسم' متبوعاً بوصف).\n"
        "• 🖼️ تحليل الصور وشرح محتواها.\n"
        "• 🌐 البحث في الإنترنت (اكتب 'ابحث' متبوعاً بسؤالك).\n\n"
        "أرسل أي ملف أو كود أو سؤال لتبدأ!",
        parse_mode=ParseMode.MARKDOWN
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 **حول {BOT_NAME}**\n\n"
        f"تم تطوير هذا البوت ليكون المساعد الذكي الشامل على تيليجرام.\n"
        f"المطور: {BOT_DEVELOPER}\n"
        "التقنيات: Groq (Llama 3), Hugging Face (FLUX.1), DuckDuckGo Search\n"
        "الإصدار: 2.1.0 (تحديث البحث والإصلاحات)",
        parse_mode=ParseMode.MARKDOWN
    )

async def features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    features_text = (
        "🌟 **مميزات {BOT_NAME} المطورة:**\n\n"
        "1️⃣ **خبير برمجيات**: حل مشاكل البرمجة وكتابة أكواد نظيفة.\n"
        "2️⃣ **محلل مستندات**: دعم كامل لملفات PDF و Word وجميع ملفات الأكواد.\n"
        "3️⃣ **فنان رقمي**: توليد صور عالية الدقة باستخدام نماذج FLUX.\n"
        "4️⃣ **رؤية حاسوبية**: تحليل الصور بدقة واستخراج النصوص منها.\n"
        "5️⃣ **بحث إنترنت**: الوصول لمعلومات حديثة عبر البحث المباشر.\n"
        "6️⃣ **سرعة فائقة**: استجابة لحظية بفضل تقنية Groq."
    ).format(BOT_NAME=BOT_NAME)
    await update.message.reply_text(features_text, parse_mode=ParseMode.MARKDOWN)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_manager.clear_history(user_id)
    await update.message.reply_text("✅ تم مسح سجل المحادثة بنجاح.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text("⚠️ مهلاً! لقد تجاوزت حد الطلبات. انتظر دقيقة ثم حاول مجدداً.")
        return

    if not await check_user_subscription(update, context, FORCE_SUBSCRIBE_CHANNEL_ID):
        await send_subscription_prompt(update, context, FORCE_SUBSCRIBE_CHANNEL_URL)
        return

    document = update.message.document
    file_name = document.file_name
    processing_msg = await update.message.reply_text(f"📥 جاري معالجة الملف: `{file_name}`...", parse_mode=ParseMode.MARKDOWN)

    try:
        file = await context.bot.get_file(document.file_id)
        ext = os.path.splitext(file_name)[1].lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            await file.download_to_drive(tmp.name)
            file_path = tmp.name

        content, is_code = await extract_text_from_file(file_path, file_name)
        os.unlink(file_path)

        if not content:
            await processing_msg.edit_text("❌ عذراً، لم أتمكن من قراءة محتوى هذا الملف.")
            return

        if is_code:
            await processing_msg.edit_text("🔍 جاري تحليل الكود البرمجي بعمق...")
            analysis = analyze_code(content, file_name)
        else:
            await processing_msg.edit_text("📄 جاري قراءة وتحليل المستند...")
            analysis = analyze_document(content)

        await processing_msg.edit_text(analysis, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"خطأ في معالجة المستند: {e}", exc_info=True)
        await processing_msg.edit_text("❌ حدث خطأ أثناء تحليل الملف.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text("⚠️ تجاوزت حد الطلبات.")
        return

    if not await check_user_subscription(update, context, FORCE_SUBSCRIBE_CHANNEL_ID):
        await send_subscription_prompt(update, context, FORCE_SUBSCRIBE_CHANNEL_URL)
        return

    photo = update.message.photo[-1]
    processing_msg = await update.message.reply_text("🖼️ جاري تحليل الصورة...")

    try:
        file = await context.bot.get_file(photo.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            await file.download_to_drive(tmp.name)
            photo_path = tmp.name

        analysis = analyze_image(photo_path)
        os.unlink(photo_path)
        await processing_msg.edit_text(analysis, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"خطأ في تحليل الصورة: {e}")
        await processing_msg.edit_text("❌ فشل تحليل الصورة.")

async def process_draw_request(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    processing_msg = await update.message.reply_text("🎨 جاري رسم لوحتك الفنية باستخدام FLUX...")
    try:
        enhanced_prompt = enhance_image_prompt(prompt)
        logger.info(f"المطالبة المحسنة: {enhanced_prompt}")
        
        image_data = await generate_image(enhanced_prompt)
        if image_data:
            image_data.seek(0)
            await update.message.reply_photo(
                photo=image_data, 
                caption=f"✅ تم الرسم بنجاح!\n\n**الوصف الأصلي:** {prompt}",
                parse_mode=ParseMode.MARKDOWN
            )
            await processing_msg.delete()
        else:
            await processing_msg.edit_text("❌ عذراً، فشلت محاولة الرسم. حاول مرة أخرى بوصف مختلف.")
    except Exception as e:
        logger.error(f"خطأ في الرسم: {e}")
        await processing_msg.edit_text("❌ حدث خطأ تقني أثناء الرسم.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id

    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text("⚠️ تجاوزت حد الطلبات.")
        return

    if not await check_user_subscription(update, context, FORCE_SUBSCRIBE_CHANNEL_ID):
        await send_subscription_prompt(update, context, FORCE_SUBSCRIBE_CHANNEL_URL)
        return

    # التحقق من طلب الرسم
    draw_keywords = ["ارسم", "رسم", "صمم", "تخيل", "draw"]
    if any(user_message.lower().startswith(kw) for kw in draw_keywords):
        prompt = user_message
        for kw in draw_keywords:
            if prompt.lower().startswith(kw):
                prompt = prompt[len(kw):].strip()
                break
        if prompt:
            await process_draw_request(update, context, prompt)
            return
        else:
            await update.message.reply_text("🎨 ماذا تريد أن أرسم؟ اكتب وصفاً بعد كلمة 'ارسم'.")
            return

    # التحقق من طلب البحث
    search_keywords = ["ابحث", "search", "جوجل", "google"]
    use_search = False
    query = user_message
    if any(user_message.lower().startswith(kw) for kw in search_keywords):
        use_search = True
        for kw in search_keywords:
            if query.lower().startswith(kw):
                query = query[len(kw):].strip()
                break
    
    if use_search and not query:
        await update.message.reply_text("🌐 ماذا تريد أن أبحث عنه؟ اكتب سؤالك بعد كلمة 'ابحث'.")
        return

    # محادثة عادية أو بحث
    status_text = "🌐 جاري البحث والتفكير..." if use_search else "💬 جاري التفكير..."
    processing_msg = await update.message.reply_text(status_text)
    
    try:
        history = chat_manager.get_history(user_id)
        response = chat_with_ai(user_id, query, history, use_search=use_search)
        
        chat_manager.add_message(user_id, "user", user_message)
        chat_manager.add_message(user_id, "assistant", response)
        
        if "```" in response:
            code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", response, re.DOTALL)
            if code_blocks and len(code_blocks[0]) > 1000:
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as tmp:
                    tmp.write(code_blocks[0])
                    tmp_path = tmp.name
                with open(tmp_path, "rb") as f:
                    await update.message.reply_document(document=f, filename="code_solution.py", caption="📄 إليك الكود البرمجي في ملف لسهولة الاستخدام.")
                os.unlink(tmp_path)

        await processing_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"خطأ في الرد: {e}")
        await processing_msg.edit_text("❌ عذراً، حدث خطأ أثناء معالجة طلبك.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN غير موجود")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).persistence(bot_persistence).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("features", features))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(CallbackQueryHandler(subscription_button_callback, pattern="check_subscription"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info(f"🚀 {BOT_NAME} v2.1 قيد التشغيل...")
    application.run_polling()

if __name__ == "__main__":
    main()
