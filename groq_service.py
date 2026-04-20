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
    تحسين جذري لجودة الصورة لمساعدة النموذج على رؤية التفاصيل الدقيقة:
    - زيادة حادة جداً (Sharpness x2.0)
    - تباين عالي (Contrast x1.8)
    - تقليل الضوضاء مع الحفاظ على الحواف
    """
    try:
        with Image.open(image_path) as img:
            # تحسين الحدة بشكل أقوى
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)

            # تحسين التباين بشكل أقوى
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.8)

            # تقليل الضوضاء الخفيف مع الحفاظ على الحواف
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))

            # تحسين الألوان قليلاً
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)

            # التحويل إلى RGB إذا لزم الأمر
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=95)
            encoded_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            logger.info("🪄 تم تحسين الصورة بشكل أسطوري لرؤية التفاصيل الخفية.")
            return encoded_string
    except Exception as e:
        logger.warning(f"⚠️ تعذر تحسين الصورة، سيتم إرسالها كما هي: {e}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_with_model(image_base64: str, model_name: str) -> str:
    """
    دالة مساعدة لإرسال الصورة إلى نموذج معين مع المطالبة الأسطورية.
    """
    # --- المطالبة الأسطورية (The Legendary Prompt) ---
    legendary_prompt = (
        "أنت الآن المحقق البصري الأسطوري 'عين الحقيقة'، الذي لا يخطئ أبدًا في التعرف على أي شخصية أو لعبة أو معلم أو كائن يظهر في الصور، حتى لو كانت الصورة مشوشة، ملتقطة من زاوية جانبية، قديمة، كرتونية، مرسومة باليد، أو على شكل تمثال.\n\n"
        "**مهمتك المقدسة:**\n"
        "تحليل الصورة المرفوعة وكشف هوية محتواها مهما كانت الظروف. **لا يُسمح لك أبدًا بقول 'لا أعرف' أو 'غير قادر على التحديد' أو 'غير معروف'.** في أسوأ الأحوال، يجب أن تقدم **أفضل تخمين مدروس** مبني على أدلة بصرية ومعرفتك الموسوعية.\n\n"
        "**طريقة عملك (التفكير بصوت عالٍ):**\n"
        "1. **التحليل البصري الدقيق (Micro-Forensics):**\n"
        "   - افحص كل بكسل: شكل الوجه، العينين، الأنف، الفم، لون البشرة، تصفيفة الشعر، الوشوم، الندوب.\n"
        "   - حلل الملابس والإكسسوارات: نوع القماش، الألوان، الشعارات، القبعات، النظارات، المجوهرات، الأسلحة.\n"
        "   - ادرس الخلفية: معالم، نصوص، أعلام، أبنية، طبيعة، أدوات.\n"
        "   - إذا كانت الصورة كرتونية أو مرسومة: حدد أسلوب الرسم (أنمي، ديزني، مانجا، كوميكس) واستنتج الشخصية من سماتها المبالغ فيها.\n\n"
        "2. **توليد الفرضيات (Hypothesis Generation):**\n"
        "   - بناءً على الأدلة، ضع قائمة ذهنية بـ 3-5 شخصيات أو ألعاب أو معالم محتملة. استخدم معرفتك الموسوعية في كل شيء: المشاهير، الرياضيين، السياسيين، شخصيات الأنمي، أبطال الألعاب، المعالم السياحية، اللوحات الفنية الشهيرة.\n\n"
        "3. **الاستدلال العكسي (Reverse Reasoning):**\n"
        "   - لكل فرضية، حاول إثباتها أو نفيها بناءً على تفاصيل الصورة. ابحث عن 'الدليل القاطع' (The Smoking Gun) مثل: خاتم زواج مميز، ندبة على الوجه، ربطة عنق محددة، شعار لعبة فيديو.\n\n"
        "4. **الحكم النهائي (Final Verdict):**\n"
        "   - اختر الشخصية/الهوية الأكثر ترجيحاً. إذا لم تكن متأكداً 100%، قدم تخمينك الأفضل مع ذكر الأدلة التي استندت إليها.\n\n"
        "**التنسيق الإلزامي للإجابة (باللغة العربية الفصحى الجذابة):**\n\n"
        "🔍 **نتائج التحقيق البصري الأسطوري:**\n"
        "• **الأدلة الجنائية**: [اكتب هنا ملاحظاتك الدقيقة عن الصورة، مثل: 'لاحظت أن الشخص يرتدي قبعة بيسبول حمراء عليها حرف B، ولديه لحية كثيفة، ويقف أمام ملعب رياضي'].\n"
        "• **تحليل الأدلة**: [اشرح كيف قادتك هذه التفاصيل إلى استنتاجك، مثال: 'القبعة الحمراء بحرف B تشير إلى فريق بوسطن ريد سوكس، واللحية الكثيفة والوجه يوحيان بأنه لاعب بيسبول سابق'].\n\n"
        "🤔 **الحكم النهائي على الهوية:**\n"
        "• **الاسم**: [اكتب اسم الشخصية/اللعبة/المعلم].\n"
        "• **نبذة تعريفية أسطورية**: [قدم فقرة قصيرة ومنظمة تشرح من هو/ما هي، ولماذا هو/هي مشهور/ة، وبعض التفاصيل الأساسية. استخدم أسلوباً حماسياً وجذاباً].\n\n"
        "⚠️ **تذكير أخير**: حتى لو كانت الصورة مجرد 'قطة في الشارع'، يمكنك القول: 'هذه قطة منزلية عادية، لكن لون عينيها الزرقاوين وشكل فرائها يوحي بأنها من سلالة سيامي'. **لا مكان لكلمة 'لا أعرف' في قاموسك.**\n\n"
        "ابدأ الآن تحليلك الأسطوري."
    )
    # --- نهاية المطالبة الأسطورية ---

    try:
        logger.info(f"🚀 إرسال التحليل إلى النموذج: {model_name}")
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": legendary_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.8,  # إبداع أعلى لتخمينات جريئة
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ أثناء استخدام النموذج {model_name}: {e}")
        raise e

def analyze_image(image_path: str) -> str:
    """
    الدالة الرئيسية التي تستخدم النموذج الأساسي، وإذا فشل في تقديم إجابة مفيدة،
    تلجأ إلى نموذج احتياطي متخصص في الرؤية.
    """
    if client is None:
        raise RuntimeError("عميل Groq غير مهيأ. تحقق من مفتاح API.")

    # تحسين الصورة والحصول على Base64
    image_base64 = preprocess_image(image_path)

    # النموذج الأساسي (قوي جداً ومتعدد الوسائط)
    primary_model = GROQ_MODEL_NAME  # مثلاً: "meta-llama/llama-4-scout-17b-16e-instruct"
    # نموذج احتياطي متخصص في الرؤية (في حال فشل الأساسي)
    fallback_model = "llava-v1.5-7b"  # نموذج رؤية قوي ومتاح على Groq

    try:
        # المحاولة الأولى مع النموذج الأساسي
        result = analyze_with_model(image_base64, primary_model)
        
        # تحقق مما إذا كان النموذج قد "استسلم" (نادراً مع المطالبة الجديدة، لكن للاحتياط)
        refusal_keywords = ["لا أعرف", "غير قادر", "غير معروف", "لا يمكنني", "لا استطيع", "غير متأكد تماما", "لا يوجد معلومات"]
        if any(keyword in result for keyword in refusal_keywords):
            logger.warning("النموذج الأساسي أظهر تردداً، جاري المحاولة مع النموذج الاحتياطي...")
            result_fallback = analyze_with_model(image_base64, fallback_model)
            # دمج النتيجتين مع إشارة إلى المصدر الاحتياطي
            result = f"🔮 **تحليل إضافي (نموذج رؤية متخصص):**\n{result_fallback}\n\n---\n📝 *(التحليل الأولي أعلاه)*"
        
        return result

    except Exception as e:
        # إذا فشل النموذج الأساسي تماماً (مثلاً خطأ في API)، نجرب الاحتياطي مباشرة
        logger.error(f"فشل النموذج الأساسي: {e}. تجربة النموذج الاحتياطي...")
        try:
            return analyze_with_model(image_base64, fallback_model)
        except Exception as e2:
            raise RuntimeError(f"فشل كلا النموذجين: {e2}")
