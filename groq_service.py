import os
import logging
import base64
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME, BOT_NAME, BOT_DEVELOPER
from search_service import search_web, format_search_prompt

logger = logging.getLogger(__name__)

client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        logger.info("✅ تم تهيئة عميل Groq بنجاح.")
    except Exception as e:
        logger.error(f"❌ فشل تهيئة عميل Groq: {e}")
else:
    logger.warning("⚠️ مفتاح GROQ_API_KEY غير موجود. لن تعمل وظائف Groq.")

# قائمة بنماذج الرؤية المتاحة والموثوقة (مع الأفضلية)
VISION_MODELS = [
    "llama-3.2-90b-vision-preview",  # نموذج قوي
    "llava-v1.5-7b-4096-preview",    # بديل خفيف
]

async def analyze_image(image_base64: str) -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    prompt = (
        "أنت خبير في تحليل الصور. قم بوصف الصورة بدقة وتفصيل، مع التركيز على العناصر الرئيسية، "
        "الألوان، الحالة العامة، وأي نص ظاهر. قدم تحليلاً شاملاً وواضحاً باللغة العربية. "
        "إذا كانت الصورة تحتوي على واجهة مستخدم، قم بوصف الواجهة وشرحها."
    )
    
    for model_name in VISION_MODELS:
        try:
            logger.info(f"🔍 جاري تحليل الصورة باستخدام نموذج Groq: {model_name}")
            chat_completion = client.chat.completions.create(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }],
                temperature=0.5,
                max_tokens=2048
            )
            logger.info(f"✅ تم تحليل الصورة بنجاح باستخدام {model_name}")
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.warning(f"❌ فشل تحليل الصورة باستخدام {model_name}: {e}")
            # إذا فشل النموذج الحالي، جرب النموذج التالي في القائمة
            continue
    
    # إذا فشلت جميع النماذج
    logger.error("❌ فشلت جميع محاولات تحليل الصورة باستخدام نماذج Groq المتاحة.")
    raise RuntimeError("فشل تحليل الصورة: لم يتمكن أي نموذج رؤية من Groq من معالجة الطلب.")

def chat_with_ai(user_id: int, user_message: str, history: list, use_search: bool = False) -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    system_prompt = (
        f"أنت {BOT_NAME}، مساعد ذكي فائق القدرات تم تطويره بواسطة {BOT_DEVELOPER}. "
        "أنت خبير برمجيات بمستوى \'Senior Architect\'، تتقن جميع لغات البرمجة والتقنيات الحديثة. "
        "قواعدك:\n"
        "1. كن دقيقاً جداً في الأكواد البرمجية واشرحها بوضوح.\n"
        "2. استخدم أفضل الممارسات (Clean Code, Design Patterns).\n"
        "3. حلل المشاكل بعمق وقدم حلولاً جذرية.\n"
        "4. أجب باللغة العربية بأسلوب مهني وودي.\n"
        "5. إذا طُلب منك البرمجة، قدم كوداً كاملاً وجاهزاً للتشغيل مع شرح لكيفية الاستخدام."
    )
    
    current_message = user_message
    if use_search:
        search_results = search_web(user_message)
        current_message = format_search_prompt(user_message, search_results)
        logger.info("🌐 تم دمج نتائج البحث في الطلب.")
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-20:]:
        if msg.get("role") in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": current_message})
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            temperature=0.6,
            max_tokens=4096
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ أثناء المحادثة: {e}")
        raise RuntimeError(f"حدث خطأ أثناء المحادثة: {e}")

def analyze_code(code: str, file_name: str = "", user_question: str = "") -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    prompt = get_code_analysis_prompt(code, file_name, user_question)
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل الكود: {e}")
        raise RuntimeError(f"فشل تحليل الكود: {e}")

def analyze_document(document_text: str, user_question: str = None) -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    if user_question:
        prompt = f"أنت خبير في تحليل المستندات. بناءً على النص التالي، أجب عن السؤال بدقة.\n\nالمستند:\n{document_text[:15000]}\n\nالسؤال: {user_question}"
    else:
        prompt = f"أنت خبير في تلخيص المستندات. قم بتقديم ملخص شامل ومنظم للنص التالي باللغة العربية، مع ذكر أهم النقاط.\n\nالمستند:\n{document_text[:15000]}"
        
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=3072
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تحليل المستند: {e}")
        raise RuntimeError(f"فشل تحليل المستند: {e}")

def enhance_image_prompt(user_prompt: str) -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
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
            model=GROQ_MODEL_NAME,
            messages=messages,
            temperature=0.8,
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ فشل تحسين المطالبة: {e}")
        return user_prompt

# Helper function for code analysis prompt (assuming it exists elsewhere or is meant to be added)
def get_code_analysis_prompt(code: str, file_name: str, user_question: str) -> str:
    # This function was not provided in the original groq_service.py, 
    # but is called by analyze_code. Adding a placeholder for now.
    if user_question:
        return f"أنت خبير في تحليل الكود. بناءً على الكود التالي من الملف {file_name}، أجب عن السؤال بدقة.\n\nالكود:\n```python\n{code}\n```\n\nالسؤال: {user_question}"
    else:
        return f"أنت خبير في تحليل الكود. قم بتقديم تحليل شامل ومنظم للكود التالي من الملف {file_name}، مع ذكر أهم النقاط، المشاكل المحتملة، واقتراحات التحسين.\n\nالكود:\n```python\n{code}\n```"
