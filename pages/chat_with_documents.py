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

# Load the same embedding model used for document processing
model = SentenceTransformer('all-MiniLM-L6-v2')
# Initialize Cohere client
co = Client(getenv("COHERE_API_KEY"))

st.set_page_config(page_title="Chat With Documents")
st.title("Chat With Documents")

class Message(TypedDict):
    role: Union[Literal["user"], Literal["assistant"]]
    content: str
    references: Optional[list[str]]

if "messages" not in st.session_state:
    st.session_state["messages"] = []
    
def push_message(message: Message):
    st.session_state["messages"] = [
        *st.session_state["messages"],
        message
    ]

async def send_message(input_message: str):
    related_document_information_chunks: list[str] = []
    
    # Generate embedding for the user's message using local model
    query_embedding = model.encode(input_message).tolist()
    
    with db.atomic() as transaction:
        set_diskann_query_rescore(100)
        # Convert embedding to string format that PostgreSQL can understand
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        result = DocumentInformationChunks.select().order_by(
            SQL("embedding <-> %s::vector", (embedding_str,))
        ).limit(5).execute()
        for row in result:
            related_document_information_chunks.append(row.chunk)
        transaction.commit()
    push_message({
        "role": "user",
        "content": input_message,
        "references": related_document_information_chunks
    })
    total_retries = 0
    while True:
        try:
            # Prepare knowledge context
            knowledge_context = RESPOND_TO_MESSAGE_SYSTEM_PROMPT.replace("{{knowledge}}", "\n".join([
                f"{index + 1}. {chunk}"
                for index, chunk in enumerate(related_document_information_chunks)
            ]))
            
            # Get the current user message (last message in the session)
            current_message = st.session_state["messages"][-1]["content"]
            
            # Call Cohere API directly instead of using pgai
            response = co.chat(
                model="command-r-plus",
                message=current_message,
                preamble=knowledge_context
            )
            
            if not response.text:
                break
            push_message({
                "role": "assistant",
                "content": response.text,
                "references": None
            })
            print(f"Generated response: {response.text}")
            break
        except Exception as e:
            total_retries += 1
            if total_retries > 5:
                raise e
            await sleep(1)
            print(f"Failed to generate response with this err: {e}. Retrying...")
    st.rerun()

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["references"]:
            with st.expander("References"):
                for reference in message["references"]:
                    st.write(reference)
input_message = st.chat_input("Say something")
if input_message:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_until_complete(send_message(input_message))
    event_loop.close()