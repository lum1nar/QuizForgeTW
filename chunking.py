import json
import os
from dotenv import load_dotenv
from utils import (
    load_prompt,
    extract_text_by_page,
    extract_json_objects_from_text,
    check_valid_jsons,
    llm,
)

# ========================
# CONSTANTS
# ========================
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"
CHUNKED_LIST_FILE = "./json/chunked_pdfs.json"
OUTPUT_FILE = "./json/all_chunks.json"
PDF_DIR = "./pdf"

# ========================
# Load processed pdf list
# ========================
if os.path.exists(CHUNKED_LIST_FILE):
    with open(CHUNKED_LIST_FILE, "r", encoding="utf-8") as f:
        chunked_pdfs = set(json.load(f))
else:
    chunked_pdfs = set()

# ========================
# Scan PDF directory
# ========================
pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
print(f"📄 發現 {len(pdf_files)} 份 PDF")

# ========================
# main
# ========================
for pdf_file in pdf_files:

    if pdf_file in chunked_pdfs:
        print(f"⏩ 跳過已處理：{pdf_file}")
        continue

    pdf_path = os.path.join(PDF_DIR, pdf_file)
    print(f"\n🚀 開始處理：{pdf_file}")

    pages_text = extract_text_by_page(pdf_path)

    all_responses = []

    if "國中" in pdf_path:
        difficulty_level = "junior_high"
    elif "高中" in pdf_path:
        difficulty_level = "senior_high"
    else:
        difficulty_level = "junior_high"

    for page_num, page_text in enumerate(pages_text, start=1):
        print(
            f"\n=== 處理文件 {pdf_file} 第 {page_num} 頁 難度 {difficulty_level}===\n"
        )
        prompt = load_prompt(
            "chunk_prompt",
            content=page_text,
            difficulty_level=difficulty_level,
            pdf_path=pdf_path,
        )
        page_response = llm(prompt, "gpt-oss:120b")
        all_responses.append(page_response)

    # merge and check if the json is valid
    llm_response = "[{}]".format(",".join([r.strip("[]") for r in all_responses]))
    extracted_json = extract_json_objects_from_text(llm_response)
    print(f"抽出 {len(extracted_json)} 個 {{}}")
    valid_jsons = check_valid_jsons(extracted_json)

    # append the new valid jsons into OUTPUT_FILE
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            last_chunk = json.load(f)
    else:
        last_chunk = []

    last_chunk.extend(valid_jsons)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(last_chunk, f, ensure_ascii=False, indent=2)

    # Update chunked_pdfs
    chunked_pdfs.add(pdf_file)
    with open(CHUNKED_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(chunked_pdfs), f, ensure_ascii=False, indent=2)
