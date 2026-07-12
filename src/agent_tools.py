from langchain_core.tools import tool

from optimize_routes import optimize_routes
from rag_query import soru_cevapla


@tool
def bilgi_sorgula(soru: str) -> str:
    """AeroCargo'nun operasyonel politikaları (kapasite planlaması, rota önceliklendirme,
    aksama yönetimi) hakkındaki soruları dokümanlara dayanarak cevaplar. Kullanıcı
    "neden", "nasıl belirleniyor", "politika nedir" gibi bilgi/açıklama sorduğunda kullan."""
    return soru_cevapla(soru)


@tool
def kapasite_optimizasyonu_calistir(top_n: int = 20) -> str:
    """En yoğun top_n rota için kapasite/rota atama optimizasyonunu (PuLP) çalıştırır ve
    her rotaya kaç uçuş atandığını özetler. Kullanıcı "optimize et", "kapasiteyi nasıl
    dağıtmalıyız", "rotalara ne kadar uçuş ayrılmalı" gibi bir hesaplama istediğinde kullan."""
    cikti = optimize_routes(top_n=top_n)
    satirlar = [
        f"Durum: {'Optimal' if cikti['status'] == 1 else cikti['status']}",
        f"Toplam kapasite: {cikti['total_capacity']}",
        "",
        cikti["results"].to_string(index=False),
    ]
    return "\n".join(satirlar)


if __name__ == "__main__":
    print("--- bilgi_sorgula testi ---")
    print(bilgi_sorgula.invoke("Havalimanı slot kısıtı nasıl belirleniyor?"))

    print("\n--- kapasite_optimizasyonu_calistir testi ---")
    print(kapasite_optimizasyonu_calistir.invoke({"top_n": 5}))
