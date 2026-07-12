import os

# MLflow 3.x, dosya tabanlı (./mlruns) tracking backend'ini "bakım modu"na aldı ve
# varsayılan olarak hata fırlatıyor (sqlite/postgres gibi bir veritabanına geçişi
# öneriyor). Bu proje ücretsiz/sıfır-kurulum prensibiyle yerel dosya backend'inde
# kalıyor (mlruns/ zaten .gitignore'da, tek kullanıcılık bir proje için yeterli) —
# bu yüzden mlflow'u import etmeden önce opt-out bayrağını set ediyoruz.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

df = pd.read_csv("data/route_features.csv").dropna(
    subset=["days_per_week", "flight_count", "origin_popularity", "destination_popularity"]
)

X = df[["origin", "destination", "days_per_week", "origin_popularity", "destination_popularity"]]
y = df["flight_count"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
y_train_log = np.log1p(y_train)

preprocessor = ColumnTransformer(
    transformers=[("kategorik", OneHotEncoder(handle_unknown="ignore"), ["origin", "destination"])],
    remainder="passthrough",
)

mlflow.set_experiment("aerocargo-talep-tahmini")

def train_and_log(model, model_name, register=False):
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])
    with mlflow.start_run(run_name=model_name):
        pipeline.fit(X_train, y_train_log)
        predictions = np.expm1(pipeline.predict(X_test))

        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        mlflow.log_param("model_type", model_name)
        mlflow.log_param("features", "origin, destination, days_per_week, origin_popularity, destination_popularity")
        mlflow.log_param("target_transform", "log1p")
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("r2", r2)
        kwargs = {"registered_model_name": "aerocargo_forecast_model"} if register else {}
        mlflow.sklearn.log_model(pipeline, "model", **kwargs)
        print(f"{model_name} -> MAE: {mae:.1f}, R2: {r2:.3f}")
        return mlflow.active_run().info.run_id, mae

sonuclar = [
    ("LinearRegression_v2", *train_and_log(LinearRegression(), "LinearRegression_v2", register=True)),
    ("RandomForest_v2", *train_and_log(RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42), "RandomForest_v2", register=True)),
]

# En düşük MAE'ye sahip modeli "champion" alias'ıyla işaretliyoruz. Stage'ler
# (Staging/Production) MLflow 2.9'dan beri deprecated; yerine önerilen yöntem bu.
# src/forecast_model.py serve ederken hep bu alias'ı yüklüyor, böylece "hangi versiyon
# en iyisiydi" bilgisini elle takip etmeye ya da koda gömmeye gerek kalmıyor.
client = mlflow.MlflowClient()
en_iyi_isim, en_iyi_run_id, en_iyi_mae = min(sonuclar, key=lambda s: s[2])
en_iyi_versiyon = next(
    v.version for v in client.search_model_versions("name='aerocargo_forecast_model'")
    if v.run_id == en_iyi_run_id
)
client.set_registered_model_alias("aerocargo_forecast_model", "champion", en_iyi_versiyon)
print(f"\nChampion: {en_iyi_isim} (v{en_iyi_versiyon}, MAE: {en_iyi_mae:.1f})")