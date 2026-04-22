import io
import logging
import aiohttp
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# إعدادات Prodia API
PRODIA_API_URL = "https://api.prodia.com/v1/job"
PRODIA_API_KEY = None  # Prodia مجاني حتى 1000 صورة/شهر بدون مفتاح

# إعدادات Pollinations API كخيار احتياطي
POLLINATIONS_API_URL = "https://gen.pollinations.ai/image"

async def generate_image_prodia(prompt: str, model: str = "sd_xl_base_1.0.safetensors [31e35c80fc]", width: int = 1024, height: int = 1024) -> Optional[io.BytesIO]:
    """توليد صورة باستخدام Prodia API."""
    try:
        headers = {"Content-Type": "application/json"}
        if PRODIA_API_KEY:
            headers["X-Prodia-Key"] = PRODIA_API_KEY

        payload = {
            "prompt": prompt,
            "model": model,
            "negative_prompt": "worst quality, blurry",
            "steps": 25,
            "cfg_scale": 7,
            "aspect_ratio": "square",
            "width": width,
            "height": height,
            "seed": -1,
            "sampler": "DPM++ 2M Karras"
        }

        logger.info(f"🎨 جاري توليد صورة باستخدام Prodia...")

        async with aiohttp.ClientSession() as session:
            # الخطوة 1: إنشاء مهمة التوليد
            async with session.post(PRODIA_API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ فشل إنشاء مهمة Prodia. Status: {response.status}, Error: {error_text}")
                    return None

                job_data = await response.json()
                job_id = job_data.get("job")

                if not job_id:
                    logger.error("❌ لم يتم استلام job_id من Prodia")
                    return None

            # الخطوة 2: انتظار اكتمال التوليد
            max_attempts = 30
            for attempt in range(max_attempts):
                await asyncio.sleep(1)
                async with session.get(f"{PRODIA_API_URL}/{job_id}", headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        continue

                    job_status = await response.json()
                    status = job_status.get("status")

                    if status == "succeeded":
                        image_url = job_status.get("image_url")
                        if image_url:
                            # الخطوة 3: تحميل الصورة
                            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as img_response:
                                if img_response.status == 200:
                                    image_data = await img_response.read()
                                    image_io = io.BytesIO(image_data)
                                    image_io.seek(0)
                                    logger.info(f"✅ تم توليد الصورة بنجاح باستخدام Prodia!")
                                    return image_io
                        break
                    elif status == "failed":
                        logger.error(f"❌ فشل توليد الصورة في Prodia")
                        break

            return None

    except asyncio.TimeoutError:
        logger.error("❌ انتهت مهلة توليد الصورة باستخدام Prodia")
        return None
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع أثناء توليد الصورة باستخدام Prodia: {e}", exc_info=True)
        return None

async def generate_image_pollinations(prompt: str, model: str = "flux", width: int = 1024, height: int = 1024) -> Optional[io.BytesIO]:
    """توليد صورة باستخدام Pollinations API (كخيار احتياطي)."""
    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)

        url = f"{POLLINATIONS_API_URL}/{encoded_prompt}"
        params = {
            "model": model,
            "width": min(width, 1024),
            "height": min(height, 1024),
            "seed": -1,
            "nologo": "true"
        }

        logger.info(f"🎨 جاري توليد صورة باستخدام Pollinations (احتياطي)...")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_io = io.BytesIO(image_data)
                    image_io.seek(0)
                    logger.info(f"✅ تم توليد الصورة بنجاح باستخدام Pollinations!")
                    return image_io
                else:
                    error_text = await response.text()
                    logger.error(f"❌ فشل توليد الصورة باستخدام Pollinations. Status: {response.status}, Error: {error_text}")
                    return None

    except asyncio.TimeoutError:
        logger.error("❌ انتهت مهلة توليد الصورة باستخدام Pollinations")
        return None
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع أثناء توليد الصورة باستخدام Pollinations: {e}", exc_info=True)
        return None

async def generate_image(prompt: str, model: str = "flux", width: int = 1024, height: int = 1024) -> Optional[io.BytesIO]:
    """
    توليد صورة باستخدام أفضل واجهة برمجة تطبيقات متاحة.
    يحاول Prodia أولاً، ثم يلجأ إلى Pollinations.
    """
    # المحاولة الأولى: Prodia
    image_data = await generate_image_prodia(prompt, "sd_xl_base_1.0.safetensors [31e35c80fc]", width, height)
    if image_data:
        return image_data

    # المحاولة الثانية: Pollinations
    logger.info("⚠️ Prodia فشل، جاري المحاولة باستخدام Pollinations...")
    return await generate_image_pollinations(prompt, model, width, height)

def get_available_models_text() -> str:
    """إرجاع قائمة بالنماذج المتاحة مع وصفها."""
    return "**النماذج المتاحة:**\n• `flux` (افتراضي): جودة عالية\n• `turbo`: سريع\n• `realistic`: واقعي\n• `anime`: أنمي"
