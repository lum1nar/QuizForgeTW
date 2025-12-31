import json
import uuid
import faiss
import numpy as np
from utils import embed_text

INPUT_FILE = "./json/all_chunks.json"
METADATA_FILE = "./json/exam_chunks_meta.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

metadatas = []
embeddings = []

for chunk in chunks:
    text = chunk["chunk_text"]
    chunk_id = str(uuid.uuid4())
    full_text = (
        f"{chunk['chunk_text']} "
        f"| 文法: {', '.join(chunk['grammar_points'])} "
        f"| 類型: {chunk['chunk_type']} "
        f"| 來源試卷: {chunk['filename']}"
    )

    print(f"""正在 embedding \n{full_text}\n""")
    vec = embed_text(full_text)

    embeddings.append(vec)
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

flat_embeddings = [vec[0] if isinstance(vec[0], list) else vec for vec in embeddings]

dim = len(flat_embeddings[0])
index = faiss.IndexFlatL2(dim)
index.add(np.array(flat_embeddings).astype("float32"))

faiss.write_index(index, "exam_chunks.faiss")

# metadata 另外存
with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(metadatas, f, ensure_ascii=False, indent=2)
