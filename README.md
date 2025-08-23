# PDF GPT - RAG Application Setup Guide

## Prerequisites

Before running this application, you need to have the following installed:

1. **Python 3.8 or higher**
2. **PostgreSQL with pgvector extension**
3. **Cohere API Key** (sign up at https://cohere.ai/)

## Database Setup

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

## Application Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Update the `.env` file with your credentials:

```
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
COHERE_API_KEY=your_cohere_api_key
```

### 3. Additional Windows Dependencies

For PDF processing on Windows, you may need to install poppler:

```bash
# Download poppler for Windows from:
# https://github.com/oschwartz10612/poppler-windows/releases
# Extract and add the 'bin' folder to your PATH environment variable
```

## Running the Application

### 1. Start the Streamlit Application

```bash
streamlit run Home.py
```

### 2. Access the Application

Open your web browser and go to: http://localhost:8501

## Usage Guide

### Step 1: Create Tags

1. Go to "Manage Tags" page
2. Create relevant tags for your documents (e.g., "Research", "Legal", "Technical")

### Step 2: Upload Documents

1. Go to "Manage Documents" page
2. Click "Upload Document"
3. Select a PDF file and upload it
4. The system will automatically:
   - Extract text from the PDF
   - Generate embeddings for semantic search
   - Suggest relevant tags
   - Store everything in the database

### Step 3: Chat with Documents

1. Go to "Chat With Documents" page
2. Ask questions about your uploaded documents
3. The AI will search through your documents and provide answers based on the content

## Troubleshooting

### Common Issues:

1. **Database Connection Error**

   - Ensure PostgreSQL is running
   - Check your database credentials in `.env`
   - Verify the pgvector extension is installed

2. **PDF Processing Error**

   - Install poppler-utils (see setup instructions above)
   - Ensure the PDF is not password-protected

3. **Cohere API Error**

   - Verify your API key is correct in `.env`
   - Check your Cohere API usage limits

4. **Import Errors**
   - Run `pip install -r requirements.txt`
   - Ensure you're using Python 3.8+

### Performance Tips:

- For better performance with large documents, consider chunking them into smaller pieces
- The embedding model (all-MiniLM-L6-v2) provides a good balance of speed and accuracy
- Increase `diskann.query_rescore` for better search accuracy at the cost of speed

## Features

- **Semantic Search**: Uses AI embeddings to find relevant content across documents
- **Vector Database**: PostgreSQL with pgvector for efficient similarity search
- **Smart Chunking**: Automatically breaks down documents into meaningful pieces
- **AI-Powered Tagging**: Automatically suggests relevant tags for documents
- **Interactive Chat**: Natural language interface for querying documents
- **Document Management**: Upload, view, and organize PDF documents
- **Tag Organization**: Create and manage tags for categorizing documents
