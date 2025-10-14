import os
import sys
import ast
import pandas as pd
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


#  Ensure live logging (so Flask UI shows logs progressively)
sys.stdout.reconfigure(line_buffering=True)


#  Load environment variables
print(" Loading environment variables...")
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    print(" Missing Pinecone API key in .env file.")
    sys.exit(1)


#  Connect to Pinecone
print(" Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "reddit-insights"


#  Load dataset
DATA_PATH = "reddit_data_sentiment.csv"
if not os.path.exists(DATA_PATH):
    print(f" File not found: {DATA_PATH}")
    sys.exit(1)

df = pd.read_csv(DATA_PATH)
print(f" Loaded dataset with {len(df)} rows.")


#  Convert rows to LangChain Documents
print(" Preparing documents...")

docs = []
for _, row in df.iterrows():
    text = str(row.get("clean_text", "")).strip()
    if not text or text.lower() == "nan":
        continue

    # Safe keyword parsing
    keywords = []
    if isinstance(row.get("keywords_found"), str):
        try:
            keywords = ast.literal_eval(row["keywords_found"])
        except (ValueError, SyntaxError):
            keywords = [row["keywords_found"]]

    metadata = {
        "id": row.get("id", ""),
        "category": row.get("category", ""),
        "subreddit": row.get("subreddit", ""),
        "keywords": ", ".join(keywords) if keywords else "",
        "sentiment": row.get("sentiment", ""),
    }

    docs.append(Document(page_content=text, metadata=metadata))

print(f" Prepared {len(docs)} documents.")


#  Split into Chunks
print(" Splitting documents into smaller chunks...")
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=80)
doc_chunks = splitter.split_documents(docs)
print(f" After splitting: {len(doc_chunks)} total chunks ready for embedding.")


#  Embeddings Setup
print(" Initializing embedding model (MiniLM)...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")


#  Create Pinecone Index if not exists
existing_indexes = [i["name"] for i in pc.list_indexes()]
if index_name not in existing_indexes:
    print(f" Creating new Pinecone index: {index_name} ...")
    pc.create_index(
        name=index_name,
        dimension=768,  # MiniLM vector dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    print(" Index created successfully!")
else:
    print(f" Index '{index_name}' already exists. Using existing index.")


#  Upload to Pinecone
print(" Uploading embeddings to Pinecone...")
vectorstore = PineconeVectorStore.from_documents(
    documents=doc_chunks,
    index_name=index_name,
    embedding=embeddings,
)

print(" Uploaded all embeddings to Pinecone successfully.")
print(" Indexing complete and ready for chatbot use.")
