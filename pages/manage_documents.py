import asyncio
from io import BytesIO
from itertools import chain
from os import getenv
import streamlit as st
import PyPDF2
from peewee import SQL, JOIN, NodeList
from cohere import Client
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel  # Pydantic validates and converts data into the types you expect, using Python classes

from db import DocumentInformationChunks, DocumentTags, Tags, db, Documents
from utils import find

# Cache the Cohere client to avoid reinitialization
@st.cache_resource
def get_cohere_client():
    """Initialize and cache Cohere client"""
    return Client(getenv("COHERE_API_KEY"))

# Cache the embedding model to avoid reloading
@st.cache_resource
def load_embedding_model():
    """Load and cache the embedding model"""
    return SentenceTransformer('all-MiniLM-L6-v2')

# Use cached resources
co = get_cohere_client()
model = load_embedding_model()

# Page header
st.markdown("# 📚 Manage Documents")
st.markdown("Upload PDF files and organize them with tags for easy searching.")

IDEAL_CHUNK_LENGTH = 2000

# That code defines two Pydantic models which guarantee that facts and tags will always be lists of strings, automatically validating and converting the data
class GeneratedDocumentInformationChunks(BaseModel):
    facts: list[str]

class GeneratedMatchingTags(BaseModel):
    tags: list[str]

def delete_document(document_id: int):
    Documents.delete().where(Documents.id == document_id).execute()


# This function takes a chunk of text from a PDF and uses an AI model to generate a list of short facts from it.
# It is asynchronous (async) so it can run many times at once without blocking other code.
async def generate_chunks(index: int, pdf_text_chunk: str):
    total_retries = 0  # This variable keeps track of how many times we've retried if something goes wrong
    while True:  # This loop will keep trying until it succeeds or fails too many times
        try:
            # Call the Cohere AI API to generate facts from the chunk of text
            response = co.chat(
                message=f"Create concise facts from this text:\n{pdf_text_chunk}",  
                model="command-r-plus"
            )
            # Get the generated text from the API response
            text = response.text
            # Split the text into a list of facts, one per line, and remove any empty lines or extra spaces
            facts = [fact.strip() for fact in text.split("\n") if fact.strip()]
            
            # If no facts were generated, use the original chunk
            if not facts:
                facts = [pdf_text_chunk]
            
            print(f"Generated {len(facts)} facts for chunk {index}.")
            return facts  
        except Exception as e:
            total_retries += 1  # Add 1 to the retry counter
            if total_retries > 5:  # If we've tried more than 5 times, give up and show the error
                raise e
            # Wait 1 second before trying again, so we don't overload the server
            await asyncio.sleep(1)
            print(f"Retrying chunk {index} due to {e}...")  


# Cache PDF text extraction to avoid re-processing
@st.cache_data
def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF with caching"""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        pdf_text = ""
        page_count = len(pdf_reader.pages)
        print(f"PDF has {page_count} pages")  # Debug
        
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            print(f"Page {page_num + 1}: {len(page_text)} characters extracted")  # Debug
            if len(page_text.strip()) == 0:
                print(f"WARNING: Page {page_num + 1} extracted no text!")  # Debug
            pdf_text += page_text + "\n\n"
        
        print(f"Total PDF text length: {len(pdf_text)} characters")  # Debug
        
        # Show a sample of the extracted text
        if len(pdf_text.strip()) > 0:
            sample = pdf_text[:500].replace('\n', ' ')
            print(f"Sample text: {sample}...")  # Debug
        else:
            print("ERROR: No text was extracted from the PDF!")  # Debug
            
        return pdf_text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")  # Debug
        return ""

# Cache tag lookup to avoid repeated database queries
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_tags():
    """Get all tags from database with caching"""
    tags_query = Tags.select()
    return [(tag.id, tag.name) for tag in tags_query]  # Keep original case

async def get_matching_tags(pdf_text: str):
    tags_data = get_all_tags()  # Use cached tags
    print(f"Available tags: {tags_data}")  # Debug
    
    if not tags_data:  
        print("No tags found in database")  # Debug
        return []
    
    tags = [tag_name for _, tag_name in tags_data]  # Extract tag names
    print(f"Tag names to match: {tags}")  # Debug
    total_retries = 0  # Counter for how many times we've retried
    
    while True:  # Keep trying until it works or fails too many times
        try:
            # Improved prompt with better instructions
            prompt = f"""You are a document categorization expert. From the following list of available tags, select ONLY the tags that are relevant to the content below. Return ONLY the exact tag names from the list, separated by commas, with no additional text.

Available tags: {tags}

Document content: {pdf_text[:2000]}

Return only the relevant tag names from the list above, separated by commas:"""
            
            print(f"Sending prompt to AI (first 200 chars): {prompt[:200]}...")  # Debug
            
            response = co.chat(
                message=prompt,
                model="command-r-plus"
            )
            
            print(f"AI response: '{response.text}'")  # Debug
            
            # Clean up the AI response
            response_text = response.text.strip()
            
            # The AI returns a string of tag names separated by commas
            tag_names = [name.strip().lower() for name in response_text.split(",") if name.strip()]
            print(f"Parsed tag names: {tag_names}")  # Debug
            
            tag_ids = []  # This will hold the IDs of the tags that match
            for name in tag_names:
                # For each tag name suggested by the AI, find the matching tag in the database (case-insensitive)
                matching_tag = next((tag_id for tag_id, tag_name in tags_data if tag_name.lower() == name.lower()), None)
                if matching_tag:
                    tag_ids.append(matching_tag)  # Add the tag's ID to the list
                    print(f"Found match: '{name}' -> ID {matching_tag}")  # Debug
                else:
                    print(f"No match found for: '{name}'")  # Debug
            
            print(f"Final tag IDs: {tag_ids}")  # Debug
            return tag_ids  
        except Exception as e:
            total_retries += 1
            if total_retries > 5:
                raise e
            await asyncio.sleep(1)  
            print(f"Retrying matching tags due to {e}...")


# This function handles the process of uploading a PDF, extracting its text, generating facts and tags, and saving everything to the database.
def upload_document(name: str, pdf_file: bytes):
    # Use cached PDF text extraction
    pdf_text = extract_pdf_text(pdf_file)
    print(f"Extracted PDF text length: {len(pdf_text)} characters")  # Debug
    
    # Split the PDF text into smaller chunks so the AI can process them (max 4000 characters each)
    pdf_text_chunks = [
        pdf_text[i:i+IDEAL_CHUNK_LENGTH]  # Take a slice of the text from i to i+IDEAL_CHUNK_LENGTH
        for i in range(0, len(pdf_text), IDEAL_CHUNK_LENGTH)  # Do this for every 4000 characters
    ]
    
    print(f"Created {len(pdf_text_chunks)} chunks")  # Debug
    for i, chunk in enumerate(pdf_text_chunks):
        print(f"Chunk {i}: {len(chunk)} characters")  # Debug

    # Set up a new asyncio event loop so we can run async functions from regular (non-async) code
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Create a list of tasks: one for each chunk (to generate facts), plus one to get matching tags for the whole document
        chunks_task = [generate_chunks(idx, chunk) for idx, chunk in enumerate(pdf_text_chunks)]
        # Only use the first 5000 characters of the PDF for tag generation (to save time and cost)
        gather_task = asyncio.gather(*chunks_task, get_matching_tags(pdf_text[:5000]))
        # Run all the tasks and wait for them to finish; get the results
        results = loop.run_until_complete(gather_task)
    finally:
        loop.close()  

    # Split the results: all but the last are document chunks, last is matching tag IDs
    document_chunks_lists = results[:-1]  # List of lists of facts
    matching_tag_ids = results[-1]        # List of tag IDs
    
    # Flatten the list of lists into a single list of facts
    document_chunks = []
    for chunk_list in document_chunks_lists:
        if isinstance(chunk_list, list):
            document_chunks.extend(chunk_list)
        else:
            # If it's not a list (shouldn't happen), treat it as a single chunk
            document_chunks.append(str(chunk_list))
    
    # Debug: Print what we're about to store
    print(f"About to store {len(document_chunks)} chunks")
    for i, chunk in enumerate(document_chunks[:3]):  # Print first 3 chunks
        print(f"Chunk {i}: {chunk[:100]}...")  # Print first 100 chars of each chunk

    # Save everything to the database in a single transaction (so it all succeeds or fails together)
    with db.atomic() as transaction:
        # Insert a new document record and get its ID
        document_id = Documents.insert(name=name).execute()
        # Insert all the facts (chunks) for this document, along with their AI-generated embeddings
        DocumentInformationChunks.insert_many([
            {
                "document_id": document_id,  # Link to the document
                "chunk": chunk,  # The chunk of text (fact)
                "embedding": model.encode(chunk).tolist()  # The AI embedding for this chunk (for searching later)
            }
            for chunk in document_chunks
        ]).execute()
        # Insert all the tags for this document
        if matching_tag_ids:  # Only insert if there are tags
            DocumentTags.insert_many([
                {"document_id": document_id, "tag_id": tag_id}
                for tag_id in matching_tag_ids
            ]).execute()
        transaction.commit()  # Commit the transaction to save everything
    # Print a summary for debugging
    print(f"Inserted {len(document_chunks)} facts for PDF {name} with {len(matching_tag_ids)} tags.")

@st.dialog("Upload document")
def upload_document_dialog_open():
    pdf_file = st.file_uploader("Upload PDF file", type="pdf")
    if pdf_file is not None:
        # Show file size and preview
        st.write(f"File size: {len(pdf_file.getvalue()) / 1024:.1f} KB")
        
        if st.button("Upload", key="upload-document-button"):
            with st.spinner("Processing PDF..."):
                try:
                    upload_document(pdf_file.name, pdf_file.getvalue())
                    st.success(f"Successfully uploaded {pdf_file.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to upload document: {e}")

st.button("Upload Document", key="upload-document-button", on_click=upload_document_dialog_open)

# Cache document listing to avoid repeated database queries
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_documents_with_tags():
    """Get all documents with their tags, cached"""
    query_result = Documents.select(
        Documents.id,  # The unique ID of the document
        Documents.name,  # The name of the document
        # This creates a list of tag names for each document, removing any NULLs (documents with no tags)
        NodeList([SQL('array_remove(array_agg('), Tags.name, SQL('), NULL)')]).alias("tags")
    ).join(DocumentTags, JOIN.LEFT_OUTER).join(Tags, JOIN.LEFT_OUTER).group_by(Documents.id)
    
    # Convert to a list of dictionaries to make it pickle-serializable
    documents_list = []
    for doc in query_result:
        documents_list.append({
            'id': doc.id,
            'name': doc.name,
            'tags': doc.tags if doc.tags else []
        })
    return documents_list

def delete_document(document_id: int):
    """Delete document and clear cache"""
    Documents.delete().where(Documents.id == document_id).execute()
    # Clear the cache so the document list updates
    get_documents_with_tags.clear()

# Query the database to get all documents, their IDs, names, and associated tags (if any)
documents = get_documents_with_tags()

# If there are any documents in the database, display them
if documents:
    for doc in documents:
        # Create a bordered container for each document (looks nice in Streamlit)
        container = st.container(border=True)
        # Show the document's name
        container.write(doc['name'])
        # If the document has any tags, display them as a comma-separated list
        if doc['tags']:
            container.write(f"Tags: {', '.join(doc['tags'])}")
        # Add a delete button for this document
        # The key ensures each button is unique, and the lambda calls delete_document with the document's ID
        if container.button("Delete", key=f"{doc['id']}-delete-button"):
            delete_document(doc['id'])
            st.rerun()
# If there are no documents, show an info message
else:
    st.info("No documents created yet!")