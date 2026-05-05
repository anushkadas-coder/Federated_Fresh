import json, time, io, os, re, uvicorn
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import PyPDF2
import chromadb
from duckduckgo_search import DDGS
from google import genai 
from google.genai import types
from dotenv import load_dotenv

load_dotenv() 
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class QueryRequest(BaseModel): prompt: str

# --- GLOBAL MEMORY ---
chat_history = [] 
active_image = None 

# --- INITIALIZATION ---
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

print("[SYSTEM] Booting Federated Core (Cloud Embedding Mode)...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="gpt_terminal_v6")

def get_gemini_embeddings(text_list):
    """Offloads heavy embedding generation to Google's cloud API"""
    embeddings = []
    for text in text_list:
        res = client.models.embed_content(
            model="text-embedding-004", 
            contents=text
        )
        embeddings.append(res.embeddings[0].values)
    return embeddings

def smart_chunk_text(text, max_length=500):
    paragraphs = re.split(r'\n\n+', text)
    chunks, current_chunk = [], ""
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_length:
            current_chunk += p + "\n\n"
        else:
            if current_chunk: chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
    if current_chunk: chunks.append(current_chunk.strip())
    return [c for c in chunks if c]

def process_file_background(filename: str, content: bytes, is_pdf: bool):
    text = ""
    if is_pdf:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        for p in reader.pages: 
            extracted = p.extract_text()
            if extracted: text += extracted + "\n"
    else:
        text = content.decode("utf-8", errors="ignore")
        
    chunks = smart_chunk_text(text)
    if chunks:
        ids = [f"{filename}_{i}_{time.time()}" for i in range(len(chunks))]
        collection.add(
            documents=chunks, 
            embeddings=get_gemini_embeddings(chunks), 
            ids=ids, 
            metadatas=[{"source": filename}]*len(chunks) 
        )
    print(f"[VAULT] {filename} completely processed and stored in background.")

@app.get("/")
async def serve_ui():
    """Serves the main terminal interface."""
    return FileResponse("index.html")

@app.get("/files")
async def list_files():
    try:
        res = collection.get(include=['metadatas'])
        files = sorted(list(set([m.get('source') for m in res['metadatas'] if m]))) if res['metadatas'] else []
        return {"files": files}
    except: return {"files": []}

@app.post("/upload")
async def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    global active_image
    try:
        content = await file.read()
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            active_image = content 
            return {"status": "ok", "message": "Image active"}
        
        is_pdf = file.filename.lower().endswith('.pdf')
        background_tasks.add_task(process_file_background, file.filename, content, is_pdf)
        return {"status": "processing", "message": "File sent to background queue"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.post("/stream") 
async def process_ai(request: QueryRequest):
    global chat_history, active_image
    start = time.time()
    ctx, web, source_used = "", "", "AI_CORE"
    query_l = request.prompt.lower()
    
    clean_q = query_l.replace("?", "").replace("!", "").strip()
    if clean_q in ["hi", "hello", "how are you", "test"]:
        source_used = "DIRECT_CHAT"
    elif any(x in query_l for x in ["twitter", "x corp", "ceo of x"]):
        search_query = "X Corp current CEO name"
    else:
        search_query = request.prompt

    if source_used == "AI_CORE":
        if collection.count() > 0:
            try:
                res = collection.query(query_embeddings=get_gemini_embeddings([request.prompt]), n_results=3)
                valid = [doc for doc, dist in zip(res['documents'][0], res['distances'][0]) if dist < 1.4]
                if valid: ctx, source_used = "\n...\n".join(valid), "SECURE_VAULT"
            except Exception as e:
                print(f"RAG Error: {e}")
        
        if source_used == "AI_CORE":
            try:
                with DDGS() as ddgs:
                    res = list(ddgs.text(search_query, max_results=3))
                    if res: web, source_used = "\n".join([r.get('body', '') for r in res]), "LIVE_WEB"
            except: pass

    sys_msg = "You are a precise AI terminal. Respond concisely."
    if source_used == "LIVE_WEB": sys_msg += f"\n\nLIVE DATA: {web}"
    elif source_used == "SECURE_VAULT": sys_msg += f"\n\nVAULT DATA: {ctx}"

    try:
        target_model = "gemini-2.5-flash" 
        formatted_contents = []
        
        for role, text in chat_history[-4:]: 
            formatted_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
            
        current_prompt_text = f"{sys_msg}\n\n{request.prompt}"
        current_parts = []
        
        if active_image:
            current_parts.append(types.Part.from_bytes(data=active_image, mime_type="image/jpeg"))
            active_image = None 
            
        current_parts.append(types.Part.from_text(text=current_prompt_text))
        formatted_contents.append(types.Content(role="user", parts=current_parts))

        response = client.models.generate_content(
            model=target_model,
            contents=formatted_contents
        )
        ans = response.text
        
        chat_history.append(("user", request.prompt))
        chat_history.append(("model", ans))
        
    except Exception as e:
        ans = f"Terminal Error: {e}"

    return {"text": ans, "latency": round(time.time() - start, 3), "source": source_used}

if __name__ == "__main__":
    if not GEMINI_KEY:
        print("[CRITICAL ERROR] GEMINI_API_KEY missing. Ensure it is set in Render Environment Variables.")
    else:
        # Uses Render's dynamic port, falls back to 8080 locally
        port = int(os.environ.get("PORT", 8080))
        uvicorn.run(app, host="0.0.0.0", port=port)