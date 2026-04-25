import io
import logging
import aiohttp
import asyncio
from config import HF_API_KEY
from typing import Optional

logger = logging.getLogger(__name__)

# استخدام نماذج قوية من Hugging Face
# FLUX.1-schnell هو نموذج قوي جداً وسريع
HF_API_URL_PRIMARY = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
# نماذج احتياطية قوية
HF_API_URL_SECONDARY = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_API_URL_TERTIARY = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

async def _generate_hf(api_url: str, prompt: str) -> Optional[io.BytesIO]:
    if not HF_API_KEY:
        logger.error("❌ مفتاح HF_API_KEY غير موجود في الإعدادات")
        return None
        
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "guidance_scale": 7.5,
            "num_inference_steps": 50,
            "width": 1024,
            "height": 1024
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload,
                                    timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status == 200:
                    return io.BytesIO(await response.read())
                elif response.status == 503:
                    # النموذج قيد التحميل، انتظر قليلاً وأعد المحاولة
                    logger.warning(f"⚠️ النموذج {api_url.split('/')[-1]} قيد التحميل، جاري الانتظار...")
                    await asyncio.sleep(20)
                    async with session.post(api_url, headers=headers, json=payload,
                                            timeout=aiohttp.ClientTimeout(total=90)) as retry:
                        if retry.status == 200:
                            return io.BytesIO(await retry.read())
                
                logger.error(f"❌ خطأ في استجابة HF ({api_url.split('/')[-1]}): {response.status}")
                return None
    except Exception as e:
        logger.error(f"❌ خطأ استثناء HF: {type(e).__name__} - {e}")
        return None

async def generate_image(prompt: str) -> Optional[io.BytesIO]:
    """توليد صورة باستخدام Hugging Face حصراً مع محاولات لنماذج مختلفة لضمان الجودة والتوفر."""
    logger.info(f"🎨 بدء توليد صورة باستخدام HF: {prompt[:50]}...")
    
    # المحاولة 1: النموذج الأساسي (FLUX.1)
    result = await _generate_hf(HF_API_URL_PRIMARY, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (FLUX.1-schnell)")
        return result
        
    # المحاولة 2: SDXL
    result = await _generate_hf(HF_API_URL_SECONDARY, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (SDXL)")
        return result
        
    # المحاولة 3: SD v1.5
    result = await _generate_hf(HF_API_URL_TERTIARY, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (Stable Diffusion v1.5)")
        return result
    
    logger.error("❌ فشلت جميع محاولات التوليد عبر Hugging Face")
    return None
