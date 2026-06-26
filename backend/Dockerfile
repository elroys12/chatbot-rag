# 1. Gunakan Python 3.12 sebagai fondasi stabil
FROM python:3.12-slim

# 2. Set folder kerja di dalam kontainer
WORKDIR /app

# 3. Pasang kompilator C++ 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy file requirements ke dalam kontainer
COPY requirements.txt .

# 5. Jalankan instalasi library
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy seluruh kode proyek Anda ke dalam kontainer
COPY . .

# 7. Ekspos port API aplikasi
EXPOSE 8000

# 8. Perintah eksekusi utama saat container menyala
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]