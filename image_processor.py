import io
import logging
import base64
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

# محاولة استيراد Real-ESRGAN (اختياري)
try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    import numpy as np
    REALESRGAN_AVAILABLE = True
    # تحميل النموذج مرة واحدة فقط عند الطلب (lazy loading)
    _realesrgan_model = None
except ImportError:
    REALESRGAN_AVAILABLE = False
    logger.warning("Real-ESRGAN غير متوفر. سيتم استخدام Pillow فقط لتحسين الصور.")


def get_realesrgan_model():
    """تحميل نموذج Real-ESRGAN (إذا كان متاحاً) مع التخزين المؤقت."""
    global _realesrgan_model
    if not REALESRGAN_AVAILABLE:
        return None
    if _realesrgan_model is None:
        try:
            # نموذج RealESRGAN_x4plus (يمكن تغييره)
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            upsampler = RealESRGANer(
                scale=4,
                model_path=None,  # سيتم تنزيل النموذج تلقائياً
                model=model,
                tile=400,
                tile_pad=10,
                pre_pad=0,
                half=False  # استخدم CPU فقط لتجنب مشاكل GPU
            )
            _realesrgan_model = upsampler
            logger.info("✅ تم تحميل نموذج Real-ESRGAN بنجاح.")
        except Exception as e:
            logger.error(f"❌ فشل تحميل نموذج Real-ESRGAN: {e}")
            _realesrgan_model = False  # تعيين False للإشارة إلى فشل التحميل
            return None
    return _realesrgan_model if _realesrgan_model is not False else None


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
    تحسين أسطوري لجودة الصورة. يحاول استخدام Real-ESRGAN إذا كان متاحاً،
    وإلا يستخدم Pillow مع تكبير 2x.
    """
    try:
        # محاولة استخدام Real-ESRGAN أولاً
        if REALESRGAN_AVAILABLE:
            model = get_realesrgan_model()
            if model:
                logger.info("🚀 استخدام Real-ESRGAN لتحسين الصورة...")
                # قراءة الصورة كـ numpy array
                img = Image.open(image_path).convert('RGB')
                img_np = np.array(img)
                # تطبيق التحسين
                output, _ = model.enhance(img_np, outscale=4)  # تكبير 4x
                # تحويل النتيجة إلى صورة
                result_img = Image.fromarray(output)
                enhanced_io = io.BytesIO()
                result_img.save(enhanced_io, format="JPEG", quality=95)
                enhanced_io.seek(0)
                logger.info("✨ تم تحسين الصورة باستخدام Real-ESRGAN.")
                return enhanced_io

        # Fallback إلى Pillow (تكبير 2x)
        logger.info("🔄 استخدام Pillow لتحسين الصورة (تكبير 2x).")
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
    except Exception as e:
        logger.error(f"❌ فشل تحسين الصورة: {e}")
        raise RuntimeError(f"فشل تحسين الصورة: {e}")
