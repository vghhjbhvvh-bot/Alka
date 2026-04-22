import io
import logging
import aiohttp
import asyncio
import urllib.parse
from config import HF_API_KEY
from typing import Optional

logger = logging.getLogger(__name__)

# رابط Hugging Face الصحيح (بدون أي لاحقة إضافية)
HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
HF_API_URL_FALLBACK = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"

# Pollinations API (مجاني، لا يحتاج مفتاح)
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"

async def generate_with_huggingface(api_url: str, prompt: str) -> Optional[io.BytesIO]:
    """محاولة توليد صورة باستخدام Hugging Face."""
    if not HF_API_KEY:
        logger.error("❌ HF_API_KEY غير موجود.")
        return None

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}

    try:
        logger.info(f"🎨 محاولة Hugging Face: {api_url}")
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload, 
                                    timeout=aiohttp.ClientTimeout(total=90)) as response:
                
                if response.status == 200:
                    image_data = await response.read()
                    image_io = io.BytesIO(image_data)
                    image_io.seek(0)
                    logger.info("✅ تم توليد الصورة بنجاح باستخدام Hugging Face")
                    return image_io
                
                elif response.status == 503:
                    logger.warning("⏳ النموذج قيد التحميل، انتظار 15 ثانية...")
                    await asyncio.sleep(15)
                    # محاولة ثانية
                    async with session.post(api_url, headers=headers, json=payload,
                                            timeout=aiohttp.ClientTimeout(total=60)) as retry:
                        if retry.status == 200:
                            image_data = await retry.read()
                            return io.BytesIO(image_data)
                        else:
                            error_text = await retry.text()
                            logger.error(f"❌ فشل بعد الانتظار: {retry.status} - {error_text[:200]}")
                            return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ فشل Hugging Face: {response.status} - {error_text[:200]}")
                    return None
    except Exception as e:
        logger.error(f"❌ استثناء Hugging Face: {type(e).__name__} - {e}")
        return None


async def generate_with_pollinations(prompt: str) -> Optional[io.BytesIO]:
    """توليد صورة باستخدام Pollinations AI (مجاني بدون مفتاح)."""
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"{POLLINATIONS_URL}/{encoded_prompt}"
        params = {
            "model": "flux",
            "width": 1024,
            "height": 1024,
            "nologo": "true"
        }
        
        logger.info(f"🎨 محاولة Pollinations AI...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_io = io.BytesIO(image_data)
                    image_io.seek(0)
                    logger.info("✅ تم توليد الصورة بنجاح باستخدام Pollinations")
                    return image_io
                else:
                    error_text = await response.text()
                    logger.error(f"❌ فشل Pollinations: {response.status} - {error_text[:200]}")
                    return None
    except Exception as e:
        logger.error(f"❌ استثناء Pollinations: {type(e).__name__} - {e}")
        return None


async def generate_image(prompt: str) -> Optional[io.BytesIO]:
    """توليد الصورة: يحاول Hugging Face أولاً، ثم Pollinations."""
    
    logger.info(f"🎨 بدء توليد صورة للوصف: {prompt[:50]}...")
    
    # المحاولة 1: Hugging Face (Flux)
    result = await generate_with_huggingface(HF_API_URL, prompt)
    if result:
        return result
    
    # المحاولة 2: Hugging Face (Stable Diffusion)
    logger.warning("⚠️ فشل Flux. المحاولة مع Stable Diffusion...")
    result = await generate_with_huggingface(HF_API_URL_FALLBACK, prompt)
    if result:
        return result
    
    # المحاولة 3: Pollinations (مجاني)
    logger.warning("⚠️ فشل Hugging Face. المحاولة مع Pollinations...")
    result = await generate_with_pollinations(prompt)
    if result:
        return result
    
    logger.error("❌ فشلت جميع محاولات توليد الصورة.")
    return None


def get_available_models_text() -> str:
    return "**النماذج المستخدمة:** Flux / Stable Diffusion / Pollinations"
