import io
import logging
import base64
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

def preprocess_image_for_analysis(image_path: str) -> str:
    """
    تحسين جذري لجودة الصورة لمساعدة النموذج على رؤية التفاصيل الدقيقة.
    """
    try:
        with Image.open(image_path) as img:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)

            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.8)

            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))

            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)

            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=95)
            encoded_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            logger.info("🪄 تم تحسين الصورة للتحليل.")
            return encoded_string
    except Exception as e:
        logger.warning(f"⚠️ تعذر تحسين الصورة للتحليل، سيتم إرسالها كما هي: {e}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

def enhance_image_quality(image_path: str) -> io.BytesIO:
    """
    تحسين جودة الصورة وإعادتها كملف جاهز للإرسال.
    """
    try:
        with Image.open(image_path) as img:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)

            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.8)

            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))

            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)

            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            enhanced_image_io = io.BytesIO()
            img.save(enhanced_image_io, format="JPEG", quality=95)
            enhanced_image_io.seek(0)
            
            logger.info("✨ تم تحسين جودة الصورة بنجاح.")
            return enhanced_image_io
    except Exception as e:
        logger.error(f"❌ فشل تحسين جودة الصورة: {e}")
        raise RuntimeError(f"فشل تحسين جودة الصورة: {e}")
