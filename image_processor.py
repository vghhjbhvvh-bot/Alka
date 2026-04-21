import io
import logging
import base64
import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from config import DEEPAI_API_KEY

logger = logging.getLogger(__name__)

# --- دوال تحسين الصور ---

def preprocess_image_for_analysis(image_path: str) -> str:
    """تحسين الصورة للتحليل فقط (بدون تغيير)."""
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
    تحسين أسطوري لجودة الصورة باستخدام DeepAI API.
    إذا فشل الاتصال بـ DeepAI، يتم الرجوع إلى تحسين Pillow.
    """
    try:
        logger.info("🚀 محاولة تحسين الصورة باستخدام DeepAI API...")
        
        with open(image_path, 'rb') as f:
            response = requests.post(
                "https://api.deepai.org/api/torch-srgan",
                files={'image': f},
                headers={'api-key': DEEPAI_API_KEY},
                timeout=60
            )
        
        if response.status_code == 200:
            data = response.json()
            output_url = data.get('output_url')
            if output_url:
                # تحميل الصورة المحسنة من الرابط
                img_response = requests.get(output_url, timeout=30)
                img_response.raise_for_status()
                enhanced_io = io.BytesIO(img_response.content)
                enhanced_io.seek(0)
                logger.info("✨ تم تحسين الصورة بنجاح باستخدام DeepAI (SRGAN).")
                return enhanced_io
            else:
                raise Exception("لم يتم العثور على 'output_url' في استجابة DeepAI")
        else:
            raise Exception(f"DeepAI API returned status {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.warning(f"⚠️ فشل تحسين الصورة باستخدام DeepAI: {e}. سيتم الرجوع إلى Pillow.")
        
        # الرجوع إلى تحسين Pillow
        try:
            with Image.open(image_path) as img:
                new_size = (img.width * 2, img.height * 2)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img = ImageOps.autocontrast(img, cutoff=0.5)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.8)
                img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=200, threshold=0))
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.5)
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.4)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.2)
                img = img.filter(ImageFilter.MedianFilter(size=3))
                img = img.filter(ImageFilter.SMOOTH_MORE)
                img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=1))
                enhanced_io = io.BytesIO()
                img.save(enhanced_io, format="JPEG", quality=100, optimize=True, progressive=True)
                enhanced_io.seek(0)
                logger.info("✨ تم تحسين الصورة باستخدام Pillow (2x).")
                return enhanced_io
        except Exception as e2:
            logger.error(f"❌ فشل تحسين الصورة باستخدام Pillow أيضاً: {e2}")
            raise RuntimeError(f"فشل تحسين الصورة: {e2}")
