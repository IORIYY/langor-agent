import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

loader = DirectoryLoader("docs/sop", glob="**/*.md", loader_cls=TextLoader,
                         loader_kwargs={"encoding": "utf-8"})
docs = loader.load()
print(f"Loaded {len(docs)} docs")

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
chunks = splitter.split_documents(docs)
print(f"Split into {len(chunks)} chunks")

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)
vs = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_test")
print("Indexed.")

for q in ["均衡电流异常怎么排查", "通讯中断怎么办", "绝缘告警处理"]:
    print(f"\n问题：{q}")
    results = vs.similarity_search_with_score(q, k=2)
    for doc, score in results:
        print(f"  [{score:.3f}] {doc.metadata['source']}")
        print(f"  {doc.page_content[:80]}...")