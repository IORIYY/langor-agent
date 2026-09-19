"""
工具注册框架。

每个工具用 @register_tool 装饰器注册，自动加入 TOOL_REGISTRY。
"""
import time
import functools
from typing import Callable


# 全局工具注册表
TOOL_REGISTRY = {}


def register_tool(name: str, description: str = "", params_schema: dict = None):
    """
    装饰器：注册工具。
    """
    def decorator(func: Callable):
        TOOL_REGISTRY[name] = {
            "name": name,
            "description": description,
            "params_schema": params_schema or {},
            "func": func
        }
        return func
    return decorator


def list_tools() -> list:
    """列出所有已注册工具"""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "params_schema": t["params_schema"]
        }
        for t in TOOL_REGISTRY.values()
    ]


def execute_tool(tool_name: str, params: dict) -> dict:
    """
    执行工具，带异常处理 + 重试 + 降级。

    返回格式：
    {
        "status": "success | error | fallback",
        "results": [...],
        "duration_ms": 123,
        "error": None,
        "retry_count": 0
    }

    重要：fallback 和 success 一样，都视为「有效返回」，
    主流程不中断。
    """
    start = time.time()

    if tool_name not in TOOL_REGISTRY:
        return {
            "status": "error",
            "error": f"工具不存在：{tool_name}",
            "results": [],
            "duration_ms": 0,
            "retry_count": 0
        }

    tool = TOOL_REGISTRY[tool_name]
    func = tool["func"]

    max_retries = 2
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            result = func(**params)
            result["duration_ms"] = int((time.time() - start) * 1000)
            result["retry_count"] = attempt
            # 确保 status 字段存在
            if "status" not in result:
                result["status"] = "success"
            return result
        except Exception as e:
            last_error = str(e)
            print(f"[工具重试 {attempt+1}/{max_retries}] {tool_name}: {e}")
            if attempt < max_retries:
                time.sleep(0.5)

    # 全部重试失败 → 降级返回（不让 Agent 崩溃）
    return {
        "status": "fallback",
        "error": last_error,
        "results": [],
        "duration_ms": int((time.time() - start) * 1000),
        "retry_count": max_retries,
        "fallback_reason": "max_retries_exceeded"
    }


def get_tools_for_planner() -> str:
    """生成给 Planner 看的工具描述文本"""
    lines = []
    for t in TOOL_REGISTRY.values():
        lines.append(f"- {t['name']}：{t['description']}")
        if t["params_schema"]:
            for param, desc in t["params_schema"].items():
                lines.append(f"    - {param}: {desc}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("工具注册框架已就绪")
    print(f"当前已注册工具：{len(TOOL_REGISTRY)} 个")