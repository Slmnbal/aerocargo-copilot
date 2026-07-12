import pandas as pd
import pytest

from optimize_routes import optimize_routes

# routes.csv'nin gerçek şeması (data_prep.py) taklit ediliyor: origin, destination,
# flight_count, route. data/routes.csv Git'e girmediği için (bkz. .gitignore) testler
# gerçek veri yerine bu küçük, elle hesaplanabilir sentetik tabloyu kullanıyor.
ROUTES_DF = pd.DataFrame([
    {"origin": "A", "destination": "B", "flight_count": 100, "route": "A -> B"},
    {"origin": "A", "destination": "C", "flight_count": 50, "route": "A -> C"},
    {"origin": "D", "destination": "E", "flight_count": 80, "route": "D -> E"},
    {"origin": "D", "destination": "F", "flight_count": 20, "route": "D -> F"},
])

TOLERANS = 1e-4


@pytest.fixture
def sonuc():
    return optimize_routes(top_n=10, routes_df=ROUTES_DF)


def test_optimal_cozum_bulunuyor(sonuc):
    assert sonuc["status"] == 1  # PuLP: 1 = Optimal


def test_toplam_kapasite_talebin_yuzde_60i(sonuc):
    assert sonuc["total_capacity"] == int(ROUTES_DF["flight_count"].sum() * 0.6)


def test_atanan_ucuslar_toplam_kapasiteyi_asmiyor(sonuc):
    toplam_atanan = sonuc["results"]["assigned_flights"].sum()
    assert toplam_atanan <= sonuc["total_capacity"] + TOLERANS


def test_minimum_hizmet_seviyesi_saglaniyor(sonuc):
    for _, row in sonuc["results"].iterrows():
        assert row["assigned_flights"] >= 0.10 * row["flight_count"] - TOLERANS


def test_yogunlasma_siniri_saglaniyor(sonuc):
    for _, row in sonuc["results"].iterrows():
        assert row["assigned_flights"] <= 0.25 * sonuc["total_capacity"] + TOLERANS


def test_havalimani_slot_kisiti_saglaniyor(sonuc):
    for havalimani in ROUTES_DF["origin"].unique():
        rotalar = sonuc["results"][sonuc["results"]["origin"] == havalimani]
        slot_kapasitesi = int(ROUTES_DF[ROUTES_DF["origin"] == havalimani]["flight_count"].sum() * 0.5)
        assert rotalar["assigned_flights"].sum() <= slot_kapasitesi + TOLERANS


def test_atanan_ucus_kendi_talebini_asmiyor(sonuc):
    for _, row in sonuc["results"].iterrows():
        assert row["assigned_flights"] <= row["flight_count"] + TOLERANS


def test_top_n_rota_sayisini_sinirliyor():
    sonuc = optimize_routes(top_n=2, routes_df=ROUTES_DF)
    assert len(sonuc["results"]) == 2
    # En yoğun 2 rota (A->B: 100, D->E: 80) seçilmeli
    assert set(sonuc["results"]["route"]) == {"A -> B", "D -> E"}
