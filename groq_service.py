import logging
import groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME
from image_processor import preprocess_image_for_analysis

logger = logging.getLogger(__name__)

try:
    client = groq.Groq(api_key=GROQ_API_KEY)
    logger.info("✅ تم إنشاء عميل Groq بنجاح.")
except Exception as e:
    logger.error(f"❌ فشل إنشاء عميل Groq: {e}")
    client = None

def analyze_with_model(image_base64: str, model_name: str) -> str:
    # --- المطالبة الأسطورية (The Legendary Prompt) ---
    legendary_prompt = (
        "أنت الآن المحقق البصري الأسطوري 'عين الحقيقة'، الذي لا يخطئ أبدًا في التعرف على أي شخصية أو لعبة أو معلم أو كائن يظهر في الصور، حتى لو كانت الصورة مشوشة، ملتقطة من زاوية جانبية، قديمة، كرتونية، مرسومة باليد، أو على شكل تمثال.\n\n"
        "**مهمتك المقدسة:**\n"
        "تحليل الصورة المرفوعة وكشف هوية محتواها مهما كانت الظروف. **لا يُسمح لك أبدًا بقول 'لا أعرف' أو 'غير قادر على التحديد' أو 'غير معروف'.** في أسوأ الأحوال، يجب أن تقدم **أفضل تخمين مدروس** مبني على أدلة بصرية ومعرفتك الموسوعية.\n\n"
        "**التنسيق الإلزامي للإجابة (باللغة العربية الفصحى الجذابة):**\n\n"
        "🔍 **نتائج التحقيق البصري الأسطوري:**\n"
        "• **الأدلة الجنائية**: [اكتب هنا ملاحظاتك الدقيقة عن الصورة].\n"
        "• **تحليل الأدلة**: [اشرح كيف قادتك هذه التفاصيل إلى استنتاجك].\n\n"
        "🤔 **الحكم النهائي على الهوية:**\n"
        "• **الاسم**: [اكتب اسم الشخصية/اللعبة/المعلم].\n"
        "• **نبذة تعريفية أسطورية**: [قدم فقرة قصيرة ومنظمة تشرح من هو/ما هي، ولماذا هو/هي مشهور/ة. استخدم أسلوباً حماسياً وجذاباً].\n\n"
        "ابدأ الآن تحليلك الأسطوري."
    )

    try:
        logger.info(f"🚀 إرسال التحليل إلى النموذج: {model_name}")
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": legendary_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            temperature=0.8,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ أثناء استخدام النموذج {model_name}: {e}")
        raise e

def analyze_image(image_path: str) -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ. تحقق من مفتاح API.")

    image_base64 = preprocess_image_for_analysis(image_path)
    primary_model = GROQ_MODEL_NAME
    fallback_model = "llava-v1.5-7b"

    try:
        result = analyze_with_model(image_base64, primary_model)
        refusal_keywords = ["لا أعرف", "غير قادر", "غير معروف", "لا يمكنني", "لا استطيع", "غير متأكد تماما", "لا يوجد معلومات"]
        if any(keyword in result for keyword in refusal_keywords):
            logger.warning("النموذج الأساسي أظهر تردداً، جاري المحاولة مع النموذج الاحتياطي...")
            result_fallback = analyze_with_model(image_base64, fallback_model)
            result = f"🔮 **تحليل إضافي (نموذج رؤية متخصص):**\n{result_fallback}\n\n---\n📝 *(التحليل الأولي أعلاه)*"
        return result
    except Exception as e:
        logger.error(f"فشل النموذج الأساسي: {e}. تجربة النموذج الاحتياطي...")
        try:
            return analyze_with_model(image_base64, fallback_model)
        except Exception as e2:
            raise RuntimeError(f"فشل كلا النموذجين: {e2}")

def chat_with_ai(user_message: str) -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ. تحقق من مفتاح API.")
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي ومتعدد الاستخدامات. يمكنك الإجابة على الأسئلة العامة، وتقديم المساعدة في البرمجة، وكتابة الأكواد البرمجية، وحتى إنشاء محتوى لملفات نصية. عند تقديم كود برمجي أو محتوى لملف، ضعه داخل علامات Markdown مناسبة (مثل ```python ... ```) ليسهل على المستخدم نسخه."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ أثناء المحادثة: {e}")
        raise RuntimeError(f"حدث خطأ أثناء المحادثة: {e}")
