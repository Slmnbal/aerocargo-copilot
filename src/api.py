from fastapi import FastAPI
from pydantic import BaseModel

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


@app.get("/saglik")
def saglik_kontrolu():
    return {"durum": "ayakta"}


@app.post("/soru", response_model=CevapYaniti)
def soru_sor_endpoint(istek: SoruIstegi):
    cevap = soru_sor(istek.soru)
    return CevapYaniti(cevap=cevap)
