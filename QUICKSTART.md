# 🚀 Quick Start Guide - PDF ChatBot RAG Application

## Overview

This is a complete production-grade RAG (Retrieval-Augmented Generation) system that allows users to upload PDF documents and ask questions about their content using AI.

## What You Get

- ✅ **PDF Upload & Processing**: Drag-and-drop PDF upload with intelligent text extraction
- ✅ **AI-Powered Chat**: Ask questions and get accurate answers from your documents
- ✅ **Vector Search**: Fast semantic search using ChromaDB embeddings
- ✅ **Modern UI**: Beautiful Next.js interface with TailwindCSS
- ✅ **Production Ready**: Docker containerized with health checks and monitoring
- ✅ **Free to Use**: No external API costs required (local models included)

## 🏃‍♂️ One-Command Setup

### Windows

```cmd
setup.bat
```

### Linux/Mac

```bash
chmod +x setup.sh
./setup.sh
```

That's it! The script will:

1. Check prerequisites (Docker & Docker Compose)
2. Set up environment files
3. Build and start all services
4. Open your application at http://localhost:3000

## 📋 Prerequisites

- **Docker Desktop** (includes Docker Compose)
- **4GB+ RAM** (recommended for local AI models)
- **Internet connection** (for downloading models and dependencies)

### Install Docker Desktop

- **Windows/Mac**: Download from [docker.com](https://www.docker.com/products/docker-desktop)
- **Linux**: Follow [Docker installation guide](https://docs.docker.com/engine/install/)

## 🎯 Usage Instructions

### 1. Upload a PDF Document

- Open http://localhost:3000
- Drag and drop a PDF file (max 10MB)
- Wait for processing (usually 30-60 seconds)

### 2. Start Chatting

- Type questions about your document
- Get AI-powered answers with source citations
- See confidence scores for each response

### 3. Example Questions to Try

- "What is this document about?"
- "Summarize the main points"
- "What are the key findings?"
- "Who are the authors mentioned?"

## 🔧 Configuration Options

### Backend Settings (backend/.env)

```bash
# Use GPU for faster processing (if available)
EMBEDDING_DEVICE=cuda

# Increase chunk size for longer documents
CHUNK_SIZE=1500

# Use external API for better responses (optional)
OPENAI_API_KEY=your_key_here
```

### Frontend Settings (frontend/.env.local)

```bash
# Change API URL if deploying remotely
NEXT_PUBLIC_API_BASE_URL=http://your-domain:8000
```

## 🚀 Production Deployment

### Quick Production Deploy

```bash
# Linux/Mac
./deploy.sh your-domain.com production

# Windows
deploy.bat your-domain.com production
```

### Manual Production Steps

1. Update environment files for your domain
2. Set up reverse proxy (nginx/Apache)
3. Configure SSL certificates
4. Run with production compose file:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

## 📊 Monitoring & Management

### Health Checks

- **Backend**: http://localhost:8000/health
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

### Useful Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Update to latest
git pull
docker-compose up --build -d
```

### Monitor Performance

```bash
# Run monitoring script
./monitor.sh  # Linux/Mac
monitor.bat   # Windows
```

## 🛠️ Troubleshooting

### Common Issues

**Services won't start**

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs backend
docker-compose logs frontend
```

**Out of memory errors**

```bash
# Reduce model size in backend/.env
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
LOCAL_LLM_MODEL_NAME=gpt2
```

**Can't access the application**

```bash
# Check if ports are available
netstat -an | grep :3000
netstat -an | grep :8000

# Try different ports in docker-compose.yml
```

**PDF upload fails**

- Check file size (max 10MB)
- Ensure file is a valid PDF
- Check backend logs for errors

### Performance Tips

**For Better Speed:**

- Use GPU if available (`EMBEDDING_DEVICE=cuda`)
- Increase Docker memory allocation
- Use SSD storage for persistent volumes

**For Better Accuracy:**

- Use larger embedding models
- Add external API keys (OpenAI/Anthropic)
- Adjust chunk size and overlap

## 🔒 Security Considerations

### Production Security

- Change default passwords/secrets
- Set up proper CORS origins
- Use HTTPS with SSL certificates
- Implement rate limiting
- Regular security updates

### File Upload Security

- Files are validated (PDF only)
- Size limits enforced (10MB)
- Temporary files cleaned up
- No executable file processing

## 📈 Scaling Options

### Horizontal Scaling

- Use Docker Swarm or Kubernetes
- Separate ChromaDB service
- Load balancer for multiple instances

### Vertical Scaling

- Increase container memory/CPU
- Use faster storage (NVMe SSD)
- GPU acceleration for embeddings

## 🤝 Support & Help

### Getting Help

1. Check the logs first: `docker-compose logs`
2. Review the troubleshooting section
3. Check API documentation: http://localhost:8000/docs
4. Create an issue with logs and error details

### Resources

- **Full Documentation**: README.md
- **API Reference**: http://localhost:8000/docs
- **Health Status**: http://localhost:8000/status

## 🎉 What's Next?

After getting the basic system running, you can:

1. **Customize the UI**: Modify the frontend components
2. **Add New Features**: User authentication, document management
3. **Integrate External Services**: Cloud storage, advanced AI models
4. **Scale the Deployment**: Multi-server setup, load balancing
5. **Add Analytics**: Usage tracking, performance monitoring

## 📱 Mobile Access

The web interface is responsive and works on mobile devices. Simply access http://localhost:3000 from any device on your network.

## 🔄 Updates & Maintenance

### Updating the Application

```bash
# Get latest version
git pull

# Rebuild and restart
docker-compose up --build -d
```

### Backup Your Data

```bash
# Backup vector database and uploads
cp -r data/ backup-$(date +%Y%m%d)/
cp -r uploads/ backup-$(date +%Y%m%d)/
```

---

**🎯 Ready to Start?**

Run the setup script and you'll have a fully functional PDF ChatBot in minutes!

```bash
./setup.sh    # Linux/Mac
setup.bat     # Windows
```

Then visit http://localhost:3000 and start uploading documents!
