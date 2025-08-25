from os import getenv
from dotenv import load_dotenv
from pgvector.peewee import VectorField
from peewee import PostgresqlDatabase, Model, TextField, ForeignKeyField   # peewee helps us to talk with postgres basically
import streamlit as st
from contextlib import contextmanager

# Load environment variables from .env file
load_dotenv()

# Cache database connection to avoid reconnecting on every page switch
@st.cache_resource
def get_database_connection():
    """Create and cache database connection"""
    return PostgresqlDatabase(
        getenv("DB_NAME"),
        user=getenv("DB_USER"),
        password=getenv("DB_PASSWORD"),
        host=getenv("DB_HOST"),
        port=getenv("DB_PORT"),
        # Add connection options that are supported by psycopg2
        autocommit=False,  # Changed to False for better transaction control
        autorollback=True,
    )

# Context manager for database operations
@contextmanager
def db_connection():
    """Context manager for database operations"""
    connection = None
    try:
        if db.is_closed():
            db.connect()
        yield db
    except Exception as e:
        if not db.is_closed():
            db.rollback()
        raise e
    finally:
        # Don't close the connection as it's cached
        pass

db = get_database_connection()

# making tables
class Documents(Model):
   name = TextField()     # creates a name which is a text field for the document
   class Meta:            # meta data for the documents table
      database = db
      db_table = 'documents'

class Tags(Model):
   name = TextField()
   class Meta:
      database = db
      db_table = 'tags'
      
class DocumentTags(Model):
   document_id = ForeignKeyField(Documents, backref="document_tags", on_delete='CASCADE')     #ForeignKeyField lets DocumentTags access ids from Documents class and onDelete='cascade' means if a document is deleted, all its tags will be deleted as well
   tag_id = ForeignKeyField(Tags, backref="document_tags", on_delete='CASCADE')
   class Meta:                  
      database = db
      db_table = 'document_tags'

class DocumentInformationChunks(Model):
   document_id = ForeignKeyField(Documents, backref="document_information_chunks", on_delete='CASCADE')
   chunk = TextField()
   embedding = VectorField(dimensions=384)  # 384-dimensional embedding vector
   class Meta:
      database = db
      db_table = 'document_information_chunks'

# Connect to database with error handling
try:
    db.connect()
    # Create tables only if they don't exist (for better performance)
    db.create_tables([Documents, Tags, DocumentTags, DocumentInformationChunks], safe=True)
    print("Database connection established successfully")
except Exception as e:
    print(f"Database connection or table creation error: {e}")
    # Don't raise the error here to allow the app to continue

# Create vector index for similarity search using HNSW (more widely supported than diskann)
try:
    db.execute_sql("""
        CREATE INDEX IF NOT EXISTS document_information_chunks_embedding_idx 
        ON document_information_chunks 
        USING hnsw (embedding vector_cosine_ops)
    """)
except Exception as e:
    print(f"Could not create vector index (this is normal for first run): {e}")

# both of those functions run raw SQL queries in Postgres
def set_diskann_query_rescore(query_rescore: int):    
    # This function is kept for compatibility but diskann settings may not be available
    try:
        with db_connection() as database:
            database.execute_sql(
                "SET diskann.query_rescore = %s",
                (query_rescore,)
            )
    except Exception as e:
        print(f"diskann not available, using default settings: {e}")

# Tells Postgres (via pgai) which Cohere API key to use for embedding or AI queries for the current session
def set_cohere_api_key():
    try:
        with db_connection() as database:
            database.execute_sql(
                "SELECT set_config('ai.cohere_api_key', %s, false)",
                (getenv("COHERE_API_KEY"),)
            )
    except Exception as e:
        print(f"Could not set Cohere API key: {e}")
