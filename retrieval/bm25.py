import os
import jieba
from rank_bm25 import BM25Okapi
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


DOCS_DIR = "docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

# 工业术语自定义词典
CUSTOM_WORDS = [
    "均衡电流", "均衡模块", "均衡阈值", "均衡周期",
    "通讯中断", "通讯参数", "通讯线", "终端电阻",
    "绝缘告警", "绝缘电阻", "绝缘老化",
    "输出电压", "输出电流",
    "直流屏", "放电设备", "并网放电",
    "RS485", "Modbus", "告警码",
    "前置条件", "排查步骤", "常见根因",
]

# 全局缓存
_bm25_index = None
_chunks = None


def _init_jieba():
    """加载自定义词典"""
    for w in CUSTOM_WORDS:
        jieba.add_word(w)


def _tokenize(text: str) -> list:
    """中文分词，用 jieba"""
    return list(jieba.cut(text))


def _load_chunks():
    """加载并切分文档"""
    loader = DirectoryLoader(
        DOCS_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
    )
    return splitter.split_documents(documents)


def _get_index():
    """延迟加载 BM25 索引"""
    global _bm25_index, _chunks
    if _bm25_index is None:
        _init_jieba()
        _chunks = _load_chunks()
        corpus = [_tokenize(c.page_content) for c in _chunks]
        _bm25_index = BM25Okapi(corpus)
    return _bm25_index, _chunks


def bm25_search(query: str, top_k: int = 3) -> list:
    """
    BM25 关键词检索。

    返回格式：
    [
        {"content": "...", "source": "...", "score": 1.23},
        ...
    ]
    """
    index, chunks = _get_index()
    tokens = _tokenize(query)
    scores = index.get_scores(tokens)

    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: -x[1])
    top = indexed[:top_k]

    results = []
    for idx, score in top:
        if score <= 0:
            continue
        chunk = chunks[idx]
        results.append({
            "content": chunk.page_content,
            "source": chunk.metadata.get("source", "unknown"),
            "score": float(score)
        })
    return results


if __name__ == "__main__":
    for q in ["均衡电流异常", "通讯中断", "终端电阻", "绝缘告警"]:
        print(f"\n问题：{q}")
        for r in bm25_search(q, top_k=2):
            print(f"  [score={r['score']:.3f}] {r['source']}")