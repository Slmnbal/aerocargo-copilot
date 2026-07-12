import os

os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

import json
from pathlib import Path

import mlflow
import pandas as pd
from scipy.stats import ks_2samp

PROJE_KOKU = Path(__file__).resolve().parent.parent
FORECAST_LOG = PROJE_KOKU / "data" / "logs" / "forecast_log.jsonl"
MODEL_ADI = "aerocargo_forecast_model"

# MAE, geçmişteki en iyi (en düşük) değerden bu oranın üzerinde kötüleşirse
# performans gerilemesi (regression) olarak işaretliyoruz.
MAE_BOZULMA_ESIGI = 0.15
# KS-test p-değeri bu eşiğin altındaysa, o özelliğin dağılımı eğitim verisinden
# istatistiksel olarak anlamlı şekilde farklılaşmış demektir (drift).
DRIFT_P_ESIGI = 0.05
# Drift testinin anlamlı olması için en az bu kadar loglanmış /forecast isteği gerekiyor.
DRIFT_MIN_ORNEK = 20


def performans_gerilemesi_var_mi():
    """MLflow'a kayıtlı tüm versiyonların MAE geçmişini karşılaştırıp, şu anki
    "champion" modelin geçmişteki en iyi MAE'ye göre belirgin şekilde kötüleşip
    kötüleşmediğini kontrol eder. Gerçek/canlı etiket verisi olmadığından
    (feedback loop kurulu değil) elimizdeki en dürüst performans sinyali bu:
    her train_forecast_model.py çalıştırmasında test setinde ölçülen MAE."""
    client = mlflow.MlflowClient()
    versiyonlar = client.search_model_versions(f"name='{MODEL_ADI}'")
    if not versiyonlar:
        return False, "Kayıtlı model versiyonu bulunamadı.", []

    gecmis = []
    for v in versiyonlar:
        run = client.get_run(v.run_id)
        gecmis.append({
            "versiyon": int(v.version),
            "model_type": run.data.params.get("model_type", "?"),
            "mae": run.data.metrics.get("mae"),
            "r2": run.data.metrics.get("r2"),
            "zaman": run.info.start_time,
        })
    gecmis.sort(key=lambda x: x["versiyon"])

    try:
        champion = client.get_model_version_by_alias(MODEL_ADI, "champion")
        champion_versiyon = int(champion.version)
    except mlflow.exceptions.MlflowException:
        return False, "'champion' alias'ı henüz atanmamış.", gecmis

    champion_kaydi = next(g for g in gecmis if g["versiyon"] == champion_versiyon)
    for g in gecmis:
        g["champion"] = g["versiyon"] == champion_versiyon

    oncekiler = [g["mae"] for g in gecmis if g["versiyon"] < champion_versiyon and g["mae"] is not None]
    if not oncekiler:
        return False, f"Champion (v{champion_versiyon}) ilk kayıt, karşılaştırılacak geçmiş yok.", gecmis

    en_iyi_gecmis_mae = min(oncekiler)
    champion_mae = champion_kaydi["mae"]
    kotulesme_orani = (champion_mae - en_iyi_gecmis_mae) / en_iyi_gecmis_mae

    if kotulesme_orani > MAE_BOZULMA_ESIGI:
        mesaj = (
            f"Champion MAE ({champion_mae:.1f}), geçmişteki en iyi MAE'den "
            f"(v{champion_versiyon} öncesi: {en_iyi_gecmis_mae:.1f}) %{kotulesme_orani * 100:.0f} daha kötü."
        )
        return True, mesaj, gecmis

    mesaj = f"Champion MAE ({champion_mae:.1f}), geçmiş en iyiye ({en_iyi_gecmis_mae:.1f}) göre sağlıklı."
    return False, mesaj, gecmis


def veri_drift_var_mi():
    """Loglanmış /forecast isteklerinin özellik dağılımını (days_per_week,
    origin_popularity, destination_popularity), eğitim verisinin (route_features.csv)
    aynı özellik dağılımıyla Kolmogorov-Smirnov testiyle karşılaştırır. Canlıdaki
    sorgu profili eğitim verisinden belirgin şekilde sapmışsa (örn. hiç görülmemiş
    rotalar/havalimanları için çok sayıda tahmin isteniyorsa) bu, modelin artık
    gerçek kullanım deseniyle uyuşmayabileceğinin bir işareti."""
    if not FORECAST_LOG.exists():
        return False, "Henüz loglanmış /forecast isteği yok.", {}

    with open(FORECAST_LOG, encoding="utf-8") as f:
        kayitlar = [json.loads(satir) for satir in f if satir.strip()]
    if len(kayitlar) < DRIFT_MIN_ORNEK:
        return False, f"Yetersiz log ({len(kayitlar)}/{DRIFT_MIN_ORNEK}), drift değerlendirilemedi.", {}

    loglar = pd.DataFrame(kayitlar)
    egitim = pd.read_csv(PROJE_KOKU / "data" / "route_features.csv")

    ozellikler = ["days_per_week", "origin_popularity", "destination_popularity"]
    sonuclar = {}
    drift_var = False
    for ozellik in ozellikler:
        istatistik, p_degeri = ks_2samp(egitim[ozellik], loglar[ozellik])
        sonuclar[ozellik] = {"ks_istatistik": round(istatistik, 3), "p_degeri": round(p_degeri, 4)}
        if p_degeri < DRIFT_P_ESIGI:
            drift_var = True

    kacan = [o for o, s in sonuclar.items() if s["p_degeri"] < DRIFT_P_ESIGI]
    mesaj = f"Drift tespit edildi: {', '.join(kacan)}" if drift_var else "Özellik dağılımları eğitim verisiyle tutarlı."
    return drift_var, mesaj, sonuclar


def rapor_olustur():
    performans_kotu, performans_mesaji, mae_gecmisi = performans_gerilemesi_var_mi()
    drift_var, drift_mesaji, drift_detaylari = veri_drift_var_mi()

    print("=== Model Performans Geçmişi (MAE) ===")
    for g in mae_gecmisi:
        isaret = " <- champion" if g.get("champion") else ""
        mae_str = f"{g['mae']:.1f}" if g["mae"] is not None else "?"
        print(f"  v{g['versiyon']} ({g['model_type']}): MAE={mae_str}{isaret}")
    print(f"\n[Performans] {performans_mesaji}")

    print("\n=== Veri Drift (KS-test) ===")
    for ozellik, s in drift_detaylari.items():
        print(f"  {ozellik}: ks={s['ks_istatistik']}, p={s['p_degeri']}")
    print(f"\n[Drift] {drift_mesaji}")

    print("\n=== Sonuç ===")
    if performans_kotu or drift_var:
        nedenler = []
        if performans_kotu:
            nedenler.append("performans gerilemesi")
        if drift_var:
            nedenler.append("veri drift")
        print(f"YENİDEN EĞİTİM ÖNERİLİYOR ({', '.join(nedenler)}). Çalıştır: python src/train_forecast_model.py")
    else:
        print("Model sağlıklı görünüyor, ek işlem gerekmiyor.")

    return performans_kotu or drift_var


if __name__ == "__main__":
    rapor_olustur()
