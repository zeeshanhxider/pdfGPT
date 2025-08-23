from os import getenv
from dotenv import load_dotenv
from pgvector.peewee import VectorField
from peewee import PostgresqlDatabase, Model, TextField, ForeignKeyField   # peewee helps us to talk with postgres basically

# Load environment variables from .env file
load_dotenv()

# setting up the database
db = PostgresqlDatabase(
    getenv("DB_NAME"),
    user=getenv("DB_USER"),
    password=getenv("DB_PASSWORD"),
    host=getenv("DB_HOST"),
    port=getenv("DB_PORT"),
)

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

DocumentInformationChunks.add_index('embedding vector_cosine_ops', using='diskann')  # Adds an index on the embedding column (VectorField) using cosine similarity (vector_cosine_ops) with the DiskANN algorithm (using='diskann') to make semantic search fast even on millions of embeddings.

db.connect()
db.create_tables([Documents, Tags, DocumentTags, DocumentInformationChunks])

# both of those functions run raw SQL queries in Postgres
# add an index on the embedding column (VectorField) using cosine similarity (vector_cosine_ops) with the DiskANN algorithm (using='diskann') to make semantic search fast even on millions of embeddings.
def set_diskann_query_rescore(query_rescore: int):    
   db.execute_sql(
      "SET diskann.query_rescore = %s",
      (query_rescore,)
   )

# Tells Postgres (via pgai) which Cohere API key to use for embedding or AI queries for the current session
def set_cohere_api_key():
    db.execute_sql(
        "SELECT set_config('ai.cohere_api_key', %s, false)",
        (getenv("COHERE_API_KEY"),)
    )
