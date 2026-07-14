# Legalitas UMKM AI Assistant - Backend (RAG System)

Backend service berbasis Python yang berfungsi sebagai asisten digital (chatbot) konsultasi legalitas UMKM untuk Dinas Koperasi dan UKM Provinsi Jawa Timur. Proyek ini mengimplementasikan metode **RAG (Retrieval-Augmented Generation)** menggunakan LLM untuk menjawab pertanyaan seputar regulasi dan panduan UMKM berdasarkan dokumen PDF resmi dinas.

---

## Fitur Utama

* **Semantic Search:** Pencarian dokumen referensi berdasarkan kedekatan makna (konteks), bukan sekadar mencocokkan kata kunci (*keyword matching*).
* **Anti-Hallucination Guardrails:** AI dibatasi secara ketat hanya boleh menjawab berdasarkan dokumen regulasi resmi yang terdaftar di basis data.
* **Persistent Vector Storage:** Menyimpan 555 chunk embedding dokumen secara aman dan permanen menggunakan ChromaDB.
* **Production-Ready API:** Dibangun dengan FastAPI yang memiliki performa tinggi, validasi skema data yang ketat, dan dokumentasi Swagger otomatis.
* **Dockerized Infrastructure:** Seluruh lingkungan sistem backend diisolasi menggunakan kontainer Docker untuk kemudahan deployment.

---

## Arsitektur Teknologi

* **Framework:** FastAPI (Python)
* **LLM & Embedding Engine:** Google Gemini API (`gemini-2.5-flash` & `text-embedding-004`)
* **Vector Database:** ChromaDB (Persistent Storage)
* **Containerization:** Docker & Docker Volumes
* **Frontend Compatibility:** Terintegrasi dengan React.js via konfigurasi CORS Middleware

---

##  Struktur Repositori

Berdasarkan struktur folder pada direktori `backend/`:

```text
chatbot-rag/backend/
├── Dokumen_PDF/          # Direktori penyimpanan dokumen PDF regulasi dari Dinas Koperasi & UKM Jatim
├── .env.example          # Template konfigurasi environment variables (API Key, Database, dll.)
├── .gitignore            # Konfigurasi file/folder yang diabaikan oleh Git (misal: database lokal, venv)
├── Dockerfile            # Konfigurasi Docker Image untuk deployment berbasis kontainer
├── ingest.py             # Script untuk memproses PDF, melakukan chunking, dan menyimpan ke Vector DB
├── main.py               # Entrypoint utama aplikasi backend (FastAPI / Flask API untuk chat interface)
└── requirements.txt      # Daftar dependensi library Python yang dibutuhkan
```

---

##  Alur Kerja Sistem (System Workflow)

Sistem RAG *(Retrieval-Augmented Generation)* ini berjalan melalui **2 langkah utama**:

### 1. Tahap Persiapan Data (Ingestion)
Tahap ini dilakukan sekali di awal (atau ketika ada dokumen baru) untuk membangun basis pengetahuan asisten digital:
1. **Ekstraksi Teks:** File regulasi PDF di dalam folder `Dokumen_PDF/` dibaca dan diekstrak teks mentahnya.
2. **Pemotongan Teks (*Chunking*):** Teks yang sangat panjang dipotong menjadi bagian-bagian kecil (*chunks*) agar pencarian informasi nantinya lebih fokus dan akurat.
3. **Vektorisasi (*Embedding*):** Setiap potongan teks diubah menjadi representasi angka (vektor) menggunakan model *Embedding*.
4. **Penyimpanan:** Vektor-vektor tersebut disimpan ke dalam database vektor (*Vector Store*) lokal untuk siap dicari kapan saja.

### 2. Tahap Tanya-Jawab (Query & Generation)
Tahap ini berjalan secara otomatis dan *real-time* setiap kali pengguna (pelaku UMKM) mengirimkan pertanyaan:
1. **Input Pengguna:** Pengguna memasukkan pertanyaan ke chatbot (melalui API di `main.py`).
2. **Pencarian Informasi:** Sistem mengubah pertanyaan tersebut menjadi vektor, lalu mencari potongan dokumen PDF paling relevan di dalam *Vector Store*.
3. **Penggabungan Konteks:** Potongan dokumen paling relevan yang ditemukan digabungkan bersama dengan pertanyaan asli pengguna ke dalam sebuah instruksi (*Prompt*).
4. **Pembuatan Jawaban:** Instruksi tersebut dikirim ke LLM (*Large Language Model*). Model akan memproses dan merumuskan jawaban yang akurat berdasarkan dokumen dinas.
5. **Respons:** Jawaban dikirim kembali ke layar percakapan pengguna secara *real-time*.

##  Panduan Setup Environment

Ikuti langkah-langkah berikut untuk menjalankan backend ini di mesin lokal Anda sebagai developer.

### Prasyarat (Prerequisites)
Pastikan Anda sudah menginstal:
* Python 3.10 atau versi di atasnya
* Docker (jika ingin menjalankan menggunakan kontainer)
* Git

---

### Metode 1: Local Development (Tanpa Docker)

**1. Clone Repositori & Masuk ke Direktori Backend**
```bash
git clone https://github.com/elroys12/chatbot-rag.git
cd chatbot-rag/backend
```

**2. Buat dan Aktifkan Virtual Environment**
*   **Windows:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
*   **macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

**3. Instal Dependensi**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Konfigurasi Environment Variables**
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```
Buka file `.env` dan masukkan API Key Anda (misalnya API key OpenAI, Gemini, atau konfigurasi database lokal):
```env
# Contoh konfigurasi .env
API_KEY=your_llm_api_key_here
```

**5. Jalankan Proses Ingest Data**
Letakkan file PDF regulasi dari Dinas Koperasi & UKM ke dalam folder `Dokumen_PDF/`, kemudian jalankan script ingest untuk membangun basis pengetahuan:
```bash
python ingest.py
```

**6. Jalankan Server Backend**
Jalankan aplikasi utama untuk melayani chat request:
```bash
python main.py
```

---

### Metode 2: Menggunakan Docker (Virtualisasi & Cloud Ready)

Metode ini mengisolasi seluruh dependensi ke dalam kontainer Docker, menyederhanakan deployment di lokal maupun cloud server.

**1. Build Docker Image**
```bash
docker build -t chatbot-rag-backend .
```

**2. Jalankan Kontainer Docker**
Jalankan kontainer dengan memetakan port yang sesuai dan menyertakan konfigurasi environment dari file `.env`:
```bash
docker run -d -p 8000:8000 --env-file .env --name chatbot-backend-container chatbot-rag-backend
```

Aplikasi backend sekarang siap melayani request pada alamat `http://localhost:8000`.
