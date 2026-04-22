import io
import logging
import aiohttp
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# إعدادات Pollinations API
POLLINATIONS_API_URL = "https://image.pollinations.ai/prompt"

# قائمة بالنماذج المتاحة (يمكنك تغييرها)
AVAILABLE_MODELS = {
    "flux": "Flux (جودة عالية)",
    "turbo": "Turbo (سريع)",
    "realistic": "Realistic Vision (واقعي)",
    "anime": "Anime (أنمي)"
}

async def generate_image(prompt: str, model: str = "flux", width: int = 1024, height: int = 1024) -> Optional[io.BytesIO]:
    """
    توليد صورة باستخدام Pollinations AI API.
    
    Args:
        prompt: وصف الصورة المطلوبة
        model: النموذج المستخدم (flux, turbo, realistic, anime)
        width: عرض الصورة (الحد الأقصى: 1024)
        height: ارتفاع الصورة (الحد الأقصى: 1024)
    
    Returns:
        BytesIO object containing the generated image, or None if failed
    """
    try:
        # تنظيف وتحضير النص للـ URL
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        
        # بناء الرابط مع المعلمات
        url = f"{POLLINATIONS_API_URL}/{encoded_prompt}"
        params = {
            "model": model,
            "width": min(width, 1024),
            "height": min(height, 1024),
            "seed": None,  # عشوائي
            "nologo": "true"  # إزالة الشعار
        }
        
        logger.info(f"🎨 جاري توليد صورة باستخدام نموذج {model}...")
        logger.debug(f"URL: {url}, Params: {params}")
        
        # إرسال الطلب
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_io = io.BytesIO(image_data)
                    image_io.seek(0)
                    logger.info(f"✅ تم توليد الصورة بنجاح!")
                    return image_io
                else:
                    error_text = await response.text()
                    logger.error(f"❌ فشل توليد الصورة. Status: {response.status}, Error: {error_text}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error("❌ انتهت مهلة توليد الصورة (120 ثانية)")
        return None
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع أثناء توليد الصورة: {e}", exc_info=True)
        return None

def get_available_models_text() -> str:
    """إرجاع قائمة بالنماذج المتاحة مع وصفها."""
    models_list = "\n".join([f"• `{code}`: {desc}" for code, desc in AVAILABLE_MODELS.items()])
    return f"**النماذج المتاحة:**\n{models_list}\n\n*النموذج الافتراضي هو `flux`.*"
