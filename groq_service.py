import base64
import logging
import groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME

logger = logging.getLogger(__name__)

try:
    client = groq.Groq(api_key=GROQ_API_KEY)
    logger.info("✅ تم إنشاء عميل Groq بنجاح.")
except Exception as e:
    logger.error(f"❌ فشل إنشاء عميل Groq: {e}")
    client = None

def analyze_image(image_path: str) -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ. تحقق من مفتاح API.")

    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ ملف الصورة غير موجود: {image_path}")
    except Exception as e:
        raise RuntimeError(f"❌ فشل قراءة أو ترميز الصورة: {e}")

    # --- الأمر الذكي (تم تصحيح إغلاق النص) ---
    intelligent_prompt = (
        "أنت محلل صور ذكي ومثقف. مهمتك هي تحليل الصورة المرفوعة والإجابة باللغة العربية على النحو التالي:\n\n"
        "1. **🔍 التحليل الأولي**: صف بإيجاز ما تراه في الصورة (المشهد، الشخصيات، الأشياء الرئيسية).\n\n"
        "2. **🤔 تحديد الهوية**:\n"
        "   - هل تظهر في الصورة شخصية مشهورة (ممثل، رياضي، مغني، شخصية تاريخية، شخصية كرتونية)؟\n"
        "   - هل تظهر لعبة فيديو معروفة؟\n"
        "   - هل يظهر معلم سياحي أو موقع شهير؟\n"
        "   - هل الصورة مجرد مشهد عام لا يحتوي على أي مما سبق؟\n\n"
        "3. **📚 البحث عن المعلومات (فكر بعمق)**:\n"
        "   - إذا حددت هوية معينة (شخصية، لعبة، معلم)، قدم فقرة تعريفية قصيرة ومنظمة عنها. اذكر اسمها، ولماذا هي مشهورة، وبعض التفاصيل الأساسية عنها.\n"
        "   - إذا لم تحدد هوية مشهورة، فقدم وصفاً دقيقاً وجذاباً للمشهد العام في الصورة.\n\n"
        "مثال على التنسيق المطلوب لإجابتك:\n\n"
        "🔍 **التحليل الأولي**:\n"
        "أرى في الصورة رجلاً يرتدي بدلة رسمية سوداء وربطة عنق، يقف أمام حشد من الناس ويلوح بيده. في الخلفية، يظهر مبنى أبيض كبير ذو قبة.\n\n"
        "🤔 **تحديد الهوية**:\n"
        "نعم، الشخص الذي في الصورة هو الرئيس الأمريكي الأسبق باراك أوباما.\n\n"
        "📚 **معلومات عن باراك أوباما**:\n"
        "باراك حسين أوباما هو الرئيس الرابع والأربعون للولايات المتحدة الأمريكية، وقد تولى منصبه من عام 2009 إلى عام 2017. يُعتبر أول رئيس أمريكي من أصول أفريقية، وقد حصل على جائزة نوبل للسلام عام 2009. اشتهر بخطاباته الملهمة وبرنامجه للرعاية الصحية \"أوباما كير\".\n\n"
        "ابدأ الآن تحليلك."
    )
    # --- نهاية الأمر الذكي ---

    try:
        logger.info(f"🧠 بدء التحليل العميق للصورة {image_path} باستخدام النموذج {GROQ_MODEL_NAME}")
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": intelligent_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_string}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except groq.AuthenticationError:
        logger.error("❌ خطأ في المصادقة: مفتاح Groq API غير صالح.")
        raise RuntimeError("مفتاح Groq API غير صالح. تأكد من المتغير GROQ_API_KEY.")
    except groq.BadRequestError as e:
        logger.error(f"❌ طلب غير صالح: {e}")
        if "model" in str(e).lower():
            raise RuntimeError(f"النموذج '{GROQ_MODEL_NAME}' غير موجود أو لا يدعم الرؤية.")
        raise RuntimeError(f"خطأ في الطلب: {e}")
    except groq.RateLimitError:
        logger.warning("⏳ تم تجاوز حد الاستخدام المجاني.")
        raise RuntimeError("حد الاستخدام المجاني لـ Groq API تجاوز الحد. انتظر قليلاً.")
    except groq.APIConnectionError:
        logger.error("🌐 فشل الاتصال بخادم Groq API.")
        raise RuntimeError("تعذر الاتصال بـ Groq API. حاول لاحقاً.")
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {type(e).__name__} - {e}")
        raise RuntimeError(f"حدث خطأ أثناء تحليل الصورة: {e}")
