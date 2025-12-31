import pdfplumber
import requests
import faiss
import json
import os
import re
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"
API_KEY = os.getenv("API_KEY")
EMBEDDING_URL = "http://localhost:11434/api/embed"
EMBEDDINGMODEL = "embeddinggemma"

def load_prompt(name: str, **kwargs):
    text = Path(f"prompts/{name}.txt").read_text(encoding="utf-8")
    return text.format(**kwargs)

def extract_text_by_page(pdf_path):
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

def extract_json_objects_from_text(text):
    objects = []
    stack = []
    start = None

    for i, ch in enumerate(text):
        if ch == "{":
            if not stack:
                start = i
            stack.append("{")
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    obj_text = text[start : i + 1]
                    objects.append(obj_text)
                    start = None
    return objects

def check_valid_jsons(extracted_json):
    valid_jsons = []
    for obj in extracted_json:
        try:
            valid_jsons.append(json.loads(obj))
        except json.JSONDecodeError:
            pass
    return valid_jsons

def embed_text(text, model=EMBEDDINGMODEL):
    resp = requests.post(
        EMBEDDING_URL,
        json={"model": model, "input": text},
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]
    # return resp.json()

def llm(prompt, llmmodel="gemma3:4b"):
    payload = {"model": llmmodel, "prompt": prompt, "stream": True}
    page_response = ""
    with requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        stream=True,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                token_json = json.loads(line.decode())
                token_text = token_json.get("response", "")
                page_response += token_text
    return page_response

def search_exam_chunks(query: str):
    with open("./json/exam_chunks_meta.json", "r", encoding="utf-8") as f:
        metadatas = json.load(f)

    # 1️⃣ 讀取已存的 faiss index
    index = faiss.read_index("exam_chunks.faiss")

    searchstr = ""
    query_vec = embed_text(query)

    # 確保形狀是 (1, dim)
    if isinstance(query_vec[0], list):
        query_vec = np.array(query_vec, dtype="float32")
    else:
        query_vec = np.array([query_vec], dtype="float32")

    # 4️⃣ 搜索，取前 k 個最相似
    k = 10
    distances, indices = index.search(query_vec, k)

    results = []
    # 5️⃣ 根據 indices 找回 metadata
    for idx, dist in zip(indices[0], distances[0]):
        meta = metadatas[idx]
        results.append(
            {
                "chunk_text": meta["chunk_text"],
                # "grammar_points": meta["grammar_points"],
                # "chunk_type": meta["chunk_type"],
                # "filename": meta["filename"],
            }
        )
        print(
            f"距離: {dist:.4f} | 題目類型: {meta['chunk_type']} | 文法類型: {meta['grammar_points']} 來源: {meta['source']}"
        )
        print(meta["chunk_text"])
        print("=" * 50)

        searchstr += f"\n距離: {dist:.4f} | 題目類型: {meta['chunk_type']} | 文法類型: {meta['grammar_points']} 來源: {meta['source']}\n"
        searchstr += meta["chunk_text"] + "\n"
        searchstr += "=" * 50 + "\n"

    return results, searchstr
