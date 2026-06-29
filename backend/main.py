import chromadb
from google import genai
from google.genai import types
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- KONFIGURASI ---
DB_PATH = "chroma_db_koperasi"
COLLECTION_NAME = "knowledge_base"
MODEL_NAME = 'gemini-2.5-flash'
EMBEDDING_MODEL = 'gemini-embedding-001'
DISTANCE_THRESHOLD = 0.6

client = genai.Client()

# --- INSTANSIASI FASTAPI ---
app = FastAPI(
    title="Backend RAG Chatbot Dinas Koperasi",
    description="API Server untuk sistem Retrieval-Augmented Generation menggunakan ChromaDB dan Gemini",
    version="1.0.0"
)

# --- KONFIGURASI CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MEMUAT DATABASE LOKAL ---
collection = None

try:
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    
    # mengambil koleksi secara mentah. 
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    
    print(f"Database terhubung. Total data: {collection.count()} chunks.")
except Exception as e:
    print(f"🚨 GAGAL MEMUAT DATABASE SAAT STARTUP: {e}")
    print("Pastikan folder 'chroma_db_koperasi' ada dan ingest.py sudah sukses dijalankan.")

# --- VALIDASI INPUT ---
class ChatRequest(BaseModel):
    message: str

# --- ENDPOINT UTAMA API ---
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    pertanyaan_user = request.message
    
    if not pertanyaan_user.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong")
    
    if collection is None:
        raise HTTPException(
            status_code=503, 
            detail="Layanan database belum siap atau gagal dimuat. Silakan jalankan ingest.py terlebih dahulu di server."
        )
        
    try:
        # A. Proses Vektorisasi Pertanyaan User
        response_embedding = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=pertanyaan_user,
        )
        query_vector = response_embedding.embeddings[0].values

        # B. Cari dokumen di ChromaDB
        hasil_pencarian = collection.query(query_embeddings=[query_vector], n_results=3)
        
        dokumen_referensi = ""
        sumber_terpakai = set()
        
        if hasil_pencarian and 'documents' in hasil_pencarian and hasil_pencarian['documents']:
            chunks_teks = hasil_pencarian['documents'][0]
            metadatas = hasil_pencarian['metadatas'][0] if hasil_pencarian['metadatas'] else []
            distances = hasil_pencarian['distances'][0] if hasil_pencarian['distances'] else []
            
            for idx, teks_chunk in enumerate(chunks_teks):
                skor_jarak = distances[idx] if idx < len(distances) else 999.0
                meta = metadatas[idx] if idx < len(metadatas) else {"sumber": "Tidak diketahui", "chunk_ke": "?"}
                
                if skor_jarak <= DISTANCE_THRESHOLD:
                    dokumen_referensi += f"\n- {teks_chunk}\n"
                    sumber_terpakai.add(f"{meta.get('sumber')} (Chunk {meta.get('chunk_ke')})")

        # C. GENERATION PROCESS
        instruksi_sistem = (
            "Anda adalah asisten AI resmi untuk Dinas Koperasi dan UKM Provinsi Jawa Timur. "
            "Tugas Anda adalah menjawab pertanyaan masyarakat dengan ramah, jelas, dan profesional. "
            "Anda HANYA BOLEH menjawab berdasarkan 'DOKUMEN REFERENSI' resmi yang disediakan di bawah ini. "
            "Jika 'DOKUMEN REFERENSI' kosong atau tidak ada jawabannya, katakan secara jujur: "
            "'Mohon maaf, informasi tersebut belum tersedia di basis data kami. Anda dapat menghubungi pihak dinas langsung melalui Instagram resmi kami di [@diskopukm_jatim](https://www.instagram.com/diskopukm_jatim).'\n\n"
            f"--- DOKUMEN REFERENSI --- \n{dokumen_referensi}"
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=pertanyaan_user,
            config=types.GenerateContentConfig(system_instruction=instruksi_sistem, temperature=0.3)
        )
        
        final_sources = list(sumber_terpakai)
        if "Mohon maaf, informasi tersebut belum tersedia" in response.text:
            final_sources = []
            
        return {
            "reply": response.text,
            "sources": final_sources
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal pada server AI: {str(e)}")

# Endpoint Health Check
@app.get("/")
def read_root():
    return {"status": "online", "message": "API Chatbot Dinas Koperasi siap digunakan"}