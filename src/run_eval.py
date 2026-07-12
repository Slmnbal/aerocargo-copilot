import json
from pathlib import Path

from agent import soru_sor_detayli

EVAL_SETI_YOLU = Path(__file__).resolve().parent.parent / "tests" / "eval_seti.jsonl"


def degerlendir(vaka, sonuc):
    """Bir eval vakasının geçip geçmediğine karar verir.
    - beklenen_tool varsa: doğru tool çağrılmış mı (agent'ın optimizasyon sonucunu
      özetlerken sayısal detayları bazen atladığını biliyoruz, o yüzden asıl güvenilir
      sinyal hangi tool'un çağrıldığı, cevabın tam metni değil).
    - beklenen_anahtar_kelimeler varsa: cevapta bunlardan en az biri geçiyor mu
      (büyük/küçük harf duyarsız)."""
    tool_gecti = (
        vaka["beklenen_tool"] is None or sonuc["tool_kullanildi"] == vaka["beklenen_tool"]
    )
    kelimeler = vaka["beklenen_anahtar_kelimeler"]
    kelime_gecti = not kelimeler or any(k.lower() in sonuc["cevap"].lower() for k in kelimeler)
    return tool_gecti and kelime_gecti


def main():
    vakalar = [json.loads(satir) for satir in EVAL_SETI_YOLU.read_text(encoding="utf-8").splitlines()]

    gecen = 0
    toplam_gecikme = 0.0
    toplam_token = 0

    for i, vaka in enumerate(vakalar, start=1):
        sonuc = soru_sor_detayli(vaka["soru"])
        basarili = degerlendir(vaka, sonuc)
        gecen += basarili
        toplam_gecikme += sonuc["gecikme_saniye"]
        toplam_token += sonuc["toplam_token"]

        durum = "GEÇTİ" if basarili else "KALDI"
        print(f"[{i}/{len(vakalar)}] {durum} — {vaka['soru']}")
        print(f"    tool: {sonuc['tool_kullanildi']} (beklenen: {vaka['beklenen_tool']})")
        print(f"    cevap: {sonuc['cevap'][:150]}")
        if not basarili:
            print(f"    beklenen anahtar kelimeler: {vaka['beklenen_anahtar_kelimeler']}")
        print()

    print("=" * 50)
    print(f"Başarı oranı: {gecen}/{len(vakalar)} ({100 * gecen / len(vakalar):.0f}%)")
    print(f"Ortalama gecikme: {toplam_gecikme / len(vakalar):.2f} sn")
    print(f"Toplam token: {toplam_token}")


if __name__ == "__main__":
    main()
