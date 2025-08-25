import asyncio
from typing import Literal, Optional, TypedDict, Union
from anyio import sleep
from os import getenv
import streamlit as st
from sentence_transformers import SentenceTransformer
from cohere import Client
from constants import RESPOND_TO_MESSAGE_SYSTEM_PROMPT
from db import DocumentInformationChunks, set_diskann_query_rescore, set_cohere_api_key, db
from peewee import SQL

# Cache the embedding model to avoid reloading on every page switch
@st.cache_resource
def load_embedding_model():
    """Load and cache the embedding model"""
    return SentenceTransformer('all-MiniLM-L6-v2')

# Cache the Cohere client
@st.cache_resource
def get_cohere_client():
    """Initialize and cache Cohere client"""
    api_key = getenv("COHERE_API_KEY")
    if not api_key:
        st.error("COHERE_API_KEY environment variable not set!")
        st.stop()
    return Client(api_key)

# Use cached resources
model = load_embedding_model()
co = get_cohere_client()

# Page header
st.markdown("# 💬 Chat With Documents")
st.markdown("Ask questions about your uploaded documents and get AI-powered answers.")

class Message(TypedDict):
    role: Union[Literal["user"], Literal["assistant"]]
    content: str
    references: Optional[list[str]]

# Initialize session state more efficiently
if "messages" not in st.session_state:
    st.session_state.messages = []

def push_message(message: Message):
    st.session_state.messages.append(message)

@st.cache_data(ttl=300)  # Cache embeddings for 5 minutes
def get_query_embedding(text: str):
    """Generate and cache embeddings for queries"""
    return model.encode(text).tolist()

@st.cache_data(ttl=600)  # Cache search results for 10 minutes
def search_related_chunks(query_embedding: list[float], limit: int = 5):
    """Search for related document chunks with caching"""
    related_chunks = []
    
    try:
        with db.atomic() as transaction:
            set_diskann_query_rescore(100)
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            result = DocumentInformationChunks.select().order_by(
                SQL("embedding <-> %s::vector", (embedding_str,))
            ).limit(limit).execute()
            
            for row in result:
                related_chunks.append(row.chunk)
            transaction.commit()
    except Exception as e:
        st.error(f"Error searching documents: {e}")
        
    return related_chunks

async def send_message(input_message: str):
    # Use cached embedding generation
    query_embedding = get_query_embedding(input_message)
    
    # Use cached search
    related_document_information_chunks = search_related_chunks(query_embedding)
    
    push_message({
        "role": "user",
        "content": input_message,
        "references": related_document_information_chunks
    })
    
    # Show a spinner while generating response
    with st.spinner("Generating response..."):
        total_retries = 0
        while True:
            try:
                # Prepare knowledge context
                knowledge_context = RESPOND_TO_MESSAGE_SYSTEM_PROMPT.replace("{{knowledge}}", "\n".join([
                    f"{index + 1}. {chunk}"
                    for index, chunk in enumerate(related_document_information_chunks)
                ]))
                
                # Get the current user message
                current_message = st.session_state.messages[-1]["content"]
                
                # Call Cohere API
                response = co.chat(
                    model="command-r-plus",
                    message=current_message,
                    preamble=knowledge_context
                )
                
                if response.text:
                    push_message({
                        "role": "assistant",
                        "content": response.text,
                        "references": None
                    })
                    print(f"Generated response: {response.text}")
                    break
                else:
                    st.error("No response generated")
                    break
                    
            except Exception as e:
                total_retries += 1
                if total_retries > 5:
                    st.error(f"Failed to generate response after 5 retries: {e}")
                    break
                await sleep(1)
                print(f"Failed to generate response with error: {e}. Retrying...")

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["references"]:
                with st.expander("References"):
                    for reference in message["references"]:
                        st.write(reference)

# Handle user input
if input_message := st.chat_input("Say something"):
    # Use existing event loop if available, otherwise create new one
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new thread for the async operation
            import threading
            import concurrent.futures
            
            def run_async():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(send_message(input_message))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(run_async)
        else:
            loop.run_until_complete(send_message(input_message))
    except RuntimeError:
        # No event loop exists, create a new one
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            event_loop.run_until_complete(send_message(input_message))
        finally:
            event_loop.close()
    
    st.rerun()