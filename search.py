import faiss
import numpy as np
import json
from utils import embed_text

# open matadata
with open("exam_chunks_meta.json", "r", encoding="utf-8") as f:
    metadatas = json.load(f)

# 1️⃣ 讀取已存的 faiss index
index = faiss.read_index("exam_chunks.faiss")

# 2️⃣ 定義你的 prompt
prompt = input("請輸入想搜尋的內容")

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
