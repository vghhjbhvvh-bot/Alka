import logging
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 5) -> str:
    """
    البحث في الإنترنت باستخدام DuckDuckGo API المجاني.
    """
    logger.info(f"🔍 جاري البحث في الإنترنت عن: {query}")
    
    # استخدام DuckDuckGo HTML search أو API بسيط
    # ملاحظة: DuckDuckGo ليس لديه API رسمي مفتوح بالكامل للنتائج الكاملة بدون مفتاح، 
    # ولكن يمكن استخدام محرك بحث مثل DDG أو البحث عن إجابات فورية.
    # هنا سنستخدم API الإجابات الفورية كخيار أول، ثم يمكن التوسع.
    
    try:
        # محاولة الحصول على إجابة فورية
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        results = []
        
        # إضافة الإجابة الفورية إذا وجدت
        if data.get("AbstractText"):
            results.append(f"📌 ملخص: {data['AbstractText']}")
        
        # إضافة الروابط المتعلقة
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if "Text" in topic and "FirstURL" in topic:
                results.append(f"🔹 {topic['Text']}\n🔗 {topic['FirstURL']}")
        
        if not results:
            # إذا لم نجد نتائج في API الإجابات الفورية، نستخدم بحثاً نصياً بسيطاً (محاكاة)
            # في بيئة الإنتاج يفضل استخدام Serper.dev أو Google Custom Search
            return "لم أتمكن من العثور على نتائج دقيقة في البحث الفوري. حاول صياغة سؤالك بشكل أوضح."
            
        return "\n\n".join(results)
        
    except Exception as e:
        logger.error(f"❌ فشل البحث في الإنترنت: {e}")
        return f"حدث خطأ أثناء محاولة البحث في الإنترنت: {e}"

def format_search_prompt(query: str, search_results: str) -> str:
    """
    تنسيق نتائج البحث لتزويدها للنموذج.
    """
    return (
        f"المستخدم يسأل عن: {query}\n\n"
        f"لقد بحثت في الإنترنت ووجدت النتائج التالية:\n"
        f"---"
        f"{search_results}\n"
        f"---"
        f"بناءً على هذه المعلومات، أجب على سؤال المستخدم بدقة وباللغة العربية."
    )
