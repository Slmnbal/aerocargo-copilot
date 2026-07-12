FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# requirements.txt macOS'ta "pip freeze" ile üretildi ve torch'u sürüm sabitliyor
# (torch==...) — Linux'ta bu pin, varsayılan PyPI indeksinden ~2GB'lık gereksiz CUDA/GPU
# paketlerini (nvidia-*) çekiyor, oysa bu container'da GPU yok. Önce CPU-only torch'u
# ayrı bir indeksten kuruyoruz, sonra requirements.txt'in geri kalanını torch pini
# olmadan kuruyoruz ki pip CUDA sürümüne "yükseltmeye" çalışmasın.
RUN grep -v '^torch==' requirements.txt > requirements-cpu.txt \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements-cpu.txt

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
