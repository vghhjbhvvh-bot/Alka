import logging
import groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME, BOT_NAME, BOT_DEVELOPER
from image_processor import preprocess_image_for_analysis
from code_analyzer import get_code_analysis_prompt

logger = logging.getLogger(__name__)

try:
    client = groq.Groq(api_key=GROQ_API_KEY)
    logger.info("✅ تم إنشاء عميل Groq بنجاح.")
except Exception as e:
    logger.error(f"❌ فشل إنشاء عميل Groq: {e}")
    client = None

# --- تحليل الصور (بدون تغيير) ---
def analyze_image(image_path: str) -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    image_base64 = preprocess_image_for_analysis(image_path)
    prompt = ("أنت المحقق البصري الأسطوري. حلل هذه الصورة بالتفصيل باللغة العربية، "
              "وحدد ما إذا كانت تحتوي على شخصية مشهورة، لعبة، أو معلم. قدم وصفاً دقيقاً.")
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}], temperature=0.7, max_tokens=1024)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل الصورة: {e}")
        raise RuntimeError(f"فشل تحليل الصورة: {e}")

# --- محادثة عامة (بدون تغيير) ---
def chat_with_ai(user_id: int, user_message: str, history: list) -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    system_prompt = (f"أنت {BOT_NAME}، مساعد ذكي ومتعدد الاستخدامات تم تطويره بواسطة {BOT_DEVELOPER}. "
                     "أجب باللغة العربية ما لم يُطلب غير ذلك.")
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-20:]:
        if msg.get("role") in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=messages, temperature=0.7, max_tokens=2048)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ أثناء المحادثة: {e}")
        raise RuntimeError(f"حدث خطأ أثناء المحادثة: {e}")

# --- تحليل الأكواد (جديد) ---
def analyze_code(code: str, file_name: str = "", user_question: str = "") -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    
    # الحصول على المطالبة المتخصصة
    prompt = get_code_analysis_prompt(code, file_name, user_question)
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=[{"role": "user", "content": prompt}],
            temperature=0.5, max_tokens=2048)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل الكود: {e}")
        raise RuntimeError(f"فشل تحليل الكود: {e}")

# --- تحليل المستندات النصية العامة (بدون تغيير) ---
def enhance_image_prompt(user_prompt: str) -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    system_prompt = (
        "أنت خبير في هندسة المطالبات (Prompt Engineering) لتوليد الصور بالذكاء الاصطناعي. "
        "مهمتك هي تحويل المطالبات البسيطة أو القصيرة التي يقدمها المستخدم إلى مطالبات مفصلة وغنية "
        "بالتفاصيل، مع التركيز على الجودة الفنية والجمالية. أضف تفاصيل حول الأسلوب الفني، الإضاءة، "
        "التكوين، الألوان، والمزاج العام للصورة. اجعل المطالبة باللغة الإنجليزية لضمان أفضل النتائج "
        "مع نماذج توليد الصور. لا تضف أي شرح إضافي، فقط المطالبة المحسنة."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"المطالبة الأصلية: {user_prompt}\n\nالمطالبة المحسنة:"}
    ]
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=messages, temperature=0.9, max_tokens=500
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ فشل تحسين المطالبة: {e}")
        return user_prompt # العودة إلى المطالبة الأصلية في حالة الفشل

def analyze_document(document_text: str, user_question: str = None) -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    if user_question:
        prompt = f"المستند التالي:\n\n{document_text[:3000]}\n\nالسؤال: {user_question}\n\nأجب بناءً على المستند فقط."
    else:
        prompt = f"المستند التالي:\n\n{document_text[:3000]}\n\nقدم ملخصاً موجزاً باللغة العربية."
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=[{"role": "user", "content": prompt}],
            temperature=0.5, max_tokens=1024)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل المستند: {e}")
        raise RuntimeError(f"فشل تحليل المستند: {e}")
