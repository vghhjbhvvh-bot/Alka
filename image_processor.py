import io
import logging
import base64
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

def preprocess_image_for_analysis(image_path: str) -> str:
    """تحسين الصورة للتحليل فقط."""
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
        logger.warning(f"⚠️ تعذر تحسين الصورة للتحليل: {e}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

def enhance_image_quality_legendary(image_path: str) -> io.BytesIO:
    """
    تحسين أسطوري لجودة الصورة:
    - تكبير 2x
    - تحسينات متقدمة
    """
    try:
        with Image.open(image_path) as img:
            # تكبير 2x
            new_size = (img.width * 2, img.height * 2)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # تحسين تلقائي للتباين
            img = ImageOps.autocontrast(img, cutoff=0.5)
            
            # تحسين الحدة
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.8)
            img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=200, threshold=0))
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
            
            # تحسين التباين واللون
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.4)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)
            
            # تقليل الضوضاء
            img = img.filter(ImageFilter.MedianFilter(size=3))
            img = img.filter(ImageFilter.SMOOTH_MORE)
            img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=1))
            
            enhanced_io = io.BytesIO()
            img.save(enhanced_io, format="JPEG", quality=100, optimize=True, progressive=True)
            enhanced_io.seek(0)
            
            logger.info("✨ تم تحسين الصورة بشكل أسطوري.")
            return enhanced_io
    except Exception as e:
        logger.error(f"❌ فشل تحسين الصورة: {e}")
        raise RuntimeError(f"فشل تحسين الصورة: {e}")
