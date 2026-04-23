import logging
import groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME, BOT_NAME, BOT_DEVELOPER
from image_processor import preprocess_image_for_analysis

logger = logging.getLogger(__name__)

try:
    client = groq.Groq(api_key=GROQ_API_KEY)
except Exception as e:
    logger.error(f"❌ فشل إنشاء عميل Groq: {e}")
    client = None

def classify_image_content(image_path: str) -> str:
    """
    تصنيف محتوى الصورة تلقائياً (مثل: طبيعة، حيوانات، أشخاص، إلخ).
    """
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    image_base64 = preprocess_image_for_analysis(image_path)
    prompt = (
        "صنف محتوى هذه الصورة إلى واحدة أو أكثر من الفئات التالية: "
        "طبيعة، حيوانات، أشخاص، طعام، عمارة، فن، تكنولوجيا، رياضة، أخرى. "
        "قدم الإجابة بصيغة قائمة مختصرة بالعربية."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.5,
            max_tokens=256
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تصنيف الصورة: {e}")
        raise RuntimeError(f"فشل تصنيف الصورة: {e}")

def generate_image_description_detailed(image_path: str) -> str:
    """
    توليد وصف تفصيلي وشامل للصورة.
    """
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    image_base64 = preprocess_image_for_analysis(image_path)
    prompt = (
        "قدم وصفاً تفصيلياً وشاملاً لهذه الصورة باللغة العربية. "
        "تضمن في الوصف: الأشياء الرئيسية، الألوان، الإضاءة، المزاج العام، "
        "وأي تفاصيل فنية أو جمالية مهمة. اجعل الوصف غنياً وغامراً."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.7,
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل توليد الوصف المفصل: {e}")
        raise RuntimeError(f"فشل توليد الوصف المفصل: {e}")

def detect_image_quality(image_path: str) -> str:
    """
    تقييم جودة الصورة وتقديم نصائح للتحسين.
    """
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    image_base64 = preprocess_image_for_analysis(image_path)
    prompt = (
        "قيّم جودة هذه الصورة من حيث: الوضوح، التركيب، الإضاءة، والألوان. "
        "قدم تقييماً بنسبة من 1-10 وقدم 2-3 نصائح محددة لتحسين الصورة. "
        "أجب باللغة العربية بصيغة مختصرة."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.5,
            max_tokens=512
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل تقييم جودة الصورة: {e}")
        raise RuntimeError(f"فشل تقييم جودة الصورة: {e}")

def extract_text_from_image(image_path: str) -> str:
    """
    استخراج النصوص من الصورة (OCR).
    """
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ.")
    
    image_base64 = preprocess_image_for_analysis(image_path)
    prompt = (
        "استخرج جميع النصوص المرئية في هذه الصورة. "
        "إذا كانت الصورة تحتوي على نصوص، أعد كتابتها بدقة. "
        "إذا لم تكن هناك نصوص، اكتب 'لا توجد نصوص في الصورة'."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            temperature=0.3,
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ فشل استخراج النصوص: {e}")
        raise RuntimeError(f"فشل استخراج النصوص: {e}")
