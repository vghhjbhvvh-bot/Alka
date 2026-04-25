import os
import logging
import tempfile
from typing import Optional, Tuple
import PyPDF2
import docx

logger = logging.getLogger(__name__)

# امتدادات الأكواد المدعومة
CODE_EXTENSIONS = [
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php', 
    '.rb', '.swift', '.kt', '.html', '.css', '.json', '.sql', '.sh', '.yaml', 
    '.yml', '.toml', '.md', '.txt', '.xml', '.bat', '.ps1', '.dart', '.lua'
]

async def extract_text_from_file(file_path: str, file_name: str) -> Tuple[Optional[str], bool]:
    """
    استخراج النص من ملف محلي. تعيد (النص, is_code).
    """
    ext = os.path.splitext(file_name)[1].lower()
    is_code = ext in CODE_EXTENSIONS
    
    try:
        # معالجة ملفات PDF
        if ext == '.pdf':
            text = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip(), False
            
        # معالجة ملفات Word
        elif ext in ['.docx', '.doc']:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip(), False
            
        # معالجة الملفات النصية والأكواد
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content, is_code
            except UnicodeDecodeError:
                # محاولة القراءة بتنسيقات أخرى إذا فشل utf-8
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                return content, is_code
                
    except Exception as e:
        logger.error(f"❌ فشل استخراج النص من {file_name}: {e}")
        return None, False
