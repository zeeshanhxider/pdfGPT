# AI Document Chatbot

A full-stack AI-powered document chatbot built with LangChain, FastAPI, and React. Upload PDF or text documents and ask natural language questions about their content using Retrieval-Augmented Generation (RAG).

## Features

### Backend
- ✅ Extract text from PDF and text files
- ✅ Generate embeddings using HuggingFace Sentence Transformers
- ✅ Store embeddings in Pinecone vector database for fast retrieval
- ✅ Retrieval-Augmented Generation (RAG) using LangChain and Google Gemini API
- ✅ Conversation history support for contextual responses
- ✅ Source references for transparency

### Frontend
- ✅ Clean, modern chat interface
- ✅ Multiple document upload support
- ✅ Real-time chat with AI
- ✅ Source references display
- ✅ Conversation history tracking
- ✅ Responsive design

## Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- LangChain - LLM orchestration framework
- Google Gemini API - Large Language Model
- HuggingFace Sentence Transformers - Text embeddings
- Pinecone - Vector database
- PyPDF2 - PDF text extraction

**Frontend:**
- React - UI library
- Vite - Build tool
- Axios - HTTP client

## Prerequisites

- Python 3.8+
- Node.js 16+
- Pinecone account ([sign up here](https://www.pinecone.io/))
- Google Gemini API key ([get one here](https://ai.google.dev/))

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd pdfGPT
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `backend/.env` and add your API keys:

```env
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=document-chatbot
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

## Running the Application

### 1. Start the Backend

```bash
cd backend
# Make sure virtual environment is activated
python main.py
```

The backend will run on `http://localhost:8000`

### 2. Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. **Upload Documents**
   - Click "Choose Files" in the sidebar
   - Select one or more PDF or TXT files
   - Wait for the upload to complete

2. **Ask Questions**
   - Type your question in the input field at the bottom
   - Press Enter or click "Send"
   - The AI will answer based on the uploaded documents
   - View source references by expanding the "Sources" section

3. **Clear Documents**
   - Click "Clear All Documents" to remove all uploaded files from the vector database

## API Endpoints

### `POST /api/upload`
Upload one or more documents (PDF or text files)

**Request:** Multipart form data with files

**Response:**
```json
{
  "message": "Successfully processed 2 document(s)",
  "documents": [
    {
      "filename": "example.pdf",
      "chunks": 15,
      "total_characters": 12500
    }
  ]
}
```

### `POST /api/chat`
Ask a question about uploaded documents

**Request:**
```json
{
  "question": "What is this document about?",
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

**Response:**
```json
{
  "answer": "The document is about...",
  "sources": [
    {
      "filename": "example.pdf",
      "chunk_id": 2,
      "content": "Relevant excerpt..."
    }
  ]
}
```

### `DELETE /api/documents`
Clear all documents from the vector database

### `GET /api/health`
Health check endpoint

## Configuration

### Embedding Model
The default embedding model is `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). You can change this in `backend/services/document_service.py`.

### Chunk Size
Documents are split into chunks of 1000 characters with 200 character overlap. Adjust in `backend/services/document_service.py`:

```python
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
```

### Retrieval Settings
The system retrieves the top 4 most relevant chunks. Adjust in `backend/services/chat_service.py`:

```python
retriever = self.vector_store.as_retriever(
    search_kwargs={"k": 4}
)
```

## Architecture

```
┌─────────────┐
│   React     │
│  Frontend   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│   FastAPI   │
│   Backend   │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌────────────┐  ┌──────────┐
│  Pinecone  │  │  Gemini  │
│   Vector   │  │   API    │
│   Store    │  │   LLM    │
└────────────┘  └──────────┘
```

## How It Works

1. **Document Upload:** PDFs and text files are uploaded and text is extracted
2. **Text Chunking:** Documents are split into overlapping chunks
3. **Embedding:** Each chunk is converted to a 384-dimensional vector using HuggingFace embeddings
4. **Storage:** Embeddings are stored in Pinecone with metadata (filename, chunk ID)
5. **Question:** User asks a question
6. **Retrieval:** Question is embedded and similar chunks are retrieved from Pinecone
7. **Generation:** Retrieved chunks + question + conversation history are sent to Gemini
8. **Response:** AI generates an answer based on the context

## Troubleshooting

### "PINECONE_API_KEY environment variable is not set"
Make sure you've created a `.env` file in the `backend` directory with your API keys.

### "Error uploading files"
- Check that files are PDF or TXT format
- Ensure Pinecone index is created (may take a minute on first run)
- Check backend logs for detailed error messages

### "Sorry, I encountered an error"
- Ensure backend is running on port 8000
- Check that you've uploaded documents before asking questions
- Verify your Gemini API key is valid

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

