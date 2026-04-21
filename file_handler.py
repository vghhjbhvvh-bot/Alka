import os
import logging
import tempfile
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ... (استيراد المكتبات الاختيارية كما هو) ...
try: import PyPDF2; PDF_SUPPORT = True
except: PDF_SUPPORT = False
try: import docx; DOCX_SUPPORT = True
except: DOCX_SUPPORT = False

CODE_EXTENSIONS = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.html', '.css', '.json', '.sql', '.sh', '.yaml', '.yml', '.toml']

async def extract_text_from_file(file) -> Tuple[Optional[str], bool]:
    """
    استخراج النص من ملف. تعيد (النص, is_code) حيث is_code تكون True إذا كان الملف كوداً.
    """
    file_name = getattr(file, 'file_name', 'unknown')
    ext = os.path.splitext(file_name)[1].lower()
    is_code = ext in CODE_EXTENSIONS

    # محاولة قراءة الملف كنص
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=ext, encoding='utf-8') as tmp:
            file_path = tmp.name
        await file.download_to_drive(file_path)
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
        os.unlink(file_path)
        return content, is_code
    except UnicodeDecodeError:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp: file_path = tmp.name
            await file.download_to_drive(file_path)
            with open(file_path, 'rb') as f: raw = f.read()
            os.unlink(file_path)
            return raw.decode('utf-8', errors='ignore'), is_code
        except Exception as e:
            logger.error(f"فشل قراءة الملف {file_name}: {e}")
            return None, False
    except Exception as e:
        logger.error(f"فشل تنزيل الملف {file_name}: {e}")
        return None, False
