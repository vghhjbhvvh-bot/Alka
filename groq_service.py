import base64
import logging
import groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME

logger = logging.getLogger(__name__)

# إنشاء عميل Groq
try:
    client = groq.Groq(api_key=GROQ_API_KEY)
except Exception as e:
    logger.error(f"فشل إنشاء عميل Groq: {e}")
    client = None

def analyze_image(image_path: str) -> str:
    """
    تحليل صورة من مسار ملف وإرجاع الوصف.
    في حالة حدوث خطأ، ترفع الاستثناء ليتم التقاطه في bot.py.
    """
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ. تحقق من مفتاح API.")

    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(f"ملف الصورة غير موجود: {image_path}")
    except Exception as e:
        raise RuntimeError(f"فشل قراءة أو ترميز الصورة: {e}")

    try:
        # إرسال الطلب إلى Groq API باستخدام نموذج الرؤية
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "ماذا يظهر في هذه الصورة؟ أجب باللغة العربية."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_string}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.5,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content

    except groq.AuthenticationError:
        logger.error("خطأ في المصادقة: مفتاح Groq API غير صالح.")
        raise RuntimeError("مفتاح Groq API غير صالح. تأكد من المتغير GROQ_API_KEY.")
    except groq.BadRequestError as e:
        logger.error(f"طلب غير صالح: {e}")
        # إذا كان الخطأ متعلقاً بالنموذج
        if "model" in str(e).lower():
            raise RuntimeError(f"النموذج '{GROQ_MODEL_NAME}' غير موجود أو لا يدعم الرؤية. تأكد من استخدام نموذج Vision.")
        raise RuntimeError(f"خطأ في الطلب: {e}")
    except groq.RateLimitError:
        logger.warning("تم تجاوز حد الاستخدام المجاني لـ Groq API.")
        raise RuntimeError("حد الاستخدام المجاني لـ Groq API تجاوز الحد. انتظر قليلاً أو قم بترقية خطتك.")
    except groq.APIConnectionError:
        logger.error("فشل الاتصال بخادم Groq API.")
        raise RuntimeError("تعذر الاتصال بـ Groq API. تحقق من اتصال الإنترنت أو حاول لاحقاً.")
    except Exception as e:
        logger.error(f"خطأ غير متوقع من Groq: {type(e).__name__} - {e}")
        raise RuntimeError(f"حدث خطأ أثناء تحليل الصورة: {e}")
