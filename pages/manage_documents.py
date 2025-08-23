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

st.set_page_config(page_title="Manage Documents")
st.title("Manage Documents")

# Initialize Cohere client and model
COHERE_API_KEY = getenv("COHERE_API_KEY")
co = Client(COHERE_API_KEY)
model = SentenceTransformer('all-MiniLM-L6-v2')

IDEAL_CHUNK_LENGTH = 4000

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


async def get_matching_tags(pdf_text: str):
    tags_result = Tags.select()  # Get all tags from the database
    tags = [tag.name.lower() for tag in tags_result]  # Make a list of tag names in lowercase
    if not tags:  
        return []
    
    total_retries = 0  # Counter for how many times we've retried
    
    while True:  # Keep trying until it works or fails too many times
        try:
            # Ask the AI to pick the best tags for the document from the list of all tags
            response = co.chat(
                message=f"Choose matching tags from this list {tags} for this text:\n{pdf_text}",
                model="command-r-plus"
            )
            # The AI returns a string of tag names separated by commas (like "science, ai, pdf")
            tag_names = [name.strip() for name in response.text.split(",") if name.strip()]
            tag_ids = []  # This will hold the IDs of the tags that match
            for name in tag_names:
                # For each tag name suggested by the AI, find the matching tag in the database (case-insensitive)
                matching_tag = find(lambda tag: tag.name.lower() == name.lower(), tags_result)
                if matching_tag:
                    tag_ids.append(matching_tag.id)  # Add the tag's ID to the list
            print(f"Generated matching tags {tag_names}.")  
            return tag_ids  
        except Exception as e:
            total_retries += 1
            if total_retries > 5:
                raise e
            await asyncio.sleep(1)  
            print(f"Retrying matching tags due to {e}...")


# This function handles the process of uploading a PDF, extracting its text, generating facts and tags, and saving everything to the database.
def upload_document(name: str, pdf_file: bytes):
    # Read the PDF file into memory and extract its text using PyPDF2
    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file))  # Convert the PDF file bytes into a PDF reader object
    pdf_text = ""
    for page in pdf_reader.pages:
        pdf_text += page.extract_text() + "\n\n"  # Extract text from each page and join with double newlines
    
    # Split the PDF text into smaller chunks so the AI can process them (max 4000 characters each)
    pdf_text_chunks = [
        pdf_text[i:i+IDEAL_CHUNK_LENGTH]  # Take a slice of the text from i to i+IDEAL_CHUNK_LENGTH
        for i in range(0, len(pdf_text), IDEAL_CHUNK_LENGTH)  # Do this for every 4000 characters
    ]

    # Set up a new asyncio event loop so we can run async functions from regular (non-async) code
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Create a list of tasks: one for each chunk (to generate facts), plus one to get matching tags for the whole document
    chunks_task = [generate_chunks(idx, chunk) for idx, chunk in enumerate(pdf_text_chunks)]
    # Only use the first 5000 characters of the PDF for tag generation (to save time and cost)
    gather_task = asyncio.gather(*chunks_task, get_matching_tags(pdf_text[:5000]))
    # Run all the tasks and wait for them to finish; get the results
    results = loop.run_until_complete(gather_task)
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
        if st.button("Upload", key="upload-document-button"):
            upload_document(pdf_file.name, pdf_file.getvalue())
            st.rerun()

st.button("Upload Document", key="upload-document-button", on_click=upload_document_dialog_open)


# Query the database to get all documents, their IDs, names, and associated tags (if any)
documents = Documents.select(
    Documents.id,  # The unique ID of the document
    Documents.name,  # The name of the document
    # This creates a list of tag names for each document, removing any NULLs (documents with no tags)
    NodeList([SQL('array_remove(array_agg('), Tags.name, SQL('), NULL)')]).alias("tags")
).join(DocumentTags, JOIN.LEFT_OUTER).join(Tags, JOIN.LEFT_OUTER).group_by(Documents.id).execute()

# If there are any documents in the database, display them
if documents:
    for doc in documents:
        # Create a bordered container for each document (looks nice in Streamlit)
        container = st.container(border=True)
        # Show the document's name
        container.write(doc.name)
        # If the document has any tags, display them as a comma-separated list
        if doc.tags:
            container.write(f"Tags: {', '.join(doc.tags)}")
        # Add a delete button for this document
        # The key ensures each button is unique, and the lambda calls delete_document with the document's ID
        container.button("Delete", key=f"{doc.id}-delete-button", on_click=lambda: delete_document(doc.id))
# If there are no documents, show an info message
else:
    st.info("No documents created yet!")