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

def count_days(value):
    """'Sunday,Tuesday,Thursday' -> 3 gibi, haftada kaç gün uçtuğunu sayar."""
    if pd.isna(value):
        return None
    value = str(value)
    if "daily" in value.lower():
        return 7
    return len(value.split(","))

df["days_per_week"] = df["daysOfWeek"].apply(count_days)

# Rota bazında özellik tablosu: haftalık ortalama gün sayısı + toplam uçuş (talep)
route_features = df.groupby(["origin", "destination"]).agg(
    days_per_week=("days_per_week", "mean"),
    flight_count=("origin", "size"),
).reset_index()
route_features["route"] = route_features["origin"] + " -> " + route_features["destination"]

origin_totals = route_features.groupby("origin")["flight_count"].sum()
destination_totals = route_features.groupby("destination")["flight_count"].sum()

route_features["origin_popularity"] = (
    route_features["origin"].map(origin_totals) - route_features["flight_count"]
)
route_features["destination_popularity"] = (
    route_features["destination"].map(destination_totals) - route_features["flight_count"]
)

route_features.to_csv("data/route_features.csv", index=False)

print(route_features.head(10))
print(f"Toplam rota: {len(route_features)}")


print(f"Temizlik sonrası satır sayısı: {len(df)}")
print(f"Toplam farklı rota sayısı: {df['route'].nunique()}")
print(route_counts.head(10))

route_counts.to_csv("data/routes.csv", index=False)
print("Kaydedildi: data/routes.csv")

# days_per_week doğru hesaplanmış mı, kontrol edelim
print("days_per_week değer aralığı:", df["days_per_week"].min(), "-", df["days_per_week"].max())
print("Kaç satırda days_per_week boş kaldı:", df["days_per_week"].isna().sum())

# Birkaç örneği yan yana görelim - orijinal metin ile hesaplanan sayı tutarlı mı
print(df[["daysOfWeek", "days_per_week"]].dropna().sample(10, random_state=1))