import io
import logging
import aiohttp
import asyncio
from config import HF_API_KEY
from typing import Optional

logger = logging.getLogger(__name__)

HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

async def generate_image(prompt: str) -> Optional[io.BytesIO]:
    """
    توليد صورة باستخدام Hugging Face Inference API مع نموذج FLUX.1-schnell.
    """
    if not HF_API_KEY:
        logger.error("❌ مفتاح Hugging Face API غير موجود في متغيرات البيئة (HF_API_KEY).")
        return None

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}

    try:
        logger.info(f"🎨 جاري توليد صورة باستخدام Hugging Face API...")
        async with aiohttp.ClientSession() as session:
            async with session.post(HF_API_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=90)) as response:
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
        logger.error("❌ انتهت مهلة توليد الصورة (90 ثانية).")
        return None
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع أثناء توليد الصورة: {e}", exc_info=True)
        return None

def get_available_models_text() -> str:
    return "**النموذج المستخدم:** `black-forest-labs/FLUX.1-schnell` (سريع وعالي الجودة)"
