import io
import logging
import base64
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

def preprocess_image_for_analysis(image_path: str) -> str:
    """تحسين الصورة للتحليل فقط (بدون تغيير)."""
    try:
        with Image.open(image_path) as img:
            # تحسينات بسيطة لضمان وضوح الصورة للتحليل بواسطة نموذج الرؤية
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.8)
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=95)
            encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
            logger.info("🪄 تم تحسين الصورة للتحليل.")
            return encoded_string
    except Exception as e:
        logger.warning(f"⚠️ تعذر تحسين الصورة للتحليل، سيتم إرسالها كما هي: {e}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
