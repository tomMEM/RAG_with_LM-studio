# RAG Repository Modernization Plan

## Current State Analysis

Your project uses:
- ✅ **LM Studio** (local LLMs) — good for privacy
- ✅ **GROBID** (scientific PDF extraction) — excellent for academic papers
- ✅ **ChromaDB** (vector store) — simple & effective
- ❌ **GROBID Docker** (complex, heavy, slow)
- ❌ **No API flexibility** (locked to LM Studio)
- ❌ **Notebooks only** (not modular or deployable)

---

## Modernization Roadmap

### 1. **Replace GROBID Docker with Simpler PDF Extraction**

**Current complexity:** Docker + GROBID service running = heavy setup

**Modern alternatives (much simpler):**

```python
# Option A: PyMuPDF (fast, no dependencies)
import fitz  # PyMuPDF

pdf_path = "paper.pdf"
doc = fitz.open(pdf_path)
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    print(text)

# Option B: pypdf (pure Python)
from pypdf import PdfReader

reader = PdfReader("paper.pdf")
for page in reader.pages:
    print(page.extract_text())

# Option C: pdfplumber (best for tables)
import pdfplumber

with pdfplumber.open("paper.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        tables = page.extract_tables()
```

**Trade-off:** Less sophisticated than GROBID (won't extract formulas/citations as structured data), but **instant setup, no Docker**.

**My recommendation:** Start with **PyMuPDF** for speed, keep GROBID as optional for scientific metadata extraction.

---

### 2. **Add Multi-API Support (Like Your Chat Dashboard Does)**

Your **Chat_Dashboard_OpenAI_Gemini_KIMI.ipynb** is modern! Apply that pattern to RAG:

```python
# Modern approach: Flexible API selection
class RAGPipeline:
    def __init__(self, provider="lm_studio"):
        self.provider = provider
    
    def get_embeddings(self, text):
        if self.provider == "lm_studio":
            return self.lm_studio_embed(text)
        elif self.provider == "openai":
            return self.openai_embed(text)
        elif self.provider == "huggingface":
            return self.huggingface_embed(text)
    
    def get_response(self, prompt):
        if self.provider == "lm_studio":
            return self.lm_studio_chat(prompt)
        elif self.provider == "openai":
            return self.openai_chat(prompt)  # GPT-4, Claude, etc.
        elif self.provider == "local":
            return self.ollama_chat(prompt)   # Ollama
```

**Benefits:**
- Users can switch providers easily
- Use OpenAI for production, LM Studio for testing
- Support Claude, Gemini, local Ollama, etc.

---

### 3. **Convert Notebooks → Production Code**

**Current:** Notebooks are exploratory, hard to deploy
**Modern:** Extract into Python modules

```
rag_project/
├── src/
│   ├── pdf_extractor.py      # Simple PDF extraction
│   ├── embeddings.py          # Handle multiple embeddings APIs
│   ├── vectorstore.py         # ChromaDB wrapper
│   ├── rag_chain.py           # Core RAG logic
│   └── config.py              # Config management
├── notebooks/
│   ├── 01_exploration.ipynb   # Keep for exploration
│   └── 02_results.ipynb       # For results/docs
├── app.py                     # Gradio app (keep your dashboard)
└── requirements.txt
```

**Advantage:** Notebook stays for UI, code is reusable & testable

---

### 4. **Modern Alternatives to LM Studio + GROBID**

| Problem | Old Solution | Modern Alternative | Complexity |
|---------|--------------|-------------------|-----------|
| **Local LLM** | LM Studio | Ollama (faster, simpler) | ⭐ |
| **PDF extraction** | GROBID Docker | PyMuPDF or pdfplumber | ⭐ |
| **Embeddings** | LM Studio embeddings | Sentence-transformers (no server needed) | ⭐⭐ |
| **Vector DB** | ChromaDB | ChromaDB (unchanged, still good) | ✓ |
| **Chat UI** | Gradio | Gradio or Streamlit | ✓ |

**Recommendation:** Replace with **Ollama** (like LM Studio, but 10x simpler):

```bash
# Instead of LM Studio GUI, just:
ollama pull mistral
ollama serve

# Use directly in Python:
from langchain_ollama import OllamaLLM
llm = OllamaLLM(model="mistral")
response = llm.invoke("Summarize this: ...")
```

---

### 5. **Add Modern Features**

**Quick wins:**

```python
# A) Hybrid search (keyword + semantic)
results = chromadb_search(query, k=5, method="hybrid")

# B) Caching (avoid re-embedding)
@cache
def embed_documents(doc_ids):
    return embeddings.embed_batch(docs)

# C) Async processing (faster)
async def process_pdfs_parallel(pdf_paths):
    tasks = [process_pdf(p) for p in pdf_paths]
    return await asyncio.gather(*tasks)

# D) Streaming responses (better UX)
for chunk in llm.stream(prompt):
    print(chunk, end="", flush=True)
```

---

## Concrete Modernization Plan (Priority Order)

### Phase 1: Quick Win (1-2 hours) ✅
1. Replace GROBID with **PyMuPDF** or **pdfplumber**
2. Update `config.json` to support multiple PDF extractors
3. Add environment variables for API keys (`.env` file)

### Phase 2: Multi-API Support (2-3 hours) ⭐ Recommended
1. Add **OpenAI** fallback option
2. Add **Ollama** as alternative to LM Studio
3. Create provider abstraction layer

### Phase 3: Code Modernization (3-4 hours)
1. Extract core logic from notebooks → `src/` modules
2. Add simple unit tests
3. Create `app.py` wrapper for Gradio

### Phase 4: Nice-to-Have (optional)
1. Add streaming responses
2. Add hybrid search
3. Add metadata filtering
4. Dockerfile for deployment

---

## Example: Minimal Modernized Version

Here's what your `app.py` could look like (modern + simpler):

```python
import gradio as gr
import pdfplumber
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaLLM
import chromadb
from dotenv import load_dotenv

load_dotenv()

class ModernRAG:
    def __init__(self, embedding_model="openai", llm_model="ollama/mistral"):
        self.embeddings = OpenAIEmbeddings() if "openai" in embedding_model else OllamaEmbeddings()
        self.llm = OllamaLLM(model="mistral")
        self.db = chromadb.Client()
    
    def extract_pdf(self, pdf_file):
        """Simple PDF extraction - no Docker needed"""
        with pdfplumber.open(pdf_file) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages])
    
    def add_documents(self, docs):
        """Add docs to vector DB"""
        embeddings = self.embeddings.embed_documents(docs)
        self.db.add(embeddings=embeddings, documents=docs)
    
    def chat(self, query):
        """RAG chat with streaming"""
        # Retrieve
        results = self.db.query(query, n_results=5)
        context = "\n".join(results['documents'][0])
        
        # Prompt
        prompt = f"Context: {context}\n\nQuestion: {query}"
        
        # Generate (with streaming)
        return self.llm.stream(prompt)

# Gradio UI
rag = ModernRAG()

with gr.Blocks() as app:
    gr.Markdown("# Modern RAG Dashboard")
    
    with gr.Tabs():
        with gr.Tab("📄 Upload PDFs"):
            file_input = gr.File(label="Upload PDF")
            status = gr.Textbox()
            file_input.upload(lambda f: rag.extract_pdf(f) and "✅ Uploaded", 
                            inputs=file_input, outputs=status)
        
        with gr.Tab("💬 Chat"):
            chat_input = gr.Textbox(label="Ask about your documents")
            chat_output = gr.Textbox(label="Response", lines=10)
            chat_input.submit(rag.chat, inputs=chat_input, outputs=chat_output)

app.launch()
```

**This version:**
- ✅ No Docker needed
- ✅ Simple PDF extraction
- ✅ Same Gradio UI you have
- ✅ Flexible API support
- ✅ ~50 lines vs notebooks

---

## Which Should You Do First?

**My recommendation (order):**

1. **Phase 1** (1-2 hrs) — Replace GROBID Docker with PyMuPDF
   - Huge setup improvement
   - No breaking changes
   - Users will appreciate simpler setup

2. **Phase 2** (2-3 hrs) — Add multi-API support
   - Reuse pattern from your Chat Dashboard
   - Keep existing LM Studio as default
   - Let users try OpenAI without changing code

3. **Phase 3** (later) — Only if you want production deployment
