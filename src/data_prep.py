from datasets import load_dataset
import pandas as pd

dataset = load_dataset("Kabil007/IndianDomesticAirlineDataset")
df = dataset["train"].to_pandas()

# Sadece işimize yarayan sütunları seç
df = df[["airline", "flightNumber", "origin", "destination", "daysOfWeek"]]

# Rota bilgisi olmayan satırlar işe yaramaz - optimize edecek bir rota yoksa o satır anlamsız
df = df.dropna(subset=["origin", "destination"])

# Havayolu bilgisi eksikse "Unknown" yaz, satırı silme (rota bilgisi hala değerli)
df["airline"] = df["airline"].fillna("Unknown")

# Rota sütunu oluştur (origin -> destination birleşimi)
df["route"] = df["origin"] + " -> " + df["destination"]

# Her rotada kaç uçuş var, sayalım - bunu "talep" varsayımı olarak kullanacağız
route_counts = df.groupby(["origin", "destination"]).size().reset_index(name="flight_count")
route_counts["route"] = route_counts["origin"] + " -> " + route_counts["destination"]
route_counts = route_counts.sort_values("flight_count", ascending=False)

print(f"Temizlik sonrası satır sayısı: {len(df)}")
print(f"Toplam farklı rota sayısı: {df['route'].nunique()}")
print(route_counts.head(10))

route_counts.to_csv("data/routes.csv", index=False)
print("Kaydedildi: data/routes.csv")