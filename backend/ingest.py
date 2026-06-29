import os
import time
import pdfplumber
import chromadb
from chromadb.api.types import EmbeddingFunction
from google import genai

# --- KONFIGURASI ---
FOLDER_PDF = "Dokumen_PDF"
DB_PATH = "chroma_db_koperasi"
COLLECTION_NAME = "knowledge_base"
EMBEDDING_MODEL = 'gemini-embedding-001'

client = genai.Client()

def pemisah_rekursif(teks, max_chars=1000, overlap=200, separators=["\n\n", "\n", " ", ""]):
    if len(teks) <= max_chars:
        return [teks]
    
    separator_dipilih = ""
    for sep in separators:
        if sep in teks:
            separator_dipilih = sep
            break
            
    if separator_dipilih:
        splits = teks.split(separator_dipilih)
    else:
        splits = list(teks)

    chunks = []
    current_chunk = ""
    
    for split in splits:
        item_teks = split + separator_dipilih if separator_dipilih else split
        if len(current_chunk) + len(item_teks) <= max_chars:
            current_chunk += item_teks
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            if len(item_teks) > max_chars:
                idx_sep = separators.index(separator_dipilih) + 1 if separator_dipilih in separators else len(separators)
                sub_separators = separators[idx_sep:]
                sub_chunks = pemisah_rekursif(item_teks, max_chars, overlap, sub_separators)
                chunks.extend(sub_chunks)
                current_chunk = ""
            else:
                current_chunk = item_teks
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    chunks_dengan_overlap = []
    for idx, c in enumerate(chunks):
        if idx == 0:
            chunks_dengan_overlap.append(c)
        else:
            mentah = chunks[idx-1][-overlap:] if len(chunks[idx-1]) >= overlap else chunks[idx-1]
            posisi_spasi = mentah.find(" ")
            if posisi_spasi != -1 and posisi_spasi < (overlap // 2):
                konteks_sebelumnya = mentah[posisi_spasi:].strip()
            else:
                konteks_sebelumnya = mentah.strip()
            chunks_dengan_overlap.append(konteks_sebelumnya + " " + c)
            
    return chunks_dengan_overlap

def buat_chunks_dari_pdf():
    if not os.path.exists(FOLDER_PDF):
        os.makedirs(FOLDER_PDF)
        print(f"Folder '{FOLDER_PDF}' dibuat. Silakan isi PDF lalu jalankan ulang.")
        return []

    files = [f for f in os.listdir(FOLDER_PDF) if f.endswith('.pdf')]
    if not files:
        print(f"Tidak ada file PDF di folder '{FOLDER_PDF}'.")
        return []

    print(f"Menemukan {len(files)} file PDF. Memulai Recursive Chunking...")
    semua_chunks = []
    
    for nama_file in files:
        path_pdf = os.path.join(FOLDER_PDF, nama_file)
        print(f"Memproses: {nama_file}...")
        teks_dokumen = ""
        try:
            with pdfplumber.open(path_pdf) as pdf:
                for halaman in pdf.pages:
                    teks_halaman = halaman.extract_text()
                    if teks_halaman:
                        teks_dokumen += teks_halaman + "\n"
            
            daftar_teks_chunk = pemisah_rekursif(teks_dokumen, max_chars=1000, overlap=200)
            for chunk_idx, teks_chunk in enumerate(daftar_teks_chunk):
                semua_chunks.append({
                    "id": f"{nama_file}_chunk_{chunk_idx}",
                    "text": teks_chunk,
                    "metadata": {"sumber": nama_file, "chunk_ke": chunk_idx}
                })
        except Exception as e:
            print(f"Gagal membaca {nama_file}: {e}")
            
    return semua_chunks

class GoogleEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        super().__init__()
    def __call__(self, input: list[str]) -> list[list[float]]:
        response = client.models.embed_content(model=EMBEDDING_MODEL, contents=input)
        return [embedding.values for embedding in response.embeddings]
    def name(self) -> str:
        return "GoogleEmbeddingFunction"

# Utama
if __name__ == "__main__":
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    embedding_fn = GoogleEmbeddingFunction()
    
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )
    
    chunks = buat_chunks_dari_pdf()
    if chunks:
        print(f"Mengubah {len(chunks)} chunks menjadi Embedding")
        
        batch_size = 5 
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            try:
                # AMBIL LIST TEKS DARI BATCH
                batch_texts = [item["text"] for item in batch]
                
                # UBAH TEKS MENJADI VEKTOR MENGGUNAKAN CLASS KUSTOM ANDA
                batch_embeddings = embedding_fn(batch_texts)
                
                # MASUKKAN KE CHROMADB BERSAMA VEKTORNYA
                collection.add(
                    ids=[item["id"] for item in batch],
                    embeddings=batch_embeddings,   # <--- TAMBAHKAN PARAMS INI!
                    documents=batch_texts,
                    metadatas=[item["metadata"] for item in batch]
                )
                print(f"Berhasil mengindeks chunk ke-{i} sampai {min(i + batch_size, len(chunks))}")
                
                time.sleep(4) 
                
            except Exception as e:
                print(f"🚨 Gagal pada batch ini ({e}), mencoba memasukkan satu per satu...")
                for item in batch:
                    try:
                        single_embedding = embedding_fn([item["text"]])
                        collection.add(
                            ids=[item["id"]], 
                            embeddings=single_embedding,
                            documents=[item["text"]], 
                            metadatas=[item["metadata"]]
                        )
                        time.sleep(5)
                    except Exception as inner_e:
                        print(f"Chunk {item['id']} dilewati: {inner_e}")
                        
        print(f"Selesai! Total {collection.count()} data aman tersimpan di '{DB_PATH}'.")