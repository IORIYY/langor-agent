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
    try:
        conn = sqlite3.connect(TICKETS_DB)
        cursor = conn.cursor()

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


@register_tool(
    name="workorder_analysis",
    description="工单统计分析，返回故障 TOP、设备 TOP、总数",
    params_schema={
        "stat_type": "统计类型：fault_top/device_top/summary（默认 summary）",
        "top_n": "返回前 N 条，默认 5"
    }
)
def workorder_analysis(stat_type: str = "summary", top_n: int = 5) -> dict:
    """工具3：工单统计分析"""
    # 宽容处理：把 Planner 可能传的各种值标准化
    stat_type = (stat_type or "summary").lower()
    if "fault" in stat_type:
        stat_type = "fault_top"
    elif "device" in stat_type:
        stat_type = "device_top"
    else:
        stat_type = "summary"

    try:
        conn = sqlite3.connect(TICKETS_DB)
        cursor = conn.cursor()

        results = []

        if stat_type in ("fault_top", "summary"):
            cursor.execute("""
                SELECT fault_phenomenon, COUNT(*) as cnt
                FROM tickets
                GROUP BY fault_phenomenon
                ORDER BY cnt DESC
                LIMIT ?
            """, (top_n,))
            fault_rows = cursor.fetchall()
            fault_text = "故障 TOP：\n"
            for i, (fault, cnt) in enumerate(fault_rows, 1):
                fault_text += f"  {i}. {fault}（{cnt} 次）\n"
            results.append({
                "content": fault_text.strip(),
                "source": "工单统计-故障TOP",
                "score": 1.0
            })

        if stat_type in ("device_top", "summary"):
            cursor.execute("""
                SELECT device_model, COUNT(*) as cnt
                FROM tickets
                GROUP BY device_model
                ORDER BY cnt DESC
                LIMIT ?
            """, (top_n,))
            device_rows = cursor.fetchall()
            device_text = "设备 TOP：\n"
            for i, (dm, cnt) in enumerate(device_rows, 1):
                device_text += f"  {i}. {dm}（{cnt} 单）\n"
            results.append({
                "content": device_text.strip(),
                "source": "工单统计-设备TOP",
                "score": 1.0
            })

        if stat_type == "summary":
            cursor.execute("SELECT COUNT(*) FROM tickets")
            total = cursor.fetchone()[0]
            results.append({
                "content": f"工单总数：{total} 单",
                "source": "工单统计-汇总",
                "score": 1.0
            })

        conn.close()

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

    print("\n=== 测试 workorder_analysis ===")
    r = execute_tool("workorder_analysis", {"stat_type": "summary"})
    print(f"状态：{r['status']}")
    for item in r["results"]:
        print(f"\n{item['content']}")

    print("\n=== 测试 fault_case_match ===")
    r = execute_tool("fault_case_match", {"fault_phenomenon": "均衡电流异常"})
    print(f"状态：{r['status']}")
    print(f"结果数：{len(r['results'])}")