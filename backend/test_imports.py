#!/usr/bin/env python3
"""
Test script to check if all imports work correctly
"""

def test_imports():
    try:
        print("Testing imports...")
        
        # Test basic imports
        print("✓ Testing basic imports...")
        import os
        import io
        import uuid
        from typing import List, Optional
        
        # Test FastAPI imports
        print("✓ Testing FastAPI imports...")
        from fastapi import FastAPI, File, UploadFile, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        
        # Test PDF processing
        print("✓ Testing PDF processing...")
        import PyPDF2
        
        # Test LangChain imports
        print("✓ Testing LangChain imports...")
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.chains import ConversationalRetrievalChain
        from langchain.memory import ConversationBufferMemory
        from langchain.prompts import PromptTemplate
        
        # Test embeddings
        print("✓ Testing embeddings...")
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        # Test vector store
        print("✓ Testing vector store...")
        from langchain_pinecone import PineconeVectorStore
        
        # Test Pinecone
        print("✓ Testing Pinecone...")
        from pinecone import Pinecone, ServerlessSpec
        
        # Test Gemini
        print("✓ Testing Gemini...")
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Test sentence transformers
        print("✓ Testing sentence transformers...")
        import sentence_transformers
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        return False

if __name__ == "__main__":
    test_imports()