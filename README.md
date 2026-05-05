# 🟢 Federated Fresh // Core Terminal

A high-performance, multi-modal AI Terminal built with **FastAPI**, **Google Gemini 2.5 Flash**, and **ChromaDB**. This system features Local RAG (Retrieval-Augmented Generation), live web search integration, and a custom "Hacker-Aesthetic" interface.

![Terminal Preview](terminal_preview.jpeg)

## 🚀 Live Demo
**Access the Core:** [https://federated-fresh-core.onrender.com](https://federated-fresh-core.onrender.com)

---

## 🛠️ Technical Architecture

This project implements a **Hybrid Intelligence Architecture** that balances local data privacy with cloud-scale reasoning.

### 1. Neural Routing Engine
The system intelligently routes queries based on intent:
*   **Secure Vault (RAG):** If the user uploads documents, the system uses **text-embedding-004** to vectorize and store data in a local **ChromaDB** instance for private querying.
*   **Live Web Search:** For real-time data (e.g., "current stock prices"), the system triggers a **DuckDuckGo** search sweep to provide up-to-date context.
*   **Direct Chat:** Standard conversational queries bypass the search engines for 0.3s latency.

### 2. Optimized Memory Management
To fit within the **512MB RAM constraints** of cloud hosting (Render), this project utilizes **Cloud-Offloaded Embeddings**. Instead of running heavy PyTorch models locally, it utilizes Google’s API to handle vectorization, ensuring the system remains lightweight and fast.

### 3. Multi-Modal Capability
The terminal supports **Vision-to-Text** analysis. Users can upload images (JPG/PNG), which are injected into the Gemini vision buffer for technical analysis and contextual discussion.

---

## 💻 Tech Stack

*   **Backend:** FastAPI (Python 3.11+)
*   **LLM:** Google Gemini 2.5 Flash
*   **Database:** ChromaDB (Vector Store)
*   **Embeddings:** Google `text-embedding-004`
*   **Frontend:** HTML5 / CSS3 (CRT-Scanline Shader) / Vanilla JS
*   **Deployment:** Render (CI/CD via GitHub)

---

## 📂 Project Structure

```text
├── api.py              # Main FastAPI Logic & Neural Routing
├── index.html          # Technical-Cool UI with CRT scanlines
├── requirements.txt    # Cloud-optimized dependencies
├── .env                # API Key storage (Git-ignored)
└── chroma_db/          # Persistent Vector Storage