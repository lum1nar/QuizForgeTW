import faiss
import requests
import numpy as np
import json

API_URL = "http://localhost:11434/api/embed"
EMBEDDINGMODEL = "embeddinggemma"
# EMBEDDINGMODEL = "qwen3-embedding:4b"
# EMBEDDINGMODEL = "nomic-embed-text:latest"

def embed_text(text, model=EMBEDDINGMODEL):
    resp = requests.post(
        API_URL,
        json={"model": model, "input": text},
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]
    # return resp.json()

# open matadata
with open("exam_chunks_meta.json", "r", encoding="utf-8") as f:
    metadatas = json.load(f)

# 1️⃣ 讀取已存的 faiss index
index = faiss.read_index("exam_chunks.faiss")

# 2️⃣ 定義你的 prompt
# prompt = "九年級 上學期 第二次段考"
# prompt = "未來式"
# prompt = "reading_questions"
prompt = "被動語態"

# 3️⃣ 將 prompt 轉成向量
query_vec = embed_text(prompt)

# 確保形狀是 (1, dim)
if isinstance(query_vec[0], list):
    query_vec = np.array(query_vec, dtype="float32")
else:
    query_vec = np.array([query_vec], dtype="float32")

# 4️⃣ 搜索，取前 k 個最相似
k = 10
distances, indices = index.search(query_vec, k)

# 5️⃣ 根據 indices 找回 metadata
for idx, dist in zip(indices[0], distances[0]):
    meta = metadatas[idx]
    print(
        f"距離: {dist:.4f} | 題目類型: {meta['chunk_type']} | 文法類型: {meta['grammar_points']} 來源: {meta['source']}"
    )
    print(meta["chunk_text"])
    print("=" * 50)
