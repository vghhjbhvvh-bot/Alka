import logging
from collections import deque
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """إدارة تاريخ المحادثة لكل مستخدم مع حد أقصى لعدد الرسائل."""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        # في الإنتاج، يمكن استخدام pickle persistence، لكننا نستخدم قاموساً بسيطاً للتوضيح
        # سيكون التخزين في context.user_data باستخدام python-telegram-bot persistence
        self._storage: Dict[int, deque] = {}

    def add_message(self, user_id: int, role: str, content: str):
        """إضافة رسالة إلى تاريخ المستخدم."""
        if user_id not in self._storage:
            self._storage[user_id] = deque(maxlen=self.max_messages)
        self._storage[user_id].append({"role": role, "content": content})
        logger.debug(f"تمت إضافة رسالة للمستخدم {user_id}. العدد الحالي: {len(self._storage[user_id])}")

    def get_history(self, user_id: int) -> List[Dict[str, str]]:
        """استرجاع تاريخ المحادثة كقائمة منسقة لـ Groq API."""
        if user_id not in self._storage:
            return []
        return list(self._storage[user_id])

    def clear_history(self, user_id: int):
        """مسح تاريخ مستخدم معين."""
        if user_id in self._storage:
            del self._storage[user_id]
            logger.info(f"تم مسح تاريخ المحادثة للمستخدم {user_id}")

    def trim_history(self, user_id: int, max_tokens_estimate: int = 3000):
        """
        تقليم التاريخ بناءً على تقدير عدد الرموز.
        (تطبيق بسيط: يحتفظ بعدد max_messages فقط)
        """
        # تطبيق بسيط: نعتمد على maxlen المحدد مسبقاً
        pass
