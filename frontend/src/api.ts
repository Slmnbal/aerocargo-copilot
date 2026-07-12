const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiHatasi extends Error {}

export async function soruSor(soru: string): Promise<string> {
  const yanit = await fetch(`${API_BASE}/soru`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ soru }),
  });
  if (!yanit.ok) {
    throw new ApiHatasi(`Sunucu hatası (${yanit.status})`);
  }
  const veri = await yanit.json();
  return veri.cevap as string;
}

export interface TahminSonucu {
  tahmini_ucus_sayisi: number;
  rota_veri_setinde_mevcut: boolean;
  kullanilan_ozellikler: {
    days_per_week: number;
    origin_popularity: number;
    destination_popularity: number;
  };
}

export async function talepTahminEt(
  origin: string,
  destination: string,
  daysPerWeek: number | null,
): Promise<TahminSonucu> {
  const yanit = await fetch(`${API_BASE}/forecast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      origin,
      destination,
      days_per_week: daysPerWeek,
    }),
  });
  if (!yanit.ok) {
    const govde = await yanit.json().catch(() => null);
    throw new ApiHatasi(govde?.detail ?? `Sunucu hatası (${yanit.status})`);
  }
  return yanit.json();
}
