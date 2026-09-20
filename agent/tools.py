import time
import sqlite3
from retrieval.fusion import hybrid_search
from agent.tool_registry import register_tool, execute_tool, list_tools, get_tools_for_planner

TICKETS_DB = "data/tickets.db"
BOM_DB = "data/bom.db"
WECOM_DB = "data/wecom.db"


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
    stat_type = (stat_type or "summary").lower()
    if "fault" in stat_type or "故障" in stat_type or "frequency" in stat_type:
        stat_type = "fault_top"
    elif "device" in stat_type or "设备" in stat_type:
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


@register_tool(
    name="bom_version_trace",
    description="查询产品 BOM 版本、工艺变更记录、批次差异",
    params_schema={
        "product_code": "产品型号/编码（如 LBE-2000、直流屏-DC110）",
        "need_version_compare": "是否对比历史版本（true/false，默认 false）"
    }
)
def bom_version_trace(product_code: str, need_version_compare: bool = False) -> dict:
    """工具4：BOM 工艺版本追溯"""
    try:
        conn = sqlite3.connect(BOM_DB)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT version, change_note, components, created_at
            FROM bom_versions
            WHERE product_code = ?
            ORDER BY version
        """, (product_code,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {
                "status": "success",
                "results": [],
                "error": None
            }

        results = []

        if need_version_compare:
            text = f"{product_code} 版本变更历史：\n"
            for i, (ver, note, comp, date) in enumerate(rows, 1):
                text += f"\n【{ver}】（{date}）\n  变更：{note}\n  物料：{comp}"
            results.append({
                "content": text.strip(),
                "source": f"BOM-{product_code}-版本对比",
                "score": 1.0
            })
        else:
            ver, note, comp, date = rows[-1]
            text = f"{product_code} 最新版本：{ver}（{date}）\n变更：{note}\n物料清单：{comp}"
            results.append({
                "content": text,
                "source": f"BOM-{product_code}-最新版本",
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
    name="wecom_chat_fetch",
    description="从企业微信售后群聊天记录中检索排障经验",
    params_schema={
        "query": "检索关键词",
        "top_k": "返回条数，默认 2"
    }
)
def wecom_chat_fetch(query: str, top_k: int = 2) -> dict:
    """工具5：企业微信聊天经验检索（mock SQLite）"""
    try:
        conn = sqlite3.connect(WECOM_DB)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT msg_id, sender, send_time, content
            FROM wecom_messages
            WHERE is_effective = 1 AND reviewed = 1
              AND content LIKE ?
            ORDER BY send_time DESC
            LIMIT ?
        """, (f"%{query}%", top_k))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for msg_id, sender, send_time, content in rows:
            results.append({
                "content": f"【{sender} {send_time}】{content}",
                "source": f"企业微信-{msg_id}",
                "score": 1.0
            })

        return {
            "status": "success",
            "results": results,
            "error": None
        }
    except Exception as e:
        return {
            "status": "fallback",
            "results": [],
            "error": f"企业微信数据不可用：{str(e)}",
            "fallback_reason": "wecom_db_unavailable"
        }

MEMORY_DB = "data/memory.db"


@register_tool(
    name="memory_search",
    description="从长期记忆中检索相似故障的处理方案（Agent 自己沉淀的经验）",
    params_schema={
        "fault_phenomenon": "故障现象描述",
        "device_model": "设备型号（可选）",
        "top_k": "返回条数，默认 2"
    }
)
@register_tool(
    name="memory_search",
    description="从长期记忆中检索相似故障的处理方案（Agent 自己沉淀的经验）",
    params_schema={
        "fault_phenomenon": "故障现象描述",
        "device_model": "设备型号（可选）",
        "top_k": "返回条数，默认 2"
    }
)
def memory_search(fault_phenomenon: str, device_model: str = None, top_k: int = 2) -> dict:
    """工具6：长期记忆检索（带软遗忘）"""
    try:
        conn = sqlite3.connect(MEMORY_DB)
        cursor = conn.cursor()

        query = """
            SELECT id, device_model, fault_phenomenon, solution, confidence, access_count
            FROM memory
            WHERE fault_phenomenon LIKE ?
        """
        params = [f"%{fault_phenomenon}%"]

        if device_model:
            query += " AND device_model = ?"
            params.append(device_model)

        # 软遗忘：按「置信度 × 访问热度」排序，不再简单按 confidence
        # 热度公式：1 + log(1 + access_count)
        query += " ORDER BY (confidence * (1 + 0.5 * access_count)) DESC LIMIT ?"
        params.append(top_k)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        if rows:
            ids = [row[0] for row in rows]
            placeholders = ",".join("?" * len(ids))
            cursor.execute(
                f"UPDATE memory SET access_count = access_count + 1, last_accessed_at = datetime('now') WHERE id IN ({placeholders})",
                ids
            )
            conn.commit()

        conn.close()

        results = []
        for row in rows:
            mid, dm, fp, sol, conf, cnt = row
            results.append({
                "content": f"【记忆 #{mid}】{dm or '通用'}｜{fp}\n方案：{sol}",
                "source": f"长期记忆 #{mid}",
                "score": conf
            })

        return {
            "status": "success",
            "results": results,
            "error": None
        }
    except Exception as e:
        return {
            "status": "fallback",
            "results": [],
            "error": f"记忆库不可用：{str(e)}"
        }


def _summarize_if_too_long(solution: str, max_len: int = 500) -> str:
    """如果方案超过 max_len，调用 LLM 摘要"""
    if len(solution) <= max_len:
        return solution

    try:
        from agent.llm import call_llm
        prompt = f"""请把以下故障处理方案压缩到 300 字以内，保留关键信息（根因、排查步骤、配件）。

原文：
{solution}

压缩后：
"""
        summary = call_llm(prompt)
        return summary.strip()
    except Exception as e:
        print(f"[记忆压缩失败] {e}")
        return solution[:max_len] + "..."


def memory_save(device_model: str, fault_phenomenon: str, solution: str,
                source_ticket: str = None, confidence: float = 0.8) -> int:
    """
    写入长期记忆（含压缩和去重）。

    返回新记录 ID。
    """
    # 压缩过长内容
    solution = _summarize_if_too_long(solution)

    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()

    # 去重检查
    cursor.execute("""
        SELECT id, confidence FROM memory
        WHERE fault_phenomenon = ? AND (device_model = ? OR (device_model IS NULL AND ? IS NULL))
    """, (fault_phenomenon, device_model, device_model))

    existing = cursor.fetchone()

    if existing:
        mid, old_conf = existing
        # 置信度取较高值
        new_conf = max(old_conf, confidence)
        cursor.execute("""
            UPDATE memory
            SET solution = ?, confidence = ?, last_accessed_at = datetime('now')
            WHERE id = ?
        """, (solution, new_conf, mid))
    else:
        cursor.execute("""
            INSERT INTO memory (device_model, fault_phenomenon, solution, source_ticket, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (device_model, fault_phenomenon, solution, source_ticket, confidence))
        mid = cursor.lastrowid

    conn.commit()
    conn.close()
    return mid