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

## Mevcut Durum (Seviye 1-3 Tamamlandı)

**Klasör yapısı:** `src/` (kod), `data/` (üretilen veri, `.gitignore`'da — Git'e girmez), `docs/` (RAG kaynak dokümanları, versiyonlanır), `notebooks/`, `tests/` (henüz boş).

**Seviye 1 — Temel + optimizasyon çekirdeği (tamamlandı):**
- `src/data_prep.py` — Hugging Face'ten `Kabil007/IndianDomesticAirlineDataset` çekilip temizlenir, rota bazlı özellik tablosu (`data/route_features.csv`) üretilir (şebeke popülerlik özellikleri dahil).
- `src/optimize_routes.py` — PuLP ile kapasite/rota atama modeli (4 kısıt: toplam kapasite, havalimanı slotu, minimum hizmet, yoğunlaşma sınırı).
- `src/train_forecast_model.py` — scikit-learn (RandomForest) + MLflow ile talep tahmin modeli. MLflow experiment adı: `aerocargo-talep-tahmini`. Kayıtlı model adı: `aerocargo_forecast_model` (en iyi versiyon: RandomForest_v2, MAE 43.3, R² 0.602).

**Seviye 2 — RAG + vector DB (tamamlandı):**
- `docs/*.md` — kapasite politikası, rota önceliklendirme, aksama yönetimi (örnek/temsili içerik, optimizasyon modelinin kısıtlarıyla tutarlı yazıldı).
- `src/build_vector_db.py` — `sentence-transformers` (`all-MiniLM-L6-v2`) ile embedding, Chroma'da saklama (`data/chroma_db/`, koleksiyon adı: `aerocargo_docs`).
- `src/rag_query.py` — `soru_cevapla(soru)` fonksiyonu: Chroma'dan bağlam çeker, Ollama'daki `llama3.2` modeline (`temperature=0`) RAG prompt'uyla gönderir. Dokümanlarda cevap yoksa model sabit bir işaret metni (`BILGI_YOK`) döndürür — doğal dilde "bilmiyorum" cümlesi kurdurmak yerine bunu tercih ettik, çünkü serbest metin her seferinde farklı çıkıyordu ve downstream kodda güvenilir şekilde yakalanamıyordu.

**Seviye 3 — LangGraph Agent + Arayüz (tamamlandı):**
- `src/optimize_routes.py` artık `optimize_routes(top_n=20)` fonksiyonu (print yerine dict return).
- `src/agent_tools.py` — iki LangGraph tool: `bilgi_sorgula` (RAG) ve `kapasite_optimizasyonu_calistir` (optimizasyon).
- `src/agent.py` — LangGraph StateGraph: agent düğümü tool seçip çağırıyor, tools düğümü çalıştırıyor, sonuç tekrar agent'a dönüp son cevabı üretiyor.
  - **Model: `llama3.1:8b`** (agent'ın tool-routing modeli) — `llama3.2` denendi ama Ollama üzerinden tool-calling'i (özellikle Türkçe karakterli argümanlarda) tutarsızdı: bazen JSON'u bozuk üretiyor, bazen aynı tool'u sonsuz çağırıyor, bazen hiç tool çağırmadan halüsinasyon yapıyordu. `llama3.1:8b` (Meta'nın fonksiyon çağırma için özel eğittiği model) bu sorunları çözdü. `rag_query.py`'nin kendi üretim adımı hâlâ `llama3.2` kullanıyor (o ayrı, tool-calling gerektirmiyor).
  - Güvenlik katmanları (küçük modellerle çalışırken gerekli oldu, büyük/bulut modele geçilse bile zararsız): ilk turda `tool_choice="any"` ile tool seçimi zorunlu kılınıyor; ikinci turda tool'lar hiç bağlanmıyor (yapısal olarak tekrar tool çağıramaz, sonsuz döngü engellenir); bozuk JSON tool çağrısı regex ile onarılıyor; `bilgi_sorgula` sonucu `BILGI_YOK` ise LLM'e hiç sorulmadan sabit bir cevap dönülüyor (halüsinasyon riski sıfırlanıyor).
  - Kalan bilinen sınırlama: agent'ın genel sentez cevapları (örn. optimizasyon sonucunu özetlerken) bazen sayısal detayları atlayıp genel geçer cümleler kuruyor — yanlış değil ama az detaylı. Seviye 4'te model değişimiyle (Groq/Gemini) yeniden değerlendirilebilir.
- `src/app.py` — Streamlit sohbet arayüzü, `agent.py`'deki `soru_sor`'u çağırıyor. `streamlit run src/app.py` ile başlatılır (proje kökünden çalıştırılmalı — göreli veri yolları buna göre). `streamlit.testing.v1.AppTest` ile uçtan uca doğrulandı (gerçek tarayıcı yerine).

## Kalan Yol Haritası

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
