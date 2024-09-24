# RAG with LM Studio
RAG with LM Studio, local LLMs
## Main Notebook for RAG based on a set of PDFs: `PDF_RAG_with_LMstudio.ipynb`
This notebook performs the following operations:
- **Reads all PDFs** in a given folder
- **Extracts text** using GROBID
- **Stores text elements** in SQLite3 database
- **Handles recursive chunks**
- **Embeds** text
- **Vectorizes** extracted data
- **Retrieval Methods**
  1. Standard Retrieval
  2. LangChain: MultiQueryRetriever
- **OpenAI-based chat** using LM Studio
- **Displays**:
  - Query
  - Prompt Information
  - Answer: Dashboard Browser Tab
- **Retrieval and QA chain** based chat using LM Studio
- **Displays** results in a new Browser Tab
## Installation & Usage
   - Additional information is within the Notebook, as some Markdown cells describe requirements and usage details.
### Prerequisites
1. **Install LM Studio**
   - Follow the official LM Studio installation guide for your operating system.
2. **Download LLM Model from Hugging Face**
   - You can download a pre-trained model from Hugging Face using the [Hugging Face Model Hub](https://huggingface.co/models). Follow the instructions on their site to use the desired model.
3. **Install Docker for GROBID**
   - Make sure Docker is installed on your machine. You can follow the installation instructions from the [Docker website](https://www.docker.com/get-started).
   - After installing Docker, pull the GROBID Docker image by running:
     ```bash
     docker pull lfoppiano/grobid
     ```
### Running the Notebook
1. Clone the repository.
2. Install the required dependencies.
3. Run the `PDFs_RAG_with_LMstudio.ipynb` notebook to begin processing your PDFs.
