import os
import logging
import tempfile
from typing import Optional, Tuple
import PyPDF2
import docx

logger = logging.getLogger(__name__)

# امتدادات الأكواد المدعومة
CODE_EXTENSIONS = [
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".go", ".rs", ".php", 
    ".rb", ".swift", ".kt", ".html", ".css", ".json", ".sql", ".sh", ".yaml", 
    ".yml", ".toml", ".md", ".txt", ".xml", ".bat", ".ps1", ".dart", ".lua"
]

async def extract_text_from_file(file_path: str, file_name: str) -> Tuple[Optional[str], bool]:
    """
    استخراج النص من ملف محلي. تعيد (النص, is_code).
    """
    ext = os.path.splitext(file_name)[1].lower()
    is_code = ext in CODE_EXTENSIONS
    
    try:
        # معالجة ملفات PDF
        if ext == ".pdf":
            text = ""
            try:
                with open(file_path, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text.strip(), False
            except PyPDF2.errors.PdfReadError as e:
                logger.error(f"❌ فشل قراءة ملف PDF {file_name}: {e}")
                return None, False
            
        # معالجة ملفات Word
        elif ext in [".docx", ".doc"]:
            try:
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text.strip(), False
            except Exception as e:
                logger.error(f"❌ فشل قراءة ملف Word {file_name}: {e}")
                return None, False
            
        # معالجة الملفات النصية والأكواد
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return content, is_code
            except UnicodeDecodeError:
                logger.warning(f"⚠️ فشل فك تشفير {file_name} باستخدام UTF-8، محاولة Latin-1.")
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                    return content, is_code
                except Exception as e:
                    logger.error(f"❌ فشل قراءة الملف النصي {file_name} بكلتا الترميزين: {e}")
                    return None, False
            except Exception as e:
                logger.error(f"❌ فشل قراءة الملف النصي {file_name}: {e}")
                return None, False
                
    except Exception as e:
        logger.error(f"❌ خطأ عام أثناء استخراج النص من {file_name}: {e}")
        return None, False
