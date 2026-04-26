import io
import logging
import aiohttp
import asyncio
from config import HF_API_KEY
from typing import Optional

logger = logging.getLogger(__name__)

# استخدام نماذج مجانية تعمل فعلاً على Hugging Face Inference API
HF_API_URL_PRIMARY = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
HF_API_URL_SECONDARY = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"
# يمكن إضافة المزيد من النماذج كـ fallback إذا لزم الأمر

async def _generate_hf(api_url: str, prompt: str) -> Optional[io.BytesIO]:
    if not HF_API_KEY:
        logger.error("❌ مفتاح HF_API_KEY غير موجود في الإعدادات")
        return None
        
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    # تصحيح الـ payload ليتناسب مع متطلبات Hugging Face Inference API (فقط inputs)
    payload = {"inputs": prompt}
    
    try:
        async with aiohttp.ClientSession() as session:
            # محاولة أولى مع timeout أطول
            async with session.post(api_url, headers=headers, json=payload,
                                    timeout=aiohttp.ClientTimeout(total=180)) as response:
                if response.status == 200:
                    content = await response.read()
                    if content.startswith(b'{'):
                        logger.error(f"❌ استجابة HF ليست صورة: {content.decode('utf-8', errors='ignore')}")
                        return None
                    return io.BytesIO(content)
                elif response.status == 503:
                    logger.warning(f"⚠️ النموذج {api_url.split('/')[-1]} قيد التحميل، جاري الانتظار وإعادة المحاولة...")
                    await asyncio.sleep(30) # انتظار أطول
                    # محاولة ثانية بعد الانتظار
                    async with session.post(api_url, headers=headers, json=payload,
                                            timeout=aiohttp.ClientTimeout(total=180)) as retry_response:
                        if retry_response.status == 200:
                            content = await retry_response.read()
                            if not content.startswith(b'{'):
                                return io.BytesIO(content)
                        error_text = await retry_response.text()
                        logger.error(f"❌ خطأ في استجابة HF بعد إعادة المحاولة ({api_url.split('/')[-1]}): {retry_response.status} - {error_text}")
                        return None
                
                error_text = await response.text()
                logger.error(f"❌ خطأ في استجابة HF ({api_url.split('/')[-1]}): {response.status} - {error_text}")
                return None
    except Exception as e:
        logger.error(f"❌ خطأ استثناء HF: {type(e).__name__} - {e}")
        return None

async def generate_image(prompt: str) -> Optional[io.BytesIO]:
    """توليد صورة باستخدام Hugging Face حصراً مع محاولات لنماذج مختلفة لضمان الجودة والتوفر."""
    logger.info(f"🎨 بدء توليد صورة باستخدام HF: {prompt[:50]}...")
    
    # المحاولة 1: النموذج الأساسي (stabilityai/stable-diffusion-2-1)
    result = await _generate_hf(HF_API_URL_PRIMARY, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (stabilityai/stable-diffusion-2-1)")
        return result
        
    # المحاولة 2: CompVis/stable-diffusion-v1-4
    result = await _generate_hf(HF_API_URL_SECONDARY, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (CompVis/stable-diffusion-v1-4)")
        return result
        
    logger.error("❌ فشلت جميع محاولات التوليد عبر Hugging Face")
    return None
