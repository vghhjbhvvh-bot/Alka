import base64
import groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME

# إنشاء عميل Groq
client = groq.Groq(api_key=GROQ_API_KEY)

def analyze_image(image_path: str) -> str:
    """
    تحليل صورة من مسار ملف وإرجاع الوصف.
    """
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # إرسال الطلب إلى Groq API باستخدام نموذج الرؤية
    chat_completion = client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "ماذا يظهر في هذه الصورة؟"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_string}"
                        }
                    }
                ]
            }
        ]
    )
    return chat_completion.choices[0].message.content
