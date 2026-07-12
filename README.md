# AeroCargo Copilot

Havayolu/kargo kapasite ve rota planlama için optimizasyon + AI destekli karar sistemi.

## Durum
Seviye 1-4 tamamlandı (optimizasyon çekirdeği, RAG, LangGraph agent, MCP/FastAPI backend, LLMOps). Seviye 5 (production görünümü) sürüyor — React arayüzü (`frontend/`) FastAPI backend'ine (`src/api.py`) bağlandı. Detaylı yol haritası için `CLAUDE.md`'ye bakabilirsin.

Not: Bu bölümün kendisi de portföy/CV seviyesine getirilmeyi bekliyor (Seviye 5 kapsamında).

## Docker ile Çalıştırma

Ön koşul: `data/route_features.csv` ve `data/chroma_db/` host'ta zaten üretilmiş olmalı (`python src/data_prep.py` ve `python src/build_vector_db.py` ile — bkz. `CLAUDE.md`). Ollama, container dışında host makinede çalışıyor olmalı (`ollama serve`, gerekli modeller pull edilmiş).

```bash
docker compose up -d --build

# İlk kurulumda (mlruns named volume boşken) talep tahmin modelini container İÇİNDE eğit —
# aksi halde backend "champion" modeli bulamaz (bkz. docker-compose.yml'deki not):
docker compose run --rm backend python src/train_forecast_model.py
docker compose restart backend
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs
- `LLM_SAGLAYICI=groq` kullanmak için proje kökünde bir `.env` dosyası oluştur (`.env.example`'a bak) — docker compose bunu otomatik okur.

## Not: docs/ Klasörü
Buradaki dokümanlar gerçek bir havayolunun SOP'ları değildir; RAG sistemini test etmek için oluşturulmuş örnek/temsili içeriktir. İçerik, projenin optimizasyon modelindeki kısıtlarla tutarlı olacak şekilde yazılmıştır.