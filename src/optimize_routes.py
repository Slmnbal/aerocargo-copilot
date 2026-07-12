import pandas as pd
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, value

routes = pd.read_csv("data/routes.csv")
routes = routes.sort_values("flight_count", ascending=False).head(20).reset_index(drop=True)

TOTAL_CAPACITY = int(routes["flight_count"].sum() * 0.6)

prob = LpProblem("Rota_Kapasite_Atama", LpMaximize)

route_vars = {
    row["route"]: LpVariable(f"flights_{i}", lowBound=0, upBound=row["flight_count"])
    for i, row in routes.iterrows()
}

# Amaç: talebe göre ağırlıklandırılmış toplam uçuşu maksimize et
prob += lpSum(row["flight_count"] * route_vars[row["route"]] for _, row in routes.iterrows())

# Kısıt 1: toplam filo kapasitesi
prob += lpSum(route_vars.values()) <= TOTAL_CAPACITY, "Toplam_Kapasite"

# Kısıt 2: havalimanı slot kısıtı (her havalimanının kalkış kapasitesi tarihsel talebinin %50'si)
for airport in routes["origin"].unique():
    airport_routes = routes[routes["origin"] == airport]
    airport_capacity = int(airport_routes["flight_count"].sum() * 0.5)
    prob += (
        lpSum(route_vars[row["route"]] for _, row in airport_routes.iterrows()) <= airport_capacity,
        f"Havalimani_Slot_{airport}",
    )

# Kısıt 3: minimum hizmet seviyesi (her rotaya en az %10 kapasite)
for _, row in routes.iterrows():
    prob += route_vars[row["route"]] >= 0.10 * row["flight_count"], f"Min_Servis_{row['route']}"

# Kısıt 4: yoğunlaşma sınırı (tek rota, toplam kapasitenin %25'ini geçemez)
for _, row in routes.iterrows():
    prob += route_vars[row["route"]] <= 0.25 * TOTAL_CAPACITY, f"Max_Yogunlasma_{row['route']}"

prob.solve()

print(f"Durum: {prob.status} (1 = optimal)")
print(f"Toplam kapasite: {TOTAL_CAPACITY}")
results = routes.copy()
results["assigned_flights"] = [value(route_vars[r]) for r in routes["route"]]
print(results[["route", "origin", "flight_count", "assigned_flights"]])