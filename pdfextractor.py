import pdfplumber
import re

def extract_text_by_page(pdf_path):
    """回傳每頁文字列表"""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # 移除中文與標點
                clean_text = re.sub(
                    r"[\u4e00-\u9fff，。！？【】（）《》；：]", "", text
                )
                pages_text.append(clean_text)
    return pages_text
