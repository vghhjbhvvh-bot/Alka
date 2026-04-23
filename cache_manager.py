import logging
import time
from typing import Dict, Any, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

class CacheManager:
    """
    مدير ذاكرة التخزين المؤقت (Cache) لتحسين الأداء وتقليل عدد الطلبات إلى الخدمات الخارجية.
    يدعم انتهاء الصلاحية التلقائي للعناصر المخزنة.
    """

    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        تهيئة مدير الذاكرة المؤقتة.
        
        Args:
            max_size: الحد الأقصى لعدد العناصر المخزنة.
            ttl: مدة صلاحية العنصر بالثواني (Time To Live).
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """استرجاع عنصر من الذاكرة المؤقتة إذا كان صالحاً."""
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        if time.time() - item['timestamp'] > self.ttl:
            # انتهت صلاحية العنصر
            del self.cache[key]
            logger.info(f"🗑️ تم حذف العنصر المنتهي الصلاحية: {key}")
            return None
        
        # نقل العنصر إلى نهاية القائمة (LRU)
        self.cache.move_to_end(key)
        logger.debug(f"✅ تم استرجاع العنصر من الذاكرة المؤقتة: {key}")
        return item['value']

    def set(self, key: str, value: Any) -> None:
        """تخزين عنصر في الذاكرة المؤقتة."""
        if key in self.cache:
            # تحديث العنصر الموجود
            self.cache.move_to_end(key)
        
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
        # حذف أقدم عنصر إذا تجاوزنا الحد الأقصى
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.info(f"🗑️ تم حذف أقدم عنصر لتحرير الذاكرة: {oldest_key}")
        
        logger.debug(f"💾 تم تخزين العنصر في الذاكرة المؤقتة: {key}")

    def clear(self) -> None:
        """مسح جميع العناصر من الذاكرة المؤقتة."""
        self.cache.clear()
        logger.info("🧹 تم مسح جميع العناصر من الذاكرة المؤقتة")

    def size(self) -> int:
        """الحصول على عدد العناصر المخزنة حالياً."""
        return len(self.cache)

    def cleanup_expired(self) -> None:
        """حذف جميع العناصر المنتهية الصلاحية."""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time - item['timestamp'] > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"🧹 تم حذف {len(expired_keys)} عناصر منتهية الصلاحية")
