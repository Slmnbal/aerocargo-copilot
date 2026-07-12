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

## Mevcut Durum (Seviye 1-4 Tamamlandı)

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

**Seviye 4 — MCP + Backend + LLMOps (Görev 1-2 tamamlandı):**
- `src/mcp_server.py` — `FastMCP` ile aynı iki tool'u (`bilgi_sorgula`, `kapasite_optimizasyonu_calistir`) MCP protokolü üzerinden dışa açıyor. `mcp.client.stdio` ile uçtan uca test edildi (tool listesi + her iki tool çağrısı).
- `optimize_routes.py` ve `rag_query.py`'deki `data/...` yolları artık `Path(__file__).resolve().parent.parent` ile proje köküne göre mutlak — MCP istemcisi (Claude Desktop gibi) script'i hangi cwd'den başlatırsa başlatsın doğru çalışır. Bunu `/tmp` dizininden çalıştırarak doğruladık.
- `optimize_routes.py`: `prob.solve()` → `prob.solve(PULP_CBC_CMD(msg=False))` — CBC solver'ın stdout'a yazdığı log satırları MCP'nin JSON-RPC stdio akışını bozuyordu, `msg=False` ile susturuldu.
- Claude Desktop config'e (`~/Library/Application Support/Claude/claude_desktop_config.json`) `mcpServers.aerocargo-copilot` eklendi (`.venv/bin/python` + `mcp_server.py` mutlak yollarla). Claude Desktop yeniden başlatılınca aktif olur.
- `src/api.py` — FastAPI backend: `GET /saglik` (health check), `POST /soru` (`{"soru": "..."}` → `{"cevap": "..."}`, `agent.py`'deki `soru_sor`'u çağırıyor). Otomatik OpenAPI docs `/docs`'ta. `uvicorn api:app --app-dir src` ile başlatılır (cwd proje kökünde kalır, `--app-dir` sadece import path'i ekliyor). curl ile uçtan uca doğrulandı (health, RAG sorusu, optimizasyon sorusu, `/docs`).
- **Loglama:** `agent.py`'deki `soru_sor_detayli(soru)` (gecikme, token, hangi tool çağrıldığı bilgisini de döndürüyor) her çağrıda `data/logs/agent_log.jsonl`'a JSON satırı olarak yazıyor (`.gitignore`'da). `soru_sor(soru)` bunun sade (sadece cevap döndüren) sarmalayıcısı.
- **Eval seti:** `tests/eval_seti.jsonl` (12 soru: RAG bilinen/bilinmeyen + optimizasyon karışımı, her biri için `beklenen_tool` ve `beklenen_anahtar_kelimeler`), `src/run_eval.py` ile çalıştırılıyor.
  - İlk çalıştırma %58 (7/12) çıktı — sebep: `bilgi_sorgula` tool'u doğru rakamı (`%50`, `%60` vb.) döndürüyordu ama agent'ın ikinci turdaki LLM sentezi bunu paraphrase ederken rakamları düşürüyordu (tool routing'in kendisi 12/12 doğruydu).
  - Düzeltme: `agent_node`'da, çağrılan tool `bilgi_sorgula` ise (BILGI_YOK durumundaki gibi) LLM'e tekrar sormadan tool sonucu doğrudan döndürülüyor artık — RAG'ın kendi cevabı zaten tam ve doğru, tekrar sentezlemenin katma değeri yok, sadece detay kaybı ve gecikme/token maliyeti getiriyordu.
  - Düzeltme sonrası: **%92 (11/12)**, ortalama gecikme 15.4sn → 12.85sn, toplam token 8012 → 6692.
  - Kalan tek başarısızlık (yoğunlaşma sınırı %25 sorusu) bir retrieval sorunu: Chroma bu soru için %25'in geçtiği doküman parçası yerine başka bir parçayı getiriyor — sentez veya halüsinasyon sorunu değil, düşük öncelikli bilinen bir sınırlama.
- `src/llm_config.py` — `LLM_SAGLAYICI` ortam değişkenine (`.env`, `.gitignore`'da; şablonu `.env.example`) göre `get_agent_llm()` (agent'ın tool-routing modeli) ve `get_rag_llm()` (RAG sentez modeli) fonksiyonları Ollama (varsayılan, key gerektirmez) veya Groq (`GROQ_API_KEY`, ücretsiz katman: `llama-3.3-70b-versatile` tool-routing için, `llama-3.1-8b-instant` RAG sentez için) döndürüyor.
  - `agent.py` ve `rag_query.py` artık bu ortak config'ten model alıyor; `rag_query.py` bu vesileyle ham `ollama` paketinden langchain arayüzüne geçti (iki modülün de aynı config'e bağlanabilmesi için).
  - Sadece Ollama ile test edildi (kullanıcının henüz Groq API key'i yok) — eval seti aynı sonucu verdi (11/12, %92), regresyon yok. Groq tarafı `console.groq.com`'dan ücretsiz key alınıp `.env`'e `GROQ_API_KEY` ve `LLM_SAGLAYICI=groq` eklenince test edilmeyi bekliyor.
  - Gemini bilinçli olarak eklenmedi (kullanıcı Ollama+Groq'u seçti); ileride istenirse aynı `llm_config.py` deseniyle eklenebilir.
- `src/forecast_model.py` — `talep_tahmin_et(origin, destination, days_per_week=None)`: MLflow'daki `aerocargo_forecast_model`'in **"champion" alias'lı** versiyonunu yükleyip talep (flight_count) tahmini üretiyor. `api.py`'de `POST /forecast` olarak dışa açık.
  - `train_forecast_model.py` artık her çalıştırıldığında iki modeli de eğitip en düşük MAE'ye sahip olanı otomatik `champion` alias'ına atıyor (MLflow'da deprecated olan Staging/Production stage'leri yerine önerilen yöntem) — `/forecast` hep bu alias'ı okuyor, "hangi versiyon en iyisiydi" elle takip edilmiyor.
  - Rota veri setinde (`route_features.csv`) zaten varsa gerçek `days_per_week`/popülerlik özellikleri kullanılıyor; yoksa `days_per_week` zorunlu (400 hatası döner) ve popülerlik, o havalimanının veri setindeki toplam uçuş sayısından (leave-one-out çıkarma yapılmadan, çünkü yeni rotanın kendi payı zaten sıfır) türetiliyor. Model `log1p(flight_count)` hedefiyle eğitildiği için tahmin `expm1` ile geri çevriliyor — bu adım atlanırsa tahminler log-ölçekte (çok küçük) çıkar.
  - **Bulunan/düzeltilen iki yan sorun:** (1) MLflow 3.x dosya tabanlı (`mlruns/`) tracking backend'i artık varsayılan olarak hataya çeviriyor (sqlite'a geçişi öneriyor) — proje sıfır-kurulum prensibini korumak için `MLFLOW_ALLOW_FILE_STORE=true` ile susturuldu (`train_forecast_model.py` ve `forecast_model.py`'nin en üstünde). (2) `api.py`'de `forecast_model` mutlaka `agent`'tan **önce** import edilmeli — `mlflow.pyfunc`'ın kullandığı `skops`, `transformers` paketi zaten yüklüyken (agent → rag_query → sentence_transformers zincirinde olduğu gibi) import edilirse `transformers`'ın lazy-loading mekanizmasına takılıp eksik `torchvision`'dan çöküyor; import sırasını tersine çevirmek yeni bağımlılık eklemeden bunu bypass ediyor.
- `src/monitor_model.py` — basit model monitoring raporu (`python src/monitor_model.py`), iki sinyali birleştiriyor:
  - **Performans:** Canlıda gerçek/etiketli talep verisi olmadığından (feedback loop kurulu değil), MLflow'a her `train_forecast_model.py` çalıştırmasında kaydedilen test-seti MAE'sini geçmiş versiyonlarla kıyaslıyor — champion'ın MAE'si geçmişteki en iyiden **%15'ten fazla** kötüyse işaretliyor.
  - **Veri drift:** `forecast_model.py` artık her `/forecast` çağrısını `data/logs/forecast_log.jsonl`'a logluyor (agent_log.jsonl ile aynı JSONL deseni); bu isteklerin özellik dağılımı (days_per_week, origin/destination_popularity) eğitim verisiyle Kolmogorov-Smirnov testiyle (`scipy.stats.ks_2samp`) karşılaştırılıyor (en az 20 örnek gerekiyor, p<0.05 ise drift).
  - Bilinçli tasarım kararı: script sadece rapor basıp "yeniden eğitim öneriliyor" diyor, **otomatik yeniden eğitmiyor** — eğitim/MLflow kaydı gibi bir yan etkiyi otomatikleştirmek riskli bulundu, karar kullanıcıda kalıyor. İki senaryo da (sağlıklı model / drift tespiti) manuel simülasyonla doğrulandı.

**Seviye 5 — Production Görünümü (Görev 1 tamamlandı):**
- `frontend/` — React (Vite + TypeScript) + Tailwind CSS v4 (`@tailwindcss/vite` plugin, ayrı postcss config gerektirmiyor). Sohbet (`/soru`) ve Talep Tahmini (`/forecast`) için iki sekmeli basit bir arayüz; `src/api.ts` backend'e `fetch` ile bağlanıyor (`VITE_API_BASE_URL`, varsayılan `http://localhost:8000`).
- `src/api.py`'ye `CORSMiddleware` eklendi (`http://localhost:5173` — Vite dev portu); canlıya alınca gerçek frontend domain'i eklenmeli.
- `src/app.py` (Streamlit) kaldırıldı, `streamlit` bağımlılığı `requirements.txt`'ten temizlendi — React artık tek arayüz. Streamlit'e dönmek istenirse git geçmişinden geri alınabilir.
- Geliştirme: `uvicorn api:app --app-dir src --port 8000` (backend) + `cd frontend && npm run dev` (frontend, ayrı terminal).

## Kalan Yol Haritası

### Seviye 5 — Production Görünümü
2. Docker + Docker Compose ile containerize et.
3. GitHub Actions ile CI (lint + pytest) kur.
4. Render/Railway/Hugging Face Spaces gibi ücretsiz bir platformda canlıya al.
5. README'yi ve proje açıklamasını portföy/CV seviyesine getir.

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
- **Python sürümü: 3.12** (`.venv`). Seviye 4 Görev 1'de `mcp` paketi Python ≥3.10 istediği için 3.9'dan yükseltildi; `.venv` silinip 3.12 ile yeniden kuruldu, tüm paketler sabit sürüm yerine üst düzey isimleriyle (pandas, pulp, mlflow, chromadb, vb.) taze kuruldu ki pip kendi uyumlu sürümlerini çözebilsin (eski dondurulmuş `requirements.txt`'teki `pyarrow==20.0.0` gibi sabit sürümler yeni paketlerle çakışıyordu).
