# AeroCargo Copilot — Proje Bağlamı

Bu dosya, Claude Code'un bu proje üzerinde çalışırken bilmesi gereken bağlamı içerir.

## Proje Nedir

**AeroCargo Copilot**: havayolu/kargo kapasite-rota planlama için optimizasyon + AI destekli bir karar sistemi. Optimizasyon çekirdeği (PuLP) ile AI Engineering (RAG, agent, MCP, API) katmanlarını birleştiren, ücretsiz/açık kaynak araçlarla kurulan bir portföy projesi. GitHub: `github.com/Slmnbal/aerocargo-copilot` (branch: `main`).

## Kim İçin Çalışıyoruz

Proje sahibi, Endüstri Mühendisliği + Data Analyst geçmişinden AI & Data + Optimization hibrit kariyerine geçiş yapan biri, projeyi **öğrenerek** inşa ediyor. Bu yüzden:

- Her önemli değişiklikte **ne yaptığını ve neden yaptığını Türkçe açıkla** — sadece kod üretme, kavramı da öğret (örn. "neden bu kütüphaneyi seçtik", "bu tasarım kararının alternatifi neydi").
- Görevleri **tek tek** yap, her görevden sonra dur, çalıştığını doğrulat, sonra bir sonrakine geç — hepsini tek seferde büyük bir patch olarak atma.
- Var olan kod stiline uy: değişken/fonksiyon isimleri karışık (bazı yerler İngilizce, kod içi açıklamalar ve print mesajları Türkçe) — bu tutarlılığı koru.
- Her görev bitince Git'e anlamlı, Türkçe bir commit mesajıyla kaydet.

## Mevcut Durum (Seviye 1-2 Tamamlandı)

**Klasör yapısı:** `src/` (kod), `data/` (üretilen veri, `.gitignore`'da — Git'e girmez), `docs/` (RAG kaynak dokümanları, versiyonlanır), `notebooks/`, `tests/` (henüz boş).

**Seviye 1 — Temel + optimizasyon çekirdeği (tamamlandı):**
- `src/data_prep.py` — Hugging Face'ten `Kabil007/IndianDomesticAirlineDataset` çekilip temizlenir, rota bazlı özellik tablosu (`data/route_features.csv`) üretilir (şebeke popülerlik özellikleri dahil).
- `src/optimize_routes.py` — PuLP ile kapasite/rota atama modeli (4 kısıt: toplam kapasite, havalimanı slotu, minimum hizmet, yoğunlaşma sınırı).
- `src/train_forecast_model.py` — scikit-learn (RandomForest) + MLflow ile talep tahmin modeli. MLflow experiment adı: `aerocargo-talep-tahmini`. Kayıtlı model adı: `aerocargo_forecast_model` (en iyi versiyon: RandomForest_v2, MAE 43.3, R² 0.602).

**Seviye 2 — RAG + vector DB (tamamlandı):**
- `docs/*.md` — kapasite politikası, rota önceliklendirme, aksama yönetimi (örnek/temsili içerik, optimizasyon modelinin kısıtlarıyla tutarlı yazıldı).
- `src/build_vector_db.py` — `sentence-transformers` (`all-MiniLM-L6-v2`) ile embedding, Chroma'da saklama (`data/chroma_db/`, koleksiyon adı: `aerocargo_docs`).
- `src/rag_query.py` — `soru_cevapla(soru)` fonksiyonu: Chroma'dan bağlam çeker, Ollama'daki `llama3.2` modeline RAG prompt'uyla gönderir.

## Kalan Yol Haritası

### Seviye 3 — LangGraph Agent + Arayüz
1. `optimize_routes.py`'deki optimizasyon mantığını ve `rag_query.py`'deki `soru_cevapla` fonksiyonunu LangGraph tool'ları olarak tanımla.
2. Çok adımlı bir agent grafiği kur: kullanıcı sorusuna göre agent hangi tool'u (RAG mi, optimizasyon mu) çağıracağına kendi karar versin.
3. Streamlit ile basit bir sohbet arayüzü kur, agent'ı buna bağla.

### Seviye 4 — MCP + Backend + LLMOps
1. Optimizasyon ve RAG tool'larını bir MCP server olarak dışa aç (Claude Desktop'tan test edilebilir olsun).
2. Agent'ı FastAPI backend'ine taşı (REST API + otomatik OpenAPI docs).
3. Loglama (gecikme, token kullanımı) ve küçük bir eval seti (10-15 test sorusu) ekle.
4. Ollama ile Groq/Gemini (ücretsiz katman) arasında config ile model değiştirilebilir hale getir.
5. `aerocargo_forecast_model`'i ayrı bir `/forecast` endpoint'i olarak serve et.
6. Model monitoring: tahmin hatası ve veri drift takibi + basit yeniden eğitim tetikleyici.

### Seviye 5 — Production Görünümü
1. Streamlit arayüzünü React (Vite + Tailwind) ile değiştir.
2. Docker + Docker Compose ile containerize et.
3. GitHub Actions ile CI (lint + pytest) kur.
4. Render/Railway/Hugging Face Spaces gibi ücretsiz bir platformda canlıya al.
5. README'yi ve proje açıklamasını portföy/CV seviyesine getir.

## Notlar

- Tüm araçlar ücretsiz/açık kaynak sürümleriyle kullanılıyor — yeni bir araç eklerken de bu prensibi koru.
- `data/*.csv` ve `data/chroma_db/` `.gitignore`'da, hiçbir zaman commit'leme.
- Varsayımlar (kapasite oranları, gün sayımı mantığı gibi) kod içinde yorum olarak belirtiliyor — yeni varsayım eklersen aynı şekilde belgelemeyi unutma.
