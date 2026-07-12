import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from agent_tools import bilgi_sorgula, kapasite_optimizasyonu_calistir
from llm_config import get_agent_llm

TOOLS = [bilgi_sorgula, kapasite_optimizasyonu_calistir]
TOOL_ADLARI = {t.name for t in TOOLS}

# temperature=0: agent'ın tool seçimi ve cevapları tutarlı (deterministik) olsun diye
# Model seçimi artık llm_config.py'de: LLM_SAGLAYICI ortam değişkeniyle Ollama
# (varsayılan, llama3.1:8b — llama3.2'nin tool-calling'i özellikle Türkçe argümanlarda
# tutarsızdı, bkz. Seviye 3 Görev 2 notları) ile Groq arasında geçiş yapılabiliyor.
llm = get_agent_llm()

# Küçük yerel modeller "gerekirse tool çağır" talimatını kendi haline bırakılınca
# tutarsız davranabiliyor: bazen hiç tool çağırmadan kendi (yanlış) bilgisinden cevap
# uyduruyor, bazen sonsuz döngüye giriyor. Bunu engellemek için ilk turda tool_choice="any"
# ile modeli MUTLAKA bir tool seçmeye zorluyoruz (hangisini seçeceği hâlâ modelin kararı);
# tool sonucunu aldıktan sonraki turda ise serbest bırakıyoruz.
llm_zorunlu_tool = llm.bind_tools(TOOLS, tool_choice="any")
# İkinci turda tool'ları hiç bağlamıyoruz: bu projede soru başına tek tool çağrısı yeterli,
# tools'suz bir LLM yapısal olarak tool_calls üretemez, bu da modelin tool sonucunu alıp
# tekrar tekrar aynı tool'u çağırmaya çalışmasından (sonsuz döngü) kesin olarak korur.
llm_ham = llm


TOOL_ADI_DESENI = re.compile(r'"name"\s*:\s*"(\w+)"')


def kirik_tool_cagrisini_onar(mesaj, orijinal_soru):
    """llama3.2, Türkçe karakterli argümanları JSON'a yazarken bazen geçersiz unicode
    kaçış dizisi üretiyor (örn. \\u015f\\ixt\\u0131) — bu yüzden tool çağrısı yapılandırılmış
    tool_calls alanına değil, bozuk düz metin olarak content'e düşüyor ve json.loads bile
    parse edemiyor. Tam JSON parse'a güvenmek yerine sadece hangi tool'un çağrılmak
    istendiğini regex ile tespit ediyoruz; argüman olarak da modelin (bozuk) yeniden
    yazdığı metni değil, kullanıcının orijinal sorusunu kullanıyoruz — zaten aramak
    istediğimiz asıl metin bu."""
    if mesaj.tool_calls or not mesaj.content.strip().startswith("{"):
        return mesaj
    eslesme = TOOL_ADI_DESENI.search(mesaj.content)
    if not eslesme or eslesme.group(1) not in TOOL_ADLARI:
        return mesaj
    ad = eslesme.group(1)
    args = {"soru": orijinal_soru} if ad == "bilgi_sorgula" else {}
    return AIMessage(
        content="",
        tool_calls=[{"name": ad, "args": args, "id": "onarilmis-1", "type": "tool_call"}],
    )


BILGI_YOK_ISARETI = "BILGI_YOK"
BILGI_YOK_CEVABI = "Bu konuda dokümanlarımızda bilgi bulunmuyor."


