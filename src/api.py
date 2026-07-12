from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# forecast_model, agent'tan ÖNCE import edilmeli: forecast_model mlflow.pyfunc üzerinden
# skops'u yüklüyor, skops kendi güvenli-tip taramasını modül yüklenirken (import zamanında)
# yapıyor. agent (rag_query -> sentence_transformers üzerinden) transformers paketini
# önce import ederse, skops'un taraması transformers'ın lazy-loading mekanizmasına takılıp
# "No module named 'torchvision'" hatasıyla çöküyor (torchvision projede kullanılmıyor,
# yüklü değil). Import sırasını tersine çevirmek, gereksiz bir bağımlılık eklemeden bu
# çakışmayı bypass ediyor.
from forecast_model import talep_tahmin_et
from agent import soru_sor

app = FastAPI(
    title="AeroCargo Copilot API",
    description="Kapasite optimizasyonu ve operasyonel politikalar (RAG) hakkında soru-cevap agent'ı.",
    version="1.0.0",
)


class SoruIstegi(BaseModel):
    soru: str


class CevapYaniti(BaseModel):
    cevap: str


class TahminIstegi(BaseModel):
    origin: str
    destination: str
    days_per_week: float | None = None


@app.get("/saglik")
def saglik_kontrolu():
    return {"durum": "ayakta"}


@app.post("/soru", response_model=CevapYaniti)
def soru_sor_endpoint(istek: SoruIstegi):
    cevap = soru_sor(istek.soru)
    return CevapYaniti(cevap=cevap)


@app.post("/forecast")
def forecast_endpoint(istek: TahminIstegi):
    try:
        return talep_tahmin_et(istek.origin, istek.destination, istek.days_per_week)
    except ValueError as hata:
        # Veri setinde olmayan yeni bir rota için days_per_week verilmediğinde
        # talep_tahmin_et ValueError fırlatıyor — bunu 400 olarak API'ye taşıyoruz.
        raise HTTPException(status_code=400, detail=str(hata))
