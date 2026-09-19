import time
import sqlite3
from retrieval.fusion import hybrid_search
from agent.tool_registry import register_tool, execute_tool, list_tools, get_tools_for_planner

TICKETS_DB = "data/tickets.db"


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
    description="从历史工单库中匹配相似故障案例，返回根因和处理方案",
    params_schema={
        "fault_phenomenon": "故障现象描述",
        "device_model": "设备型号（可选）",
        "top_k": "返回条数，默认 2"
    }
)
def fault_case_match(fault_phenomenon: str, device_model: str = None, top_k: int = 2) -> dict:
    """工具2：历史故障案例匹配（SQLite）"""
    if not sqlite3:
        return {"status": "error", "error": "sqlite3 未加载", "results": []}

    try:
        conn = sqlite3.connect(TICKETS_DB)
        cursor = conn.cursor()

        # 按故障现象模糊匹配
        query = """
            SELECT ticket_no, device_model, fault_phenomenon, root_cause, solution
            FROM tickets
            WHERE fault_phenomenon LIKE ?
        """
        params = [f"%{fault_phenomenon}%"]

        if device_model:
            query += " AND device_model = ?"
            params.append(device_model)

        query += " LIMIT ?"
        params.append(top_k)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            ticket_no, dm, fp, rc, sol = row
            results.append({
                "content": f"工单 {ticket_no}｜{dm}｜{fp}\n根因：{rc}\n处理：{sol}",
                "source": f"历史工单 {ticket_no}",
                "score": 1.0
            })

        return {
            "status": "success",
            "results": results,
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "results": []
        }


if __name__ == "__main__":
    print("=== 已注册工具 ===")
    for t in list_tools():
        print(f"- {t['name']}: {t['description']}")

    print("\n=== 测试 fault_case_match ===")
    r = execute_tool("fault_case_match", {"fault_phenomenon": "均衡电流异常"})
    print(f"状态：{r['status']}")
    print(f"结果数：{len(r['results'])}")
    for item in r["results"]:
        print(f"  {item['content'][:60]}...")