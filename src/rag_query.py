from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
import ollama

# Proje köküne göre mutlak yol: MCP gibi bu script'i hangi dizinden çalıştıracağı belli
# olmayan istemcilerden çağrıldığında da (cwd her zaman proje kökü olmayabilir) doğru
# data/chroma_db klasörünü bulabilsin diye.
PROJE_KOKU = Path(__file__).resolve().parent.parent

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=str(PROJE_KOKU / "data" / "chroma_db"))
collection = client.get_or_create_collection("aerocargo_docs")

def soru_cevapla(soru):
    soru_embedding = model.encode([soru]).tolist()
    sonuclar = collection.query(query_embeddings=soru_embedding, n_results=2)
    baglam = "\n\n".join(sonuclar["documents"][0])

    # Not: "bilmiyorsan söyle" talimatı doğal dille verildiğinde model her seferinde farklı
    # bir cümle kuruyor (agent.py tarafında bunu algılamayı güvenilmez hale getiriyordu).
    # Bunun yerine tek, sabit bir işaret metni istiyoruz — böylece "bilgi yok" durumu
    # downstream kodda serbest metin ayrıştırmadan, doğrudan karşılaştırmayla yakalanabiliyor.
    prompt = f"""Aşağıdaki doküman parçalarını kullanarak soruyu cevapla.
Sadece verilen bilgiye dayan. Cevap dokümanlarda yoksa, başka hiçbir şey yazmadan
SADECE şunu yaz: BILGI_YOK

Dokümanlar:
{baglam}

Soru: {soru}

Cevap:"""

    # temperature=0: cevabın her seferinde dokümana sadık, tutarlı olması için
    # (varsayılan sıcaklıkta model bazen bağlamı bırakıp kendi bilgisini uyduruyordu)
    yanit = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    return yanit["message"]["content"]

if __name__ == "__main__":
    soru = "Havalimanı slot kısıtı nasıl belirleniyor?"
    print(f"Soru: {soru}\n")
    print(f"Cevap: {soru_cevapla(soru)}")
