import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden, TelegramError

logger = logging.getLogger(__name__)

async def check_user_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: str) -> bool:
    """
    تتحقق مما إذا كان المستخدم مشتركًا في القناة المحددة.
    تعيد True إذا كان المستخدم مشتركًا (عضو، مشرف، مالك)، و False بخلاف ذلك.
    """
    user_id = update.effective_user.id
    bot = context.bot

    try:
        chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        # الحالات التي تعتبر مشتركًا: "creator" (مالك)، "administrator" (مشرف)، "member" (عضو)
        if chat_member.status in ['creator', 'administrator', 'member']:
            logger.info(f"✅ المستخدم {user_id} مشترك في القناة {channel_id}")
            return True
        else:
            logger.info(f"❌ المستخدم {user_id} غير مشترك في القناة {channel_id} (الحالة: {chat_member.status})")
            return False

    except BadRequest as e:
        if "user not found" in str(e).lower() or "chat not found" in str(e).lower():
            logger.warning(f"⚠️ المستخدم {user_id} غير موجود في القناة {channel_id}: {e}")
            return False
        else:
            logger.error(f"❌ خطأ BadRequest غير متوقع أثناء التحقق من اشتراك المستخدم {user_id}: {e}")
            return False
    except Forbidden as e:
        logger.error(f"🚫 البوت ليس لديه صلاحية للوصول إلى القناة {channel_id}. تأكد من أن البوت مشرف في القناة: {e}")
        return False
    except TelegramError as e:
        logger.error(f"❌ خطأ في Telegram API أثناء التحقق من الاشتراك: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع أثناء التحقق من الاشتراك: {e}", exc_info=True)
        return False


async def send_subscription_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_url: str):
    """
    ترسل رسالة تطلب من المستخدم الاشتراك في القناة.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ اشترك في القناة", url=channel_url)],
        [InlineKeyboardButton("🔄 تحققت من الاشتراك", callback_data="check_subscription")]
    ])

    await update.message.reply_text(
        "⚠️ **تنبيه هام!**\n\n"
        "للأسف، لا يمكنك استخدام هذا البوت إلا بعد الاشتراك في قناتنا الرسمية.\n\n"
        "👆 **يرجى اتباع الخطوات التالية:**\n"
        "1️⃣ اضغط على زر **'اشترك في القناة'**.\n"
        "2️⃣ انضم إلى القناة.\n"
        "3️⃣ عد إلى هنا واضغط على **'تحققت من الاشتراك'**.\n\n"
        "شكرًا لدعمك! 💙",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )


async def subscription_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: str):
    """
    تعالج الضغط على زر التحقق من الاشتراك.
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    bot = context.bot

    # التحقق من الاشتراك مرة أخرى
    if await check_user_subscription(update, context, channel_id):
        await query.edit_message_text(
            "✅ **شكرًا لاشتراكك!**\n\n"
            "تم التحقق من اشتراكك بنجاح. يمكنك الآن استخدام جميع ميزات البوت بحرية.\n\n"
            "🎉 استمتع بتجربة Titan AI!",
            parse_mode=ParseMode.MARKDOWN
        )
        return True
    else:
        # إعادة عرض رسالة الاشتراك
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ اشترك في القناة", url=FORCE_SUBSCRIBE_CHANNEL_URL)],
            [InlineKeyboardButton("🔄 تحققت من الاشتراك", callback_data="check_subscription")]
        ])

        await query.edit_message_text(
            "⚠️ **لم يتم التحقق من اشتراكك بعد!**\n\n"
            "يبدو أنك لم تشترك في القناة بعد، أو أن الاشتراك لم يكتمل.\n\n"
            "👆 **يرجى المحاولة مرة أخرى:**\n"
            "1️⃣ اضغط على زر **'اشترك في القناة'**.\n"
            "2️⃣ انضم إلى القناة.\n"
            "3️⃣ عد إلى هنا واضغط على **'تحققت من الاشتراك'**.\n\n"
            "شكرًا لتعاونك! 💙",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        return False
