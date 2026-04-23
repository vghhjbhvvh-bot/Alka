import io
import logging
import aiohttp
import asyncio
import urllib.parse
from config import HF_API_KEY, FAL_AI_API_KEY
from typing import Optional

logger = logging.getLogger(__name__)

# روابط API (داخلية فقط)
HF_API_URL_PRIMARY = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
HF_API_URL_FALLBACK = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"
FAL_AI_URL = "https://api.fal.ai/sdxl/image/generate"

async def _generate_hf(api_url: str, prompt: str) -> Optional[io.BytesIO]:
    if not HF_API_KEY:
        return None
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload,
                                    timeout=aiohttp.ClientTimeout(total=90)) as response:
                if response.status == 200:
                    return io.BytesIO(await response.read())
                elif response.status == 503:
                    await asyncio.sleep(15)
                    async with session.post(api_url, headers=headers, json=payload,
                                            timeout=aiohttp.ClientTimeout(total=60)) as retry:
                        if retry.status == 200:
                            return io.BytesIO(await retry.read())
                return None
    except Exception as e:
        logger.error(f"خطأ HF: {type(e).__name__}")
        return None

async def _generate_fal_ai(prompt: str) -> Optional[io.BytesIO]:
    if not FAL_AI_API_KEY:
        return None
    headers = {
        "Authorization": f"Key {FAL_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "model_name": "flux", # أو أي نموذج آخر مدعوم من Fal.ai
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 50,
        "guidance_scale": 7.5
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(FAL_AI_URL, headers=headers, json=payload,
                                    timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data.get("image_url")
                    if image_url:
                        async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as img_response:
                            if img_response.status == 200:
                                return io.BytesIO(await img_response.read())
                    return None
                else:
                    logger.error(f"خطأ Fal.ai API: {response.status} - {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"خطأ Fal.ai: {type(e).__name__} - {e}")
        return None

async def _generate_pollinations(prompt: str) -> Optional[io.BytesIO]:
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"{POLLINATIONS_URL}/{encoded}"
        params = {"model": "flux", "width": 1024, "height": 1024, "nologo": "true"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status == 200:
                    return io.BytesIO(await response.read())
                return None
    except Exception as e:
        logger.error(f"خطأ Pollinations: {type(e).__name__}")
        return None

async def generate_image(prompt: str) -> Optional[io.BytesIO]:
    """توليد صورة - يحاول عدة خدمات داخلية دون إظهار أسمائها للمستخدم."""
    logger.info(f"بدء توليد صورة: {prompt[:50]}...")
    
    # المحاولة 1: Fal.ai (الأفضلية)
    result = await _generate_fal_ai(prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (Fal.ai)")
        return result

    # المحاولة 2: Hugging Face Primary
    result = await _generate_hf(HF_API_URL_PRIMARY, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (Hugging Face الأساسية)")
        return result
    
    # المحاولة 3: Hugging Face Fallback
    result = await _generate_hf(HF_API_URL_FALLBACK, prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (Hugging Face الاحتياطية)")
        return result
    
    # المحاولة 4: Pollinations.ai
    result = await _generate_pollinations(prompt)
    if result:
        logger.info("✅ تم التوليد بنجاح (Pollinations.ai)")
        return result
    
    logger.error("❌ فشلت جميع محاولات التوليد")
    return None
