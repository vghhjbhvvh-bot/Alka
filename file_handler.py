import os
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# محاولة استيراد مكتبات معالجة الملفات (اختيارية)
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("مكتبة PyPDF2 غير مثبتة. دعم PDF غير مفعل.")

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    logger.warning("مكتبة python-docx غير مثبتة. دعم DOCX غير مفعل.")

async def extract_text_from_file(file) -> Optional[str]:
    """
    استخراج النص من ملف بناءً على امتداده.
    تدعم: .txt, .py, .js, .html, .css, .json, .pdf, .docx
    """
    file_name = getattr(file, 'file_name', 'unknown')
    if not file_name:
        # محاولة الحصول على اسم الملف من المسار
        file_name = getattr(file, 'file_path', 'unknown')
    ext = os.path.splitext(file_name)[1].lower()

    # ملفات نصية بسيطة
    if ext in ['.txt', '.py', '.js', '.html', '.css', '.json', '.md', '.csv', '.log']:
        try:
            # تنزيل الملف إلى مسار مؤقت
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=ext, encoding='utf-8') as tmp:
                file_path = tmp.name
            await file.download_to_drive(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            os.unlink(file_path)
            return content
        except UnicodeDecodeError:
            # محاولة قراءة كـ bytes وتحويلها
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    file_path = tmp.name
                await file.download_to_drive(file_path)
                with open(file_path, 'rb') as f:
                    raw = f.read()
                os.unlink(file_path)
                # محاولة فك الترميز
                return raw.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.error(f"فشل قراءة الملف النصي {file_name}: {e}")
                return None

    # PDF
    elif ext == '.pdf' and PDF_SUPPORT:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                file_path = tmp.name
            await file.download_to_drive(file_path)
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            os.unlink(file_path)
            return text.strip() if text else None
        except Exception as e:
            logger.error(f"فشل استخراج النص من PDF {file_name}: {e}")
            return None

    # DOCX
    elif ext == '.docx' and DOCX_SUPPORT:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                file_path = tmp.name
            await file.download_to_drive(file_path)
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            os.unlink(file_path)
            return text.strip() if text else None
        except Exception as e:
            logger.error(f"فشل استخراج النص من DOCX {file_name}: {e}")
            return None

    else:
        logger.warning(f"نوع الملف غير مدعوم: {ext}")
        return None
