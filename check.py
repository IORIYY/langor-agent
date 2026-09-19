import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

vs = Chroma(
    persist_directory="data/chroma_db",
    embedding_function=embeddings
)

for q in ["均衡电流异常怎么排查", "通讯中断怎么办", "绝缘告警处理"]:
    print(f"\n问题：{q}")
    for doc, score in vs.similarity_search_with_score(q, k=2):
        print(f"  [{score:.3f}] {doc.metadata['source']}")