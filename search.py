import faiss
import numpy as np
import json
from utils import embed_text

with open("exam_chunks_meta.json", "r", encoding="utf-8") as f:
    metadatas = json.load(f)

index = faiss.read_index("exam_chunks.faiss")

prompt = input("請輸入想搜尋的內容")

query_vec = embed_text(prompt)

if isinstance(query_vec[0], list):
    query_vec = np.array(query_vec, dtype="float32")
else:
    query_vec = np.array([query_vec], dtype="float32")

k = 10
distances, indices = index.search(query_vec, k)

for idx, dist in zip(indices[0], distances[0]):
    meta = metadatas[idx]
    print(
        f"距離: {dist:.4f} | 題目類型: {meta['chunk_type']} | 文法類型: {meta['grammar_points']} 來源: {meta['source']}"
    )
    print(meta["chunk_text"])
    print("=" * 50)
