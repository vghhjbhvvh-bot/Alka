import io
import logging
import base64
from PIL import Image

logger = logging.getLogger(__name__)

def preprocess_image_for_analysis(image_path: str) -> str:
    """
    تحضير الصورة للتحليل عن طريق تغيير حجمها (إذا كانت كبيرة جداً) وتحويلها إلى Base64.
    """
    try:
        with Image.open(image_path) as img:
            # تحويل إلى RGB إذا كانت بصيغة مختلفة (مثل RGBA)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # تصغير حجم الصورة إذا كانت كبيرة جداً لتوفير الباندويث وتجنب قيود API
            max_size = (1024, 1024)
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.info(f"📏 تم تصغير حجم الصورة إلى {img.size}")

            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
            logger.info("✅ تم تحضير الصورة للتحليل بنجاح.")
            return encoded_string
    except Exception as e:
        logger.warning(f"⚠️ حدث خطأ أثناء معالجة الصورة، سيتم إرسالها كما هي: {e}")
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e2:
            logger.error(f"❌ فشل قراءة الصورة تماماً: {e2}")
            raise e2