def agent_node(state: MessagesState):
    mesajlar = state["messages"]
    henuz_tool_calismadi = not any(isinstance(m, ToolMessage) for m in mesajlar)

    if not henuz_tool_calismadi:
        son_tool_mesaji = next(m for m in reversed(mesajlar) if isinstance(m, ToolMessage))
        if BILGI_YOK_ISARETI in son_tool_mesaji.content:
            # rag_query.py bu işareti döndürdüğünde LLM'e hiç sormuyoruz — model bu
            # durumda bile bazen kendi bilgisinden bir cevap uyduruyordu (halüsinasyon).
            # Doğal dil talimatına güvenmek yerine bunu kodda garanti altına alıyoruz.
            return {"messages": [AIMessage(content=BILGI_YOK_CEVABI)]}
        if son_tool_mesaji.name == "bilgi_sorgula":
            # bilgi_sorgula zaten dokümana dayalı, tam ve doğru bir cevap döndürüyor.
            # Bunu LLM'e tekrar "sentezletmek" (eval_seti.jsonl ile ölçtük) rakamları
            # (%50, %60 gibi) paraphrase sırasında düşürüyordu — hem yanlış bilgi riski
            # hem gereksiz gecikme/token. Bu yüzden tool sonucunu doğrudan iletiyoruz.
            return {"messages": [AIMessage(content=son_tool_mesaji.content)]}

    secilen_llm = llm_zorunlu_tool if henuz_tool_calismadi else llm_ham
    yanit = secilen_llm.invoke(mesajlar)
    if henuz_tool_calismadi:
        orijinal_soru = next(m.content for m in mesajlar if isinstance(m, HumanMessage))
        yanit = kirik_tool_cagrisini_onar(yanit, orijinal_soru)
    return {"messages": [yanit]}


def sonraki_adim(state: MessagesState):
    son_mesaj = state["messages"][-1]
    if getattr(son_mesaj, "tool_calls", None):
        return "tools"
    return END


graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(TOOLS))
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", sonraki_adim, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

app = graph.compile()


SISTEM_MESAJI = (
    "Sen AeroCargo operasyon asistanısın. Elindeki tool'ları kullanarak soruları cevapla. "
    "Bir tool çağırıp sonucunu aldıktan sonra, aynı soru için tekrar tool çağırma — "
    "o sonucu kullanarak kullanıcıya doğrudan düz metin bir cevap yaz."
)


LOG_DOSYASI = Path(__file__).resolve().parent.parent / "data" / "logs" / "agent_log.jsonl"


def _log_kaydet(soru, cevap, gecikme_saniye, tool_kullanildi, toplam_token):
    LOG_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
    kayit = {
        "zaman": datetime.now(timezone.utc).isoformat(),
        "soru": soru,
        "cevap": cevap,
        "gecikme_saniye": round(gecikme_saniye, 2),
        "tool_kullanildi": tool_kullanildi,
        "toplam_token": toplam_token,
    }
    with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def soru_sor_detayli(soru):
    """soru_sor'un, LLMOps için gecikme/token/tool bilgisini de döndüren hali.
    Hem loglama hem eval script'i (run_eval.py) bunu kullanıyor."""
    mesajlar = [
        {"role": "system", "content": SISTEM_MESAJI},
        {"role": "user", "content": soru},
    ]
    baslangic = time.monotonic()
    sonuc = app.invoke({"messages": mesajlar}, config={"recursion_limit": 8})
    gecikme_saniye = time.monotonic() - baslangic

    tum_mesajlar = sonuc["messages"]
    cevap = tum_mesajlar[-1].content
    tool_kullanildi = next(
        (m.name for m in tum_mesajlar if isinstance(m, ToolMessage)), None
    )
    toplam_token = sum(
        m.usage_metadata["total_tokens"]
        for m in tum_mesajlar
        if isinstance(m, AIMessage) and getattr(m, "usage_metadata", None)
    )

    _log_kaydet(soru, cevap, gecikme_saniye, tool_kullanildi, toplam_token)

    return {
        "cevap": cevap,
        "tool_kullanildi": tool_kullanildi,
        "gecikme_saniye": gecikme_saniye,
        "toplam_token": toplam_token,
    }


def soru_sor(soru):
    return soru_sor_detayli(soru)["cevap"]


if __name__ == "__main__":
    for soru in [
        "Havalimanı slot kısıtı nasıl belirleniyor?",
        "En yoğun 5 rota için kapasiteyi optimize eder misin?",
    ]:
        print(f"Soru: {soru}")
        print(f"Cevap: {soru_sor(soru)}")
        print("-" * 40)
