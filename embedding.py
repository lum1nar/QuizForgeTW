import requests
import json
import uuid
import faiss
import numpy as np

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

with open("./all_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(chunks)
print()
print(chunks[0]["chunk_text"])
texts = []
metadatas = []
embeddings = []

for chunk in chunks:
    text = chunk["chunk_text"]
    chunk_id = str(uuid.uuid4())
    # full_text = f"{chunk['chunk_text']} | 文法: {', '.join(chunk['grammar_points'])} | 類型: {chunk['chunk_type']}"
    full_text = (
        f"{chunk['chunk_text']} "
        f"| 文法: {', '.join(chunk['grammar_points'])} "
        f"| 類型: {chunk['chunk_type']} "
        f"| 來源試卷: {chunk['filename']}"
    )

    print(full_text)
    vec = embed_text(full_text)

    embeddings.append(vec)
    texts.append(text)
    metadatas.append(
        {
            "chunk_type": chunk["chunk_type"],
            "level": chunk["level"],
            "grammar_points": chunk["grammar_points"],
            "index": chunk_id,
            "chunk_text": chunk["chunk_text"],
            "source": chunk["filename"],
        }
    )

# print(embeddings[0][0])
flat_embeddings = [vec[0] if isinstance(vec[0], list) else vec for vec in embeddings]

dim = len(flat_embeddings[0])
index = faiss.IndexFlatL2(dim)
index.add(np.array(flat_embeddings).astype("float32"))

faiss.write_index(index, "exam_chunks.faiss")

# metadata 另外存
with open("exam_chunks_meta.json", "w", encoding="utf-8") as f:
    json.dump(metadatas, f, ensure_ascii=False, indent=2)
