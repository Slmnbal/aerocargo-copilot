import { useState } from "react";
import { ApiHatasi, talepTahminEt, type TahminSonucu } from "../api";

export function Forecast() {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [daysPerWeek, setDaysPerWeek] = useState("");
  const [sonuc, setSonuc] = useState<TahminSonucu | null>(null);
  const [hata, setHata] = useState<string | null>(null);
  const [yukleniyor, setYukleniyor] = useState(false);

  async function gonder(e: React.FormEvent) {
    e.preventDefault();
    if (!origin.trim() || !destination.trim() || yukleniyor) return;

    setYukleniyor(true);
    setHata(null);
    setSonuc(null);
    try {
      const veri = await talepTahminEt(
        origin.trim(),
        destination.trim(),
        daysPerWeek.trim() ? Number(daysPerWeek) : null,
      );
      setSonuc(veri);
    } catch (e) {
      setHata(e instanceof ApiHatasi ? e.message : "Beklenmeyen bir hata oluştu.");
    } finally {
      setYukleniyor(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <p className="text-sm text-neutral-500 dark:text-neutral-400">
        Bir rota için talep (uçuş sayısı) tahmini üret. Rota veri setinde yoksa haftalık gün
        sayısını (days_per_week) girmen gerekiyor.
      </p>
      <form onSubmit={gonder} className="flex flex-col gap-3">
        <div className="flex gap-3">
          <input
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="Origin (örn. Delhi)"
            className="flex-1 rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm outline-none focus:border-indigo-500 dark:border-neutral-700"
          />
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Destination (örn. Mumbai)"
            className="flex-1 rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm outline-none focus:border-indigo-500 dark:border-neutral-700"
          />
        </div>
        <input
          value={daysPerWeek}
          onChange={(e) => setDaysPerWeek(e.target.value)}
          type="number"
          min={1}
          max={7}
          placeholder="days_per_week (opsiyonel, rota mevcutsa gerekmez)"
          className="rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm outline-none focus:border-indigo-500 dark:border-neutral-700"
        />
        <button
          type="submit"
          disabled={yukleniyor || !origin.trim() || !destination.trim()}
          className="self-start rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          {yukleniyor ? "Hesaplanıyor…" : "Tahmin Et"}
        </button>
      </form>

      {hata && (
        <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {hata}
        </div>
      )}

      {sonuc && (
        <div className="rounded-md border border-neutral-200 p-4 text-sm dark:border-neutral-800">
          <p className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
            {sonuc.tahmini_ucus_sayisi}
            <span className="ml-2 text-sm font-normal text-neutral-500 dark:text-neutral-400">
              tahmini uçuş sayısı
            </span>
          </p>
          <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-neutral-500 dark:text-neutral-400">
            <dt>Rota veri setinde mevcut</dt>
            <dd>{sonuc.rota_veri_setinde_mevcut ? "Evet" : "Hayır (yeni rota)"}</dd>
            <dt>days_per_week</dt>
            <dd>{sonuc.kullanilan_ozellikler.days_per_week.toFixed(1)}</dd>
            <dt>origin_popularity</dt>
            <dd>{sonuc.kullanilan_ozellikler.origin_popularity}</dd>
            <dt>destination_popularity</dt>
            <dd>{sonuc.kullanilan_ozellikler.destination_popularity}</dd>
          </dl>
        </div>
      )}
    </div>
  );
}
