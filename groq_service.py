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

def analyze_image(image_path: str) -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    image_base64 = preprocess_image_for_analysis(image_path)
    prompt = ("أنت المحقق البصري الأسطوري وخبير تحليل الصور. حلل هذه الصورة بدقة متناهية باللغة العربية. "
              "حدد العناصر، الأشخاص، النصوص، الأجواء، والألوان. إذا كانت الصورة تحتوي على كود برمج، فقم باستخراجه وشرحه.")
    try:
        chat_completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview", # استخدام نموذج رؤية قوي
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}], temperature=0.5, max_tokens=2048)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل الصورة: {e}")
        raise RuntimeError(f"فشل تحليل الصورة: {e}")

def chat_with_ai(user_id: int, user_message: str, history: list) -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    
    # مطالبة نظام متطورة تجعل البوت ذكياً جداً في البرمجة
    system_prompt = (
        f"أنت {BOT_NAME}، مساعد ذكي فائق القدرات تم تطويره بواسطة {BOT_DEVELOPER}. "
        "أنت خبير برمجيات بمستوى 'Senior Architect'، تتقن جميع لغات البرمجة والتقنيات الحديثة. "
        "قواعدك:\n"
        "1. كن دقيقاً جداً في الأكواد البرمجية واشرحها بوضوح.\n"
        "2. استخدم أفضل الممارسات (Clean Code, Design Patterns).\n"
        "3. حلل المشاكل بعمق وقدم حلولاً جذرية.\n"
        "4. أجب باللغة العربية بأسلوب مهني وودي.\n"
        "5. إذا طُلب منك البرمجة، قدم كوداً كاملاً وجاهزاً للتشغيل مع شرح لكيفية الاستخدام."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-20:]:
        if msg.get("role") in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=messages, temperature=0.6, max_tokens=4096)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ أثناء المحادثة: {e}")
        raise RuntimeError(f"حدث خطأ أثناء المحادثة: {e}")

def analyze_code(code: str, file_name: str = "", user_question: str = "") -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    prompt = get_code_analysis_prompt(code, file_name, user_question)
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=4096)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل الكود: {e}")
        raise RuntimeError(f"فشل تحليل الكود: {e}")

def analyze_document(document_text: str, user_question: str = None) -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    
    if user_question:
        prompt = f"أنت خبير في تحليل المستندات. بناءً على النص التالي، أجب عن السؤال بدقة.\n\nالمستند:\n{document_text[:15000]}\n\nالسؤال: {user_question}"
    else:
        prompt = f"أنت خبير في تلخيص المستندات. قم بتقديم ملخص شامل ومنظم للنص التالي باللغة العربية، مع ذكر أهم النقاط.\n\nالمستند:\n{document_text[:15000]}"
        
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=[{"role": "user", "content": prompt}],
            temperature=0.4, max_tokens=3072)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل المستند: {e}")
        raise RuntimeError(f"فشل تحليل المستند: {e}")

def enhance_image_prompt(user_prompt: str) -> str:
    if client is None: raise RuntimeError("عميل Groq غير مهيأ.")
    system_prompt = (
        "أنت خبير عالمي في هندسة مطالبات الصور (Stable Diffusion & FLUX). "
        "حول وصف المستخدم البسيط إلى مطالبة احترافية بالإنجليزية تتضمن:\n"
        "- تفاصيل دقيقة (Detailed textures, lighting, composition).\n"
        "- الأسلوب الفني (Cinematic, photorealistic, 8k, highly detailed).\n"
        "- استبعد الكلمات السلبية.\n"
        "أخرج المطالبة فقط بدون أي نص إضافي."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"المطالبة الأصلية: {user_prompt}"}
    ]
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME, messages=messages, temperature=0.8, max_tokens=1024)
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ فشل تحسين المطالبة: {e}")
        return user_prompt
