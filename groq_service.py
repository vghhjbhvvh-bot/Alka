import base64
import logging
import groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME

logger = logging.getLogger(__name__)

# إنشاء عميل Groq
try:
    client = groq.Groq(api_key=GROQ_API_KEY)
    logger.info("✅ تم إنشاء عميل Groq بنجاح.")
except Exception as e:
    logger.error(f"❌ فشل إنشاء عميل Groq: {e}")
    client = None

def analyze_image(image_path: str) -> str:
    """
    يحلل الصورة بعمق: يحدد إذا كانت شخصية مشهورة، لعبة، معلم، إلخ.
    ويجلب معلومات مفصلة عنها.
    """
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ. تحقق من مفتاح API.")

    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ ملف الصورة غير موجود: {image_path}")
    except Exception as e:
        raise RuntimeError(f"❌ فشل قراءة أو ترميز الصورة: {e}")

    # --- 🧠 الأمر الذكي (The Smart Prompt) ---
    intelligent_prompt = """أنت محلل صور ذكي ومثقف. مهمتك هي تحليل الصورة المرفوعة والإجابة باللغة العربية على النحو التالي:

1.  **🔍 التحليل الأولي**: صف بإيجاز ما تراه في الصورة (المشهد، الشخصيات، الأشياء الرئيسية).

2.  **🤔 تحديد الهوية**:
    *   هل تظهر في الصورة شخصية مشهورة (ممثل، رياضي، مغني، شخصية تاريخية، شخصية كرتونية)؟
    *   هل تظهر لعبة فيديو معروفة؟
    *   هل يظهر معلم سياحي أو موقع شهير؟
    *   هل الصورة مجرد مشهد عام لا يحتوي على أي مما سبق؟

3.  **📚 البحث عن المعلومات (فكر بعمق)**:
    *   **إذا حددت هوية معينة (شخصية، لعبة، معلم)**، قدم فقرة تعريفية قصيرة ومنظمة عنها. اذكر اسمها، ولماذا هي مشهورة، وبعض التفاصيل الأساسية عنها.
    *   **إذا لم تحدد هوية مشهورة**، فقدم وصفاً دقيقاً وجذاباً للمشهد العام في الصورة.

**مثال على التنسيق المطلوب لإجابتك:**
    
