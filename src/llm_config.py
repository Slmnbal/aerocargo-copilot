import os

from dotenv import load_dotenv

# .env dosyası proje kökünde (Git'e girmiyor, bkz. .gitignore) — GROQ_API_KEY gibi
# sırları koda gömmeden okumak için. Ollama kullanırken .env hiç gerekmiyor.
load_dotenv()

# LLM_SAGLAYICI ortam değişkeniyle "ollama" (varsayılan, yerel/ücretsiz, key gerektirmez)
# ile "groq" (bulut, ücretsiz katman, hız/kalite için) arasında geçiş yapılabiliyor.
# Ollama varsayılan kaldı ki mevcut davranış (API key olmadan çalışma) bozulmasın.
SAGLAYICI = os.getenv("LLM_SAGLAYICI", "ollama").lower()


def get_agent_llm():
    """Agent'ın tool-routing/karar verme adımında kullandığı model.
    Tool-calling güvenilirliği önemli (bkz. agent.py'deki llama3.1:8b notları),
    Groq tarafında da bu yüzden büyük/tool-calling'de güçlü bir model seçildi."""
    if SAGLAYICI == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    from langchain_ollama import ChatOllama

    return ChatOllama(model="llama3.1:8b", temperature=0)


def get_rag_llm():
    """RAG cevap sentezi için kullanılan model. Tool-calling gerekmiyor, sadece
    verilen bağlamdan düz metin cevap üretiyor — bu yüzden daha küçük/hızlı bir
    model yeterli (Ollama tarafında zaten llama3.2 kullanılıyordu)."""
    if SAGLAYICI == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    from langchain_ollama import ChatOllama

    return ChatOllama(model="llama3.2", temperature=0)
