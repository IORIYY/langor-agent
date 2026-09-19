import time
from retrieval.fusion import hybrid_search
from agent.tool_registry import register_tool, execute_tool, list_tools, get_tools_for_planner


@register_tool(
    name="rag_search",
    description="检索设备运维知识库，支持设备型号和故障现象过滤",
    params_schema={
        "query": "检索关键词或问题",
        "top_k": "返回条数，默认 3"
    }
)
def rag_search(query: str, top_k: int = 3) -> dict:
    """工具1：知识库检索（混合检索 + Rerank）"""
    results = hybrid_search(query, top_k=top_k, use_rerank=True)
    normalized = []
    for r in results:
        normalized.append({
            "content": r["content"],
            "source": r["source"],
            "score": r.get("rerank_score", r.get("rrf_score", 0))
        })
    return {
        "status": "success",
        "results": normalized,
        "error": None
    }


@register_tool(
    name="fault_case_match",
    description="匹配历史故障案例，返回根因和维修方案",
    params_schema={
        "fault_phenomenon": "故障现象描述",
        "top_k": "返回条数，默认 2"
    }
)
def fault_case_match(fault_phenomenon: str, top_k: int = 2) -> dict:
    """工具2：历史故障案例匹配"""
    results = hybrid_search(fault_phenomenon, top_k=top_k, use_rerank=True)
    normalized = []
    for r in results:
        normalized.append({
            "content": r["content"],
            "source": r["source"],
            "score": r.get("rerank_score", r.get("rrf_score", 0))
        })
    return {
        "status": "success",
        "results": normalized,
        "error": None
    }


if __name__ == "__main__":
    print("=== 已注册工具 ===")
    for t in list_tools():
        print(f"- {t['name']}: {t['description']}")

    print("\n=== 测试执行 ===")
    r = execute_tool("rag_search", {"query": "均衡电流异常"})
    print(f"状态：{r['status']}")
    print(f"耗时：{r['duration_ms']}ms")
    print(f"结果数：{len(r['results'])}")

    print("\n=== 测试不存在的工具 ===")
    r = execute_tool("nonexistent", {})
    print(f"状态：{r['status']}")
    print(f"错误：{r['error']}")