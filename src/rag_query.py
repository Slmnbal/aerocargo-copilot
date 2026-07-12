import chromadb
from sentence_transformers import SentenceTransformer
import ollama

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_or_create_collection("aerocargo_docs")

def soru_cevapla(soru):
    soru_embedding = model.encode([soru]).tolist()
    sonuclar = collection.query(query_embeddings=soru_embedding, n_results=2)
    baglam = "\n\n".join(sonuclar["documents"][0])

    prompt = f"""Aşağıdaki doküman parçalarını kullanarak soruyu cevapla.
Sadece verilen bilgiye dayan, bilmiyorsan "Bu bilgi dokümanlarda yok" de.

Dokümanlar:
{baglam}

Soru: {soru}

Cevap:"""

    yanit = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    return yanit["message"]["content"]

if __name__ == "__main__":
    soru = "Havalimanı slot kısıtı nasıl belirleniyor?"
    print(f"Soru: {soru}\n")
    print(f"Cevap: {soru_cevapla(soru)}")
