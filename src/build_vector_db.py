import os
import chromadb
from sentence_transformers import SentenceTransformer

# Embedding modeli: metni anlam taşıyan sayısal vektöre çevirir (yerel, ücretsiz, ~80MB)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Chroma istemcisi: vektör veritabanını diske kalıcı olarak kaydeder
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_or_create_collection("aerocargo_docs")

# docs/ klasöründeki tüm .md dosyalarını oku
documents, ids = [], []
for filename in os.listdir("docs"):
    if filename.endswith(".md"):
        with open(os.path.join("docs", filename), "r", encoding="utf-8") as f:
            documents.append(f.read())
        ids.append(filename)

# Metinleri embedding'e çevir ve Chroma'ya kaydet
embeddings = model.encode(documents).tolist()
collection.add(documents=documents, embeddings=embeddings, ids=ids)
print(f"{len(documents)} doküman vektör veritabanına eklendi.")

# Test sorgusu: bir soru sor, en alakalı dokümanları getir
soru = "Düşük talepli bir rotayı neden tamamen kapatmıyoruz?"
soru_embedding = model.encode([soru]).tolist()
sonuclar = collection.query(query_embeddings=soru_embedding, n_results=2)

print("\nEn alakalı dokümanlar:")
for doc_id, doc_text in zip(sonuclar["ids"][0], sonuclar["documents"][0]):
    print(f"\n--- {doc_id} ---")
    print(doc_text[:300])
