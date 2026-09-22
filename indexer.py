import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import shutil

DOCS_DIR = "docs/sop"
PERSIST_DIR = "data/chroma_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

print("Step 1: loading docs...")
loader = DirectoryLoader(
    DOCS_DIR,
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"}
)
documents = loader.load()
print(f"Loaded {len(documents)} documents")
for doc in documents:
    print(f"  - {doc.metadata.get('source', 'unknown')}")

print("\nStep 2: splitting...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
)
chunks = splitter.split_documents(documents)
print(f"Split into {len(chunks)} chunks")

print("\nStep 3: loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

print("\nStep 4: writing to Chroma...")
if os.path.exists(PERSIST_DIR):
    shutil.rmtree(PERSIST_DIR)
    print(f"Removed old {PERSIST_DIR}")

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=PERSIST_DIR
)
print(f"Done. Saved to {PERSIST_DIR}, total {len(chunks)} chunks")