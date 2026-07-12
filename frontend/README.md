# AeroCargo Copilot — Frontend

React (Vite + TypeScript) + Tailwind CSS ile yazılmış sohbet ve talep tahmini arayüzü. `src/api.py`'deki FastAPI backend'ine (`/soru`, `/forecast`) doğrudan tarayıcıdan istek atar.

## Geliştirme

```bash
npm install
npm run dev
```

Backend ayrı bir terminalde, proje kökünden çalışıyor olmalı:

```bash
uvicorn api:app --app-dir src --port 8000
```

Backend adresi varsayılan olarak `http://localhost:8000` — değiştirmek için `.env.example`'ı `.env` olarak kopyalayıp `VITE_API_BASE_URL`'i güncelle.

## Build

```bash
npm run build
```
