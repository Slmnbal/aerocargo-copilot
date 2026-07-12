import { useState } from "react";
import { ApiHatasi, soruSor } from "../api";

interface Mesaj {
  rol: "kullanici" | "asistan";
  icerik: string;
}

export function Chat() {
  const [mesajlar, setMesajlar] = useState<Mesaj[]>([]);
  const [girdi, setGirdi] = useState("");
  const [yukleniyor, setYukleniyor] = useState(false);

  async function gonder(e: React.FormEvent) {
    e.preventDefault();
    const soru = girdi.trim();
    if (!soru || yukleniyor) return;

    setMesajlar((onceki) => [...onceki, { rol: "kullanici", icerik: soru }]);
    setGirdi("");
    setYukleniyor(true);
    try {
      const cevap = await soruSor(soru);
      setMesajlar((onceki) => [...onceki, { rol: "asistan", icerik: cevap }]);
    } catch (hata) {
      const mesaj = hata instanceof ApiHatasi ? hata.message : "Beklenmeyen bir hata oluştu.";
      setMesajlar((onceki) => [...onceki, { rol: "asistan", icerik: `Hata: ${mesaj}` }]);
    } finally {
      setYukleniyor(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {mesajlar.length === 0 && (
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            Kapasite politikaları, rota önceliklendirme veya "en yoğun 5 rotayı optimize et" gibi
            sorular sorabilirsin.
          </p>
        )}
        {mesajlar.map((m, i) => (
          <div key={i} className={`flex ${m.rol === "kullanici" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                m.rol === "kullanici"
                  ? "bg-indigo-600 text-white"
                  : "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-100"
              }`}
            >
              {m.icerik}
            </div>
          </div>
        ))}
        {yukleniyor && (
          <div className="flex justify-start">
            <div className="rounded-lg bg-neutral-100 px-3 py-2 text-sm text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400">
              Düşünüyor…
            </div>
          </div>
        )}
      </div>
      <form onSubmit={gonder} className="flex gap-2 border-t border-neutral-200 p-3 dark:border-neutral-800">
        <input
          value={girdi}
          onChange={(e) => setGirdi(e.target.value)}
          placeholder="Bir soru sor…"
          disabled={yukleniyor}
          className="flex-1 rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm outline-none focus:border-indigo-500 dark:border-neutral-700"
        />
        <button
          type="submit"
          disabled={yukleniyor || !girdi.trim()}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          Gönder
        </button>
      </form>
    </div>
  );
}
