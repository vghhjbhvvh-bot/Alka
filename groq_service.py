import logging
import groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME, BOT_NAME, BOT_DEVELOPER
from image_processor import preprocess_image_for_analysis

logger = logging.getLogger(__name__)

try:
    client = groq.Groq(api_key=GROQ_API_KEY)
    logger.info("✅ تم إنشاء عميل Groq بنجاح.")
except Exception as e:
    logger.error(f"❌ فشل إنشاء عميل Groq: {e}")
    client = None


def analyze_image(image_path: str) -> str:
    """تحليل الصورة باستخدام نموذج الرؤية."""
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    image_base64 = preprocess_image_for_analysis(image_path)
    prompt = (
        "أنت المحقق البصري الأسطوري. حلل هذه الصورة بالتفصيل باللغة العربية، "
        "وحدد ما إذا كانت تحتوي على شخصية مشهورة، لعبة، أو معلم. قدم وصفاً دقيقاً."
    )
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل الصورة: {e}")
        raise RuntimeError(f"فشل تحليل الصورة: {e}")


def chat_with_ai(user_id: int, user_message: str, history: list) -> str:
    """
    محادثة مع الذكاء الاصطناعي مع الأخذ بالاعتبار تاريخ المحادثة.
    """
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    system_prompt = (
        f"أنت {BOT_NAME}، مساعد ذكي ومتعدد الاستخدامات تم تطويره بواسطة {BOT_DEVELOPER}. "
        "أنت قادر على الإجابة على الأسئلة العامة، المساعدة في البرمجة، كتابة الأكواد، وإنشاء ملفات. "
        "عند تقديم كود برمجي، ضعه داخل علامات Markdown (```python ... ```). "
        "أجب باللغة العربية ما لم يُطلب غير ذلك."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    # إضافة تاريخ المحادثة (مع التأكد من أن الأدوار صحيحة)
    for msg in history[-20:]:  # آخر 20 رسالة لتجنب تجاوز الحد
        if msg.get("role") in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    # إضافة رسالة المستخدم الحالية
    messages.append({"role": "user", "content": user_message})
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ أثناء المحادثة: {e}")
        raise RuntimeError(f"حدث خطأ أثناء المحادثة: {e}")


def analyze_document(document_text: str, user_question: str = None) -> str:
    """تحليل مستند نصي والإجابة عن أسئلة حوله."""
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    # تحديد المطالبة بناءً على وجود سؤال
    if user_question:
        prompt = f"المستند التالي:\n\n{document_text[:3000]}\n\nالسؤال: {user_question}\n\nأجب بناءً على المستند فقط."
    else:
        prompt = f"المستند التالي:\n\n{document_text[:3000]}\n\nقدم ملخصاً موجزاً باللغة العربية."
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل المستند: {e}")
        raise RuntimeError(f"فشل تحليل المستند: {e}")
