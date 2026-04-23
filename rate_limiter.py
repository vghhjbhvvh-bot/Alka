import logging
import time
from typing import Dict
from collections import deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    مدير معدل الطلبات (Rate Limiter) لمنع الإساءة والحفاظ على استقرار الخدمة.
    يسمح بعدد محدود من الطلبات لكل مستخدم في فترة زمنية معينة.
    """

    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        تهيئة مدير معدل الطلبات.
        
        Args:
            max_requests: الحد الأقصى للطلبات المسموح بها.
            time_window: نافذة الوقت بالثواني.
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.user_requests: Dict[int, deque] = {}

    def is_allowed(self, user_id: int) -> bool:
        """
        التحقق مما إذا كان المستخدم مسموحاً له بإرسال طلب جديد.
        
        Args:
            user_id: معرف المستخدم.
        
        Returns:
            True إذا كان مسموحاً، False بخلاف ذلك.
        """
        current_time = time.time()
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = deque()
        
        # حذف الطلبات القديمة خارج نافذة الوقت
        while self.user_requests[user_id] and \
              current_time - self.user_requests[user_id][0] > self.time_window:
            self.user_requests[user_id].popleft()
        
        # التحقق من عدد الطلبات الحالية
        if len(self.user_requests[user_id]) < self.max_requests:
            self.user_requests[user_id].append(current_time)
            return True
        
        logger.warning(f"⚠️ المستخدم {user_id} تجاوز حد معدل الطلبات")
        return False

    def get_remaining_requests(self, user_id: int) -> int:
        """الحصول على عدد الطلبات المتبقية للمستخدم."""
        current_time = time.time()
        
        if user_id not in self.user_requests:
            return self.max_requests
        
        # حذف الطلبات القديمة
        while self.user_requests[user_id] and \
              current_time - self.user_requests[user_id][0] > self.time_window:
            self.user_requests[user_id].popleft()
        
        return max(0, self.max_requests - len(self.user_requests[user_id]))

    def get_reset_time(self, user_id: int) -> float:
        """الحصول على الوقت المتبقي قبل إعادة تعيين العداد (بالثواني)."""
        if user_id not in self.user_requests or not self.user_requests[user_id]:
            return 0
        
        oldest_request = self.user_requests[user_id][0]
        reset_time = oldest_request + self.time_window - time.time()
        return max(0, reset_time)

    def reset_user(self, user_id: int) -> None:
        """إعادة تعيين عداد الطلبات للمستخدم."""
        if user_id in self.user_requests:
            self.user_requests[user_id].clear()
            logger.info(f"🔄 تم إعادة تعيين عداد الطلبات للمستخدم {user_id}")
