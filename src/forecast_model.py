import os

# train_forecast_model.py'deki aynı opt-out: MLflow 3.x dosya tabanlı (./mlruns)
# backend'i varsayılan olarak hataya çeviriyor, bu proje sıfır-kurulum için yerel
# dosya backend'inde kalıyor.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

import json
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd

PROJE_KOKU = Path(__file__).resolve().parent.parent

# monitor_model.py'nin veri drift analizinde kullandığı istek/tahmin geçmişi.
# agent.py'deki agent_log.jsonl ile aynı JSONL deseni; .gitignore'da (data/logs/).
LOG_DOSYASI = PROJE_KOKU / "data" / "logs" / "forecast_log.jsonl"

_route_df = pd.read_csv(PROJE_KOKU / "data" / "route_features.csv")
# origin_popularity/destination_popularity, data_prep.py'de "leave-one-out" olarak
# hesaplanıyor: o havalimanının TÜM rotalarındaki toplam uçuş sayısı, EKSİ bu rotanın
# kendi payı. Veri setinde olmayan (yeni) bir rota için bu rotanın payı zaten 0
# olduğundan, aşağıdaki toplamlardan çıkarma yapmıyoruz — tam toplamı kullanıyoruz.
_origin_toplam = _route_df.groupby("origin")["flight_count"].sum()
_destination_toplam = _route_df.groupby("destination")["flight_count"].sum()

# "champion" alias'ı train_forecast_model.py tarafından, en düşük MAE'ye sahip modele
# otomatik atanıyor (bkz. o dosyadaki not) — burada hep o versiyonu yüklüyoruz.
_model = mlflow.pyfunc.load_model("models:/aerocargo_forecast_model@champion")


def _log_kaydet(origin, destination, days_per_week, origin_pop, destination_pop, tahmin, rota_mevcut):
    LOG_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
    kayit = {
        "zaman": datetime.now(timezone.utc).isoformat(),
        "origin": origin,
        "destination": destination,
        "days_per_week": float(days_per_week),
        "origin_popularity": float(origin_pop),
        "destination_popularity": float(destination_pop),
        "tahmini_ucus_sayisi": tahmin,
        "rota_veri_setinde_mevcut": rota_mevcut,
    }
    with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def talep_tahmin_et(origin: str, destination: str, days_per_week: float | None = None) -> dict:
    """Verilen rota için uçuş sayısı (talep vekili — bkz. data_prep.py'deki flight_count
    tanımı, belirli bir haftalık periyoda değil, veri setindeki toplam gözlemlere dayanır)
    tahmini üretir.

    Rota veri setinde zaten varsa (route_features.csv), days_per_week verilmediği
    sürece oradaki gerçek özellikler kullanılır. Rota veri setinde yoksa days_per_week
    zorunludur ve havalimanı popülerlikleri origin/destination toplamlarından türetilir.
    """
    mevcut_rota = _route_df[
        (_route_df["origin"] == origin) & (_route_df["destination"] == destination)
    ]

    if not mevcut_rota.empty:
        satir = mevcut_rota.iloc[0]
        if days_per_week is None:
            days_per_week = satir["days_per_week"]
        origin_pop = satir["origin_popularity"]
        destination_pop = satir["destination_popularity"]
    else:
        if days_per_week is None:
            raise ValueError(
                "Bu rota veri setinde yok, days_per_week zorunlu (örn. 3 ya da 7)."
            )
        origin_pop = _origin_toplam.get(origin, 0)
        destination_pop = _destination_toplam.get(destination, 0)

    X = pd.DataFrame([{
        "origin": origin,
        "destination": destination,
        "days_per_week": days_per_week,
        "origin_popularity": origin_pop,
        "destination_popularity": destination_pop,
    }])

    # Model, log1p(flight_count) hedefiyle eğitildi (train_forecast_model.py) —
    # tahmini gerçek uçuş sayısına çevirmek için expm1 ile tersini alıyoruz.
    log_tahmin = _model.predict(X)[0]
    tahmini_ucus_sayisi = max(0, round(float(np.expm1(log_tahmin))))

    _log_kaydet(
        origin, destination, days_per_week, origin_pop, destination_pop,
        tahmini_ucus_sayisi, not mevcut_rota.empty,
    )

    return {
        "tahmini_ucus_sayisi": tahmini_ucus_sayisi,
        "rota_veri_setinde_mevcut": not mevcut_rota.empty,
        "kullanilan_ozellikler": {
            "days_per_week": float(days_per_week),
            "origin_popularity": float(origin_pop),
            "destination_popularity": float(destination_pop),
        },
    }


if __name__ == "__main__":
    print(talep_tahmin_et("Delhi", "Mumbai"))
    print(talep_tahmin_et("Delhi", "Srinagar", days_per_week=5))
