# pdfGPT - RAG Application

An AI-powered document interaction system that allows you to upload PDF documents and have intelligent conversations with their content using Retrieval-Augmented Generation (RAG).

## ✨ Features

- **Semantic Search**: AI embeddings for intelligent content discovery
- **Interactive Chat**: Natural language interface for querying documents
- **Document Management**: Upload, organize, and manage PDF documents
- **Smart Tagging**: AI-powered automatic tag suggestions
- **Vector Database**: PostgreSQL with pgvector for fast similarity search
- **Local Processing**: Embeddings generated locally for privacy

## 📋 Prerequisites

Before running this application, you need to have the following installed:

1. **Python 3.8 or higher**
2. **PostgreSQL with pgvector extension**
3. **Cohere API Key** (sign up at https://cohere.ai/)

## 🗄️ Database Setup

### 1. Install PostgreSQL

- Download and install PostgreSQL from https://www.postgresql.org/download/
- Make sure to remember your postgres user password

### 2. Install pgvector extension

```bash
# On Windows (using PostgreSQL installer)
# The pgvector extension should be available in newer PostgreSQL versions
# If not available, you can install it via:
# https://github.com/pgvector/pgvector#installation

# Connect to PostgreSQL and create the extension
psql -U postgres -d postgres
CREATE EXTENSION vector;
```

### 3. Create Database (Optional)

The application will use the default 'postgres' database, but you can create a dedicated one:

```sql
CREATE DATABASE pdfgpt;
CREATE EXTENSION vector;
```

## 🧩 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd pdfGPT
python -m venv venv
.\venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your credentials:

```env
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
COHERE_API_KEY=your_cohere_api_key
```

### 3. Run the Application

```bash
streamlit run Home.py
```

Visit http://localhost:8501 in your browser.

## 🛠️ Technical Details

- **Frontend**: Streamlit 
- **Backend**: Python with async processing
- **Database**: PostgreSQL with pgvector extension
- **AI**: Cohere API + local sentence-transformers
- **Embeddings**: all-MiniLM-L6-v2 (384 dimensions)

## 📂 File Structure

```
pdfGPT/
├── Home.py                     # Main application entry
├── db.py                       # Database models and setup
├── constants.py                # AI prompts and constants
├── utils.py                    # Utility functions
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── pages/
    ├── chat_with_documents.py  # Chat interface
    ├── manage_documents.py     # Document management
    └── manage_tags.py          # Tag management
```

## Made with 🧡 by zeeshan