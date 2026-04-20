import base64
import logging
import io
import groq
from PIL import Image, ImageEnhance, ImageFilter
from config import GROQ_API_KEY, GROQ_MODEL_NAME

logger = logging.getLogger(__name__)

try:
    client = groq.Groq(api_key=GROQ_API_KEY)
    logger.info("✅ تم إنشاء عميل Groq بنجاح.")
except Exception as e:
    logger.error(f"❌ فشل إنشاء عميل Groq: {e}")
    client = None

def preprocess_image(image_path: str) -> str:
    """
    تحسين جودة الصورة لمساعدة النموذج في الرؤية الليلية:
    - زيادة الحدة (Sharpness)
    - زيادة التباين (Contrast)
    - تقليل الضوضاء (Smoothness)
    يتم حفظ الصورة المحسنة في الذاكرة وإعادتها كسلسلة Base64.
    """
    try:
        with Image.open(image_path) as img:
            # 1. تحسين الحدة (لإظهار تفاصيل الوجه أو الشعارات)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)

            # 2. تحسين التباين (لإبراز الظلال والإضاءة)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.3)

            # 3. تحسين الألوان (اختياري ولكن مفيد)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)

            # تحويل الصورة إلى Base64
            buffered = io.BytesIO()
            # الحفاظ على التنسيق الأصلي أو التحويل إلى JPEG
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(buffered, format="JPEG", quality=95)
            encoded_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            logger.info("🪄 تم تحسين جودة الصورة تلقائياً لتحسين دقة التحليل.")
            return encoded_string
    except Exception as e:
        logger.warning(f"⚠️ تعذر تحسين الصورة، سيتم إرسالها كما هي: {e}")
        # إذا فشل التحسين، نقرأ الصورة الأصلية بصيغة Base64
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path: str) -> str:
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ. تحقق من مفتاح API.")

    # تحسين الصورة أولاً
    encoded_string = preprocess_image(image_path)

    # --- الأمر الذكي للمحقق (The Detective Prompt) ---
    detective_prompt = (
        "أنت الآن محقق صور محترف ومثقف موسوعي. مهمتك الأساسية هي تحليل الصورة المرفوعة وكشف هوية محتواها مهما كانت الصورة غير واضحة، قديمة، ملتقطة من زاوية جانبية، أو تحتوي على تشويش.\n"
        "اتبع خطوات التحقيق التالية بدقة، وفكر بصوت عالٍ داخل عقلك قبل الإجابة:\n\n"
        "**الخطوة 1: التحليل الجنائي للصورة (Forensic Analysis)**\n"
        "لا تكتفِ بالنظر للعنصر الرئيسي. حلل كل بكسل في الصورة:\n"
        "- افحص الخلفية: هل يوجد معالم مميزة، شعارات، نصوص، أعلام؟\n"
        "- افحص الملابس والإكسسوارات: هل يرتدي الشخص زياً رسمياً، قميص نادٍ رياضي، قبعة معينة، ساعة يد مميزة؟\n"
        "- افحص ملامح الوجه الدقيقة (حتى لو كانت غير واضحة): شكل الأنف، العينين، تصفيفة الشعر، لون البشرة، الوشوم.\n\n"
        "**الخطوة 2: توليد الفرضيات (Hypothesis Generation)**\n"
        "بناءً على الأدلة التي جمعتها، ضع قائمة بـ 3 إلى 5 شخصيات أو ألعاب أو معالم محتملة قد تكون الظاهرة في الصورة. استخدم معرفتك الموسوعية الواسعة.\n"
        "مثال: إذا رأيت رجلاً أصلع يرتدي بذلة رمادية ويقف أمام مبنى الكابيتول، ضع فرضية: 'جيف بيزوس' أو 'سياسي أمريكي'.\n\n"
        "**الخطوة 3: الاستدلال العكسي (Reverse Reasoning)**\n"
        "لكل فرضية، حاول إثبات صحتها أو نفيها بناءً على تفاصيل الصورة. ابحث عن 'التفاصيل القاتلة' (The Smoking Gun) التي تؤكد هوية الشخص.\n"
        "مثال: 'إنه جيف بيزوس لأن شكل رأسه الأصلع وابتسامته المميزة تتطابق مع الصورة، ولا يوجد سبب لوجود مارك زوكربيرج في هذا الموقع.'\n\n"
        "**الخطوة 4: الوصول إلى الحكم النهائي (Final Verdict)**\n"
        "اختر الشخصية/الهوية الأكثر ترجيحاً بناءً على تحليلك. حتى لو لم تكن متأكداً 100%، قدم أفضل تخمين مدعوم بالأدلة.\n\n"
        "**التنسيق النهائي للإجابة (باللغة العربية):**\n\n"
        "🔍 **نتائج التحقيق في الصورة:**\n"
        "- **الأدلة الجنائية**: [اكتب ملاحظاتك الدقيقة عن تفاصيل الصورة].\n"
        "- **تحليل الأدلة**: [اشرح كيف قادتك هذه التفاصيل إلى فرضية معينة].\n\n"
        "🤔 **الحكم النهائي على الهوية:**\n"
        "- **الاسم**: [اسم الشخصية أو اللعبة أو المعلم].\n"
        "- **نبذة تعريفية**: [قدم فقرة قصيرة ومنظمة تشرح من هو/ما هي، ولماذا هو/هي مشهور/ة].\n\n"
        "ابدأ الآن تحليلك كمحقق. فكر بعمق."
    )
    # --- نهاية الأمر الذكي ---

    try:
        logger.info(f"🕵️ بدء التحقيق العميق في الصورة {image_path} باستخدام النموذج {GROQ_MODEL_NAME}")
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": detective_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_string}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.6, # توازن بين الإبداع والدقة
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
