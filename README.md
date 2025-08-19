# PDF ChatBot - RAG Application

A production-grade web application that allows users to upload PDF documents and ask questions about their content using Retrieval-Augmented Generation (RAG) powered by ChromaDB, HuggingFace embeddings, and language models.

## 🚀 Features

- **PDF Upload & Processing**: Upload PDF documents up to 10MB
- **Intelligent Text Extraction**: Uses pdfplumber and PyPDF2 for robust text extraction
- **Vector Search**: ChromaDB for efficient semantic search
- **RAG Pipeline**: Retrieval-Augmented Generation for accurate, context-aware answers
- **Modern UI**: Next.js with TailwindCSS and shadcn/ui components
- **Real-time Chat**: Interactive chat interface with confidence scores and source citations
- **Docker Support**: Fully containerized for easy deployment
- **API Documentation**: Automatic FastAPI documentation
- **Persistent Storage**: Vector embeddings and documents are persisted

## 🏗️ Architecture

### Backend (FastAPI)

- **Framework**: FastAPI for high-performance async API
- **PDF Processing**: pdfplumber + PyPDF2 for text extraction
- **Embeddings**: HuggingFace SentenceTransformers (all-MiniLM-L6-v2)
- **Vector Database**: ChromaDB for similarity search
- **LLM**: Local HuggingFace models with external API support (OpenAI/Anthropic)
- **Logging**: Structured logging with structlog

### Frontend (Next.js)

- **Framework**: Next.js 14 with TypeScript
- **Styling**: TailwindCSS + shadcn/ui components
- **File Upload**: react-dropzone for drag-and-drop uploads
- **State Management**: React hooks
- **API Client**: Axios for HTTP requests

### Infrastructure

- **Containerization**: Docker & docker-compose
- **Storage**: Persistent volumes for data and uploads
- **Networking**: Internal docker network
- **Health Checks**: Built-in health monitoring

## 📋 Prerequisites

- Docker and Docker Compose
- Git
- (Optional) Node.js 18+ and Python 3.11+ for local development

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pdfGPT
```

### 2. Environment Setup

Copy environment files:

```bash
# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.local.example frontend/.env.local
```

### 3. Docker Deployment (Recommended)

```bash
# Build and run all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

This will start:

- Backend API at http://localhost:8000
- Frontend at http://localhost:3000
- API Documentation at http://localhost:8000/docs

### 4. Access the Application

Open your browser and navigate to:

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🛠️ Local Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Run the development server
npm run dev
```

## 📁 Project Structure

```
pdfGPT/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Configuration and logging
│   │   ├── models/        # Pydantic models
│   │   └── services/      # Business logic services
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities and API client
│   │   └── types/         # TypeScript definitions
│   ├── Dockerfile
│   ├── package.json
│   └── .env.local.example
├── data/                  # Persistent data (created at runtime)
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

### Backend Configuration (.env)

```bash
# App settings
APP_NAME=PDF ChatBot RAG
DEBUG=false
VERSION=1.0.0

# Server settings
HOST=0.0.0.0
PORT=8000

# File upload settings
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./uploads

# ChromaDB settings
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_COLLECTION_NAME=pdf_documents

# Model settings
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
USE_LOCAL_LLM=true
LOCAL_LLM_MODEL_NAME=microsoft/DialoGPT-medium

# Text processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=5
SIMILARITY_THRESHOLD=0.7

# External APIs (optional)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Frontend Configuration (.env.local)

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## 📚 API Documentation

### Endpoints

- **POST /api/v1/upload** - Upload PDF document
- **POST /api/v1/chat** - Send chat message
- **GET /api/v1/health** - Health check
- **GET /api/v1/status** - System status
- **DELETE /api/v1/documents/{id}** - Delete document

### Example API Usage

```bash
# Upload PDF
curl -X POST \
  http://localhost:8000/api/v1/upload \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@document.pdf'

# Send chat message
curl -X POST \
  http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "What is this document about?",
    "document_id": "document_id_here",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

## 🚀 Production Deployment

### Docker Production

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or use environment-specific compose files
docker-compose --env-file .env.prod up -d
```

### Environment Variables for Production

```bash
# Backend
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
EMBEDDING_DEVICE=cuda  # If GPU available

# Frontend
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
```

### Deployment Options

1. **Docker Swarm**
2. **Kubernetes**
3. **Cloud Platforms** (AWS ECS, Google Cloud Run, etc.)
4. **VPS with Docker Compose**

## 🔍 Monitoring & Logging

### Health Checks

- Backend: `GET /health`
- Docker: Built-in health checks
- Logs: Structured JSON logging

### Performance Monitoring

- Response times logged
- Embedding generation times
- File processing metrics
- Vector search performance

## 🛡️ Security Considerations

- File type validation (PDF only)
- File size limits (10MB max)
- Input sanitization
- CORS configuration
- Environment variable security
- Docker security best practices

## 🐛 Troubleshooting

### Common Issues

1. **Memory Issues**: Reduce chunk size or use smaller models
2. **CUDA Issues**: Set `EMBEDDING_DEVICE=cpu` if no GPU
3. **File Upload Fails**: Check file size and format
4. **Vector Search Slow**: Ensure ChromaDB persistence is working
5. **API Connection Issues**: Verify CORS settings

### Debug Mode

```bash
# Enable debug mode
echo "DEBUG=true" >> backend/.env
docker-compose restart backend
```

### Logs

```bash
# View logs
docker-compose logs backend
docker-compose logs frontend

# Follow logs
docker-compose logs -f backend
```

## 🔄 Updates & Maintenance

### Updating Dependencies

```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

### Model Updates

To use different embedding or language models, update the configuration:

```bash
# For better performance (if you have GPU)
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DEVICE=cuda

# For different LLM
LOCAL_LLM_MODEL_NAME=microsoft/DialoGPT-large
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Create an issue for bug reports
- Check the documentation at `/docs` endpoint
- Review the API documentation at `/docs`

## 🔮 Future Enhancements

- [ ] Multi-document support
- [ ] User authentication
- [ ] Document management dashboard
- [ ] Advanced search filters
- [ ] Export chat history
- [ ] Multiple language support
- [ ] Voice input/output
- [ ] Integration with cloud storage
- [ ] Advanced analytics dashboard
- [ ] Batch processing capabilities
