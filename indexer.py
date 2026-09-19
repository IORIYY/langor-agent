import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ============ 配置 ============
DOCS_DIR = "docs"
PERSIST_DIR = "data/chroma_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

# ============ 1. 加载文档 ============
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

# ============ 2. 切分 ============
print("\nStep 2: splitting...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
)
chunks = splitter.split_documents(documents)
print(f"Split into {len(chunks)} chunks")

# ============ 3. 嵌入 ============
print("\nStep 3: loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# ============ 4. 写入 Chroma ============
print("\nStep 4: writing to Chroma...")
if os.path.exists(PERSIST_DIR):
    import shutil
    shutil.rmtree(PERSIST_DIR)
    print(f"Removed old {PERSIST_DIR}")

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=PERSIST_DIR
)
print(f"Done. Saved to {PERSIST_DIR}, total {len(chunks)} chunks")