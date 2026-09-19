import time
from retriever import retrieve_with_filter


def rag_search(query: str, top_k: int = 3, max_score: float = 1.2) -> dict:
    """工具1：知识库检索"""
    start = time.time()
    try:
        results = retrieve_with_filter(query, top_k=top_k, max_score=max_score)
        return {
            "status": "success",
            "results": results,
            "duration_ms": int((time.time() - start) * 1000)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "results": [],
            "duration_ms": int((time.time() - start) * 1000)
        }


def fault_case_match(fault_phenomenon: str, top_k: int = 2) -> dict:
    """工具2：历史故障案例匹配（暂用检索代替）"""
    start = time.time()
    try:
        results = retrieve_with_filter(fault_phenomenon, top_k=top_k, max_score=1.2)
        return {
            "status": "success",
            "results": results,
            "duration_ms": int((time.time() - start) * 1000)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "results": [],
            "duration_ms": int((time.time() - start) * 1000)
        }


# 工具注册表
TOOL_REGISTRY = {
    "rag_search": rag_search,
    "fault_case_match": fault_case_match,
}


def execute_tool(tool_name: str, params: dict) -> dict:
    """执行工具，带异常处理"""
    if tool_name not in TOOL_REGISTRY:
        return {
            "status": "error",
            "error": f"工具不存在：{tool_name}",
            "results": [],
            "duration_ms": 0
        }
    try:
        return TOOL_REGISTRY[tool_name](**params)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "results": [],
            "duration_ms": 0
        }


if __name__ == "__main__":
    # 测试
    r = execute_tool("rag_search", {"query": "均衡电流异常怎么排查"})
    print(f"状态：{r['status']}")
    print(f"耗时：{r['duration_ms']}ms")
    print(f"结果数：{len(r['results'])}")
    for item in r["results"]:
        print(f"  [{item['score']:.3f}] {item['source']}")