# RAG with LM Studio: Local LLMs for Document Interaction

This project provides tools and a Gradio-based dashboard for performing Retrieval Augmented Generation (RAG) using local Large Language Models (LLMs) run via LM Studio. It allows you to process your documents, create searchable vector databases, and chat with your data.

## Key Features:

*   **Local LLM Integration:** Designed to work with LLMs hosted locally through [LM Studio](https://lmstudio.ai/).
*   **Document Processing:** Ingest PDFs or text files, extract content (optionally using Grobid for scientific PDFs), and store structured data in SQLite databases.
*   **Vector Database Creation:** Build ChromaDB vector stores from your SQLite data for efficient semantic search.
*   **SQLite Data Viewer:** Inspect the contents of your processed SQLite databases directly within the dashboard.
*   **Interactive RAG Chat:** Converse with your documents using a Gradio interface, leveraging retrieved context to inform LLM responses.
*   **Flexible Retrieval Methods:** Experiment with different query refinement techniques (keywords, LLM-based refinement, original query).

## Main Application: Gradio Dashboard

The primary interface is a Gradio dashboard, derived from `StandAlone_Load_Vecdb_RAG_CHAT_v4.ipynb` (and likely run as `standalone_app.py` or similar after conversion).

### How to Use the Gradio Dashboard:

1.  **Prerequisites:**
    *   **LM Studio:** Ensure LM Studio is installed, running, and a compatible model is loaded and served on the local server (typically `http://localhost:1238/v1`). The application is pre-configured to use this endpoint, but also normal OpenAI API could be used.
    *   **Python Environment:** Make sure you have all necessary Python packages installed (e.g., `gradio`, `openai`, `langchain`, `chromadb`, `pypdf`, `requests`, etc.).
    *   **Grobid (Optional):** If processing PDFs using the "grobid" mode, ensure your Grobid service is running and accessible (the app uses a `config.json` for Grobid client settings, typically pointing to `http://localhost:8070`).

2.  **Launch the Dashboard:**
    Navigate to the project directory and open StandAlone_Load_Vecdb_RAG_CHAT_v4.ipynb
    or 
    ```bash
    python standalone_app.py # in case it has been converted
    ```
    The application will typically launch on `http://127.0.0.1:7860` (or as specified in the script's `demo.launch()` method). Open this URL in your web browser.
    * in case of PDF text extraction by GROBID, then start GROBID Docker as outlined in README.md
    * if new databases from a pdf collections are not planned, or finished, then stop docker
    * for RAG Chat switch on LM Studio Server with LLM and Embedding Model (server port: 1234)

3.  **Dashboard Tabs & Functionality:**

    *   **📄 Data Ingestion & DB Management Tab:**
        *   **1. Process PDF/Text to SQLite Database:**
            *   **Upload Files:** Upload your PDF or TXT files directly.
            *   **Server Directory:** Alternatively, specify a path to a directory on the server containing your documents.
            *   **Output Settings:** Define the output directory for the SQLite DB and a name for the database.
            *   **Processing Mode:** Choose "grobid" (for structured PDF extraction), "text" (for plain text), or "both".
            *   **Overwrite:** Option to overwrite an existing SQLite DB.
            *   Click "⚙️ Process Files to SQLite" to start ingestion. The processed data will be saved in an SQLite database.
        *   **2. View SQLite Database Records:**
            *   **Load DB:** Select a processed SQLite database using the dropdown (which lists DBs from your `docs` folder) or by pasting its path into the textbox. Click "📂 Load SQLite DB for Viewing".
            *   **Browse Records:** Once loaded, select individual records from the "Select Record (ID: Title)" dropdown to view their details (Record Number, Authors, Date, etc.) and content (Abstract/Body).

    *   **🔬 Scientific RAG Conversation Tab:**
        *   **1. RAG Database Management:**
            *   **Select Source Folder:** Choose a "Document Collection Source Folder" from the dropdown. These folders are expected to be subdirectories within your main `docs` directory.
            *   **Action for RAG DB:**
                *   **Load Existing ChromaDB:** If the selected source folder already contains a pre-built ChromaDB (typically in a `chroma_db` subfolder or a custom-named `chroma_<name>_db` subfolder), use this option to load it.
                *   **Create New ChromaDB (from SQLite):**
                    *   If you choose this, a second dropdown will appear: "Select Specific SQLite File for New RAG DB".
                    *   Select the desired SQLite database from within the chosen source folder.
                    *   The system will then chunk the documents from this SQLite DB and create a new ChromaDB vector store. The ChromaDB will be named based on the SQLite file (e.g., `docs/my_collection/chroma_mydata_db/` if you processed `mydata.db`).
            *   **Overwrite:** Option to overwrite an existing ChromaDB if creating a new one and the target directory exists.
            *   Click "🔄 Process Selected RAG Database". The status will update, indicating the number of original documents and chunks in the loaded/created RAG DB.
        *   **2. Chat Controls & Conversation:**
            *   **Retrieval Method:** Select how your query should be refined for document retrieval (e.g., 'combined', 'keywords', 'llm', 'original_query').
            *   **Chunks to Retrieve (K):** Adjust the number of document chunks to retrieve for context.
            *   **Chat:** Type your query into the textbox and press Enter.
                *   The system will retrieve relevant document chunks from the active RAG DB.
                *   The query, conversation history (optional), and retrieved documents will be formatted into a prompt for the LLM.
                *   The LLM's response will appear in the chat window.
            *   **Special Queries:**
                *   `doc_id:<number>`: Directly retrieve all chunks for a specific original document ID.
                *   `{no history}`: Append to your query to exclude past conversation from the LLM prompt.
        *   **3. Timings and Debug Information (Accordion):**
            *   Expand this section to see details about the retrieval query used, the full prompt sent to the LLM, and timing information for retrieval and LLM response.

## Other Notebooks

*   **`PDF_RAG_with_LMstudio_opti.ipynb`**: Contains earlier, cell-by-cell explorations and optimizations for RAG based on a set of PDFs. This can be useful for understanding the underlying steps or for more granular experimentation.

## Project Structure (Illustrative)

```text
your_project_directory/
├── StandAlone_Load_Vecdb_RAG_CHAT_v4.ipynb
├── (or standalone_app.py)
├── assets/                   # Utility functions, configurations
│   ├── func_inputoutput.py
│   └── pdftosqlite_processor.py# PDF to SQLite processing logic
├── docs/                     # Root for document collections and databases
│   ├── my_collection_A/
│   │   ├── source_doc1.pdf
│   │   ├── my_data_A.db        # SQLite DB created by ingestion
│   │   └── chroma_my_data_A_db/  # ChromaDB created from my_data_A.db
│   │       └── chroma.sqlite3
│   │       └── ...
│   └── my_collection_B/
│       ├── another.db
│       └── chroma_db/          # Default named ChromaDB
│           └── ...
├── processed_databases/ # Default output location for SQLite DBs
│   └── ...
├── pdf_ingestion_settings.json # Saved settings for the ingestion tab
│── config.json # Settings for GROBID
```

## Setup Notes & Troubleshooting

*   Ensure all file paths in the application (e.g., for `BASE_DOCS_PATH`, Grobid config) are correctly set for your environment.
*   If LM Studio or Grobid are running on different ports/addresses, update the client configurations.
*   Check the console outputs for any error messages or warnings.


