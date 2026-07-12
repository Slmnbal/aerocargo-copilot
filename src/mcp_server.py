from mcp.server.fastmcp import FastMCP

from optimize_routes import optimize_routes
from rag_query import soru_cevapla

# FastMCP: tool'ları basit bir Python fonksiyonu gibi yazıp @mcp.tool() ile işaretlememizi
# sağlıyor; MCP protokolünün istemciyle (Claude Desktop gibi) konuşma, tool listesini
# duyurma, JSON şema üretme gibi kısımlarını arkada kendisi hallediyor.
mcp = FastMCP("aerocargo-copilot")


@mcp.tool()
def bilgi_sorgula(soru: str) -> str:
    """AeroCargo'nun operasyonel politikaları (kapasite planlaması, rota önceliklendirme,
    aksama yönetimi) hakkındaki soruları dokümanlara dayanarak cevaplar."""
    return soru_cevapla(soru)


@mcp.tool()
def kapasite_optimizasyonu_calistir(top_n: int = 20) -> str:
    """En yoğun top_n rota için kapasite/rota atama optimizasyonunu (PuLP) çalıştırır ve
    her rotaya kaç uçuş atandığını özetler."""
    cikti = optimize_routes(top_n=top_n)
    satirlar = [
        f"Durum: {'Optimal' if cikti['status'] == 1 else cikti['status']}",
        f"Toplam kapasite: {cikti['total_capacity']}",
        "",
        cikti["results"].to_string(index=False),
    ]
    return "\n".join(satirlar)


if __name__ == "__main__":
    mcp.run()
