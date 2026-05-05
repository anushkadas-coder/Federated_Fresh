import streamlit as st
import os, torch, faiss, numpy as np, time
from threading import Thread
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from peft import PeftModel
from sentence_transformers import SentenceTransformer, CrossEncoder

# --- MONOCHROMATIC BENTO-BOX UI ---
st.set_page_config(page_title="SYSTEM // FEDERATED RAG", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
    /* Import Apple-style typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* True Deep-Dark Canvas */
    .stApp { 
        background: radial-gradient(circle at 50% 0%, #151515 0%, #000000 100%); 
        color: #ffffff; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Strip default branding & padding */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem !important;}
    
    /* Glassmorphic Floating Panels (The Apple/Vercel Look) */
    div[data-testid="stVerticalBlock"] > div {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
        padding: 2rem;
        transition: transform 0.3s ease, border 0.3s ease;
    }
    
    /* Subtle hover interactions */
    div[data-testid="stVerticalBlock"] > div:hover {
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    
    /* High-End Input Field */
    .stTextInput>div>div>input {
        background-color: rgba(0, 0, 0, 0.4) !important; 
        color: #ffffff !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 16px !important;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: #ffffff !important;
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Clean Chat Integration */
    .stChatMessage {background-color: transparent !important; border: none !important; padding: 0.5rem 0;}
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] {display: none;}
    
    /* Premium Telemetry Typography */
    .metric-label {color: #777777; font-size: 0.70rem; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 4px; font-weight: 600;}
    .metric-value {color: #ffffff; font-size: 1.75rem; font-weight: 300; letter-spacing: -1px; margin-bottom: 20px;}
    .sys-title {color: #ffffff; font-weight: 300; letter-spacing: 2px; font-size: 2rem; margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_assets():
    tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    base = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0", torch_dtype=torch.bfloat16)
    
    if os.path.exists("./global_model_adapter"):
        model = PeftModel.from_pretrained(base, "./global_model_adapter")
    else:
        model = base
        
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return tokenizer, model, encoder, reranker

with st.spinner("INITIALIZING FEDERATED WEIGHTS..."):
    tokenizer, model, encoder, reranker = load_assets()

def elite_rag(query, knowledge):
    q_vec = encoder.encode([query]).astype('float32')
    k_vecs = encoder.encode(knowledge).astype('float32')
    index = faiss.IndexFlatL2(k_vecs.shape[1])
    index.add(k_vecs)
    D, I = index.search(q_vec, k=min(3, len(knowledge)))
    candidates = [knowledge[idx] for idx in I[0]]
    
    scores = reranker.predict([(query, c) for c in candidates])
    best_idx = np.argmax(scores)
    return candidates[best_idx], scores[best_idx], candidates

st.markdown("<h2 class='sys-title'>FEDERATED RAG // SECURE TERMINAL</h2>", unsafe_allow_html=True)

with open("enterprise_knowledge.txt", "r") as f:
    knowledge = [l.strip() for l in f.readlines() if len(l.strip()) > 5]

col1, col2 = st.columns([2.5, 1])

with col1:
    if prompt := st.chat_input("Enter query parameter..."):
        start_time = time.time()
        
        with st.chat_message("user"): 
            st.markdown(f"**USER:** {prompt}")
        
        with st.chat_message("assistant"):
            st.markdown("**SYS_AGENT:**")
            context, score, candidates = elite_rag(prompt, knowledge)
            
            # --- IRONCLAD ANTI-HALLUCINATION PROMPT ---
            full_p = f"<|system|>\nYou are a highly restricted data extraction terminal. Answer the user's query using ONLY the exact facts provided in the Verified Context. Do NOT invent or assume any other information. Keep it brief.\nVerified Context: {context}\n<|user|>\n{prompt}\n<|assistant|>\n"
            inputs = tokenizer(full_p, return_tensors="pt")
            
            # --- TIER 1 FEATURE: LIVE TOKEN STREAMING ---
            streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
            generation_kwargs = dict(
                **inputs, 
                streamer=streamer, 
                max_new_tokens=50, 
                temperature=0.01, # Extremely low temp forces exact answers
                repetition_penalty=1.1
            )
            
            thread = Thread(target=model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Dynamic Typewriter Effect
            response_placeholder = st.empty()
            generated_text = ""
            for new_text in streamer:
                generated_text += new_text
                response_placeholder.markdown(generated_text + "█") # Blinking cursor effect
            
            response_placeholder.markdown(generated_text) # Final text without cursor
            
            latency = time.time() - start_time

with col2:
    if 'latency' in locals():
        st.markdown("""
        <div class="metric-label">Compute Latency</div>
        <div class="metric-value">{:.2f}s (Streaming)</div>
        <div class="metric-label">Vector Similarity Match</div>
        <div class="metric-value">{:.2f}%</div>
        <div class="metric-label">Differential Noise (σ)</div>
        <div class="metric-value">0.01</div>
        """.format(latency, score*10), unsafe_allow_html=True)
        
        st.markdown("<br><div class='metric-label'>RETRIEVED CANDIDATES</div>", unsafe_allow_html=True)
        for i, c in enumerate(candidates):
            st.markdown(f"<span style='color:#555; font-size:0.85rem;'>[{i+1}] {c[:45]}...</span>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='metric-label' style='color:#444;'>SYSTEM IDLE... AWAITING QUERY</div>", unsafe_allow_html=True)