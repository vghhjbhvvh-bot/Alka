import io
import logging
import aiohttp
import asyncio
from config import HF_API_KEY
from typing import Optional

logger = logging.getLogger(__name__)

# النموذج الأساسي (سريع، جودة ممتازة)
HF_API_URL_PRIMARY = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
# النموذج الاحتياطي (مستقر جداً)
HF_API_URL_FALLBACK = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"

async def generate_with_model(api_url: str, prompt: str) -> Optional[io.BytesIO]:
    """محاولة توليد صورة باستخدام نموذج محدد."""
    if not HF_API_KEY:
        logger.error("❌ HF_API_KEY غير موجود.")
        return None

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}  # انتظار تحميل النموذج

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload, 
                                    timeout=aiohttp.ClientTimeout(total=120)) as response:
                
                if response.status == 200:
                    image_data = await response.read()
                    image_io = io.BytesIO(image_data)
                    image_io.seek(0)
                    return image_io
                
                elif response.status == 503:
                    logger.warning(f"⏳ النموذج قيد التحميل (503). انتظر 20 ثانية وأعد المحاولة...")
                    await asyncio.sleep(20)
                    # محاولة ثانية
                    async with session.post(api_url, headers=headers, json=payload,
                                            timeout=aiohttp.ClientTimeout(total=60)) as retry_response:
                        if retry_response.status == 200:
                            image_data = await retry_response.read()
                            return io.BytesIO(image_data)
                        else:
                            error_text = await retry_response.text()
                            logger.error(f"❌ فشل بعد الانتظار: {retry_response.status} - {error_text}")
                            return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ فشل التوليد: {response.status} - {error_text[:200]}")
                    return None
    except asyncio.TimeoutError:
        logger.error(f"❌ مهلة (Timeout) عند استخدام {api_url}")
        return None
    except Exception as e:
        logger.error(f"❌ استثناء غير متوقع: {type(e).__name__} - {e}")
        return None

async def generate_image(prompt: str) -> Optional[io.BytesIO]:
    """توليد الصورة باستخدام النموذج الأساسي، والاحتياطي عند الفشل."""
    
    logger.info(f"🎨 بدء توليد صورة للوصف: {prompt[:50]}...")
    
    # المحاولة الأولى: النموذج الأساسي (Flux)
    result = await generate_with_model(HF_API_URL_PRIMARY, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح باستخدام Flux")
        return result
    
    # المحاولة الثانية: النموذج الاحتياطي (Stable Diffusion)
    logger.warning("⚠️ فشل النموذج الأساسي. المحاولة باستخدام النموذج الاحتياطي...")
    result = await generate_with_model(HF_API_URL_FALLBACK, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح باستخدام Stable Diffusion 2.1")
        return result
    
    logger.error("❌ فشلت جميع محاولات توليد الصورة.")
    return None

def get_available_models_text() -> str:
    return "**النموذج المستخدم:** Flux (رئيسي) / Stable Diffusion 2.1 (احتياطي)"
