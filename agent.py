import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import ollama
from retriever import retrieve_with_filter

# ============ 配置 ============
MODEL_NAME = "qwen2.5:7b"
SCORE_THRESHOLD = 0.8
TOP_K = 3

SYSTEM_PROMPT = """你是一个工业设备运维助手，帮售后工程师排查故障。

请严格基于以下参考资料回答，要求：

1. 只使用参考资料中的信息，不要编造
2. 按以下结构输出：
   - 【故障总结】一句话概括
   - 【可能原因】按可能性从高到低列出
   - 【排查步骤】分步骤，清晰可执行
   - 【所需配件】如涉及更换
   - 【安全提示】涉及高压等操作必须提醒
   - 【来源】参考资料文件名
3. 如果参考资料不足以回答，明确说"根据现有资料无法回答"
4. 用简洁中文，控制在 500 字以内
"""

REFUSAL_ANSWER = "根据现有资料无法回答这个问题，建议人工排查或咨询资深工程师。"


def ask(question: str) -> dict:
    """
    输入问题，返回结构化排查报告。

    返回格式：
    {
        "answer": "报告内容",
        "sources": ["来源文件"],
        "blocked": False 或 True,
        "reason": "拒答原因（可选）"
    }
    """
    # 1. 检索
    results = retrieve_with_filter(question, top_k=TOP_K, max_score=SCORE_THRESHOLD)

    # 2. 无相关内容 → 拒答
    if not results:
        return {
            "answer": REFUSAL_ANSWER,
            "sources": [],
            "blocked": True,
            "reason": "no_relevant_docs"
        }

    # 3. 拼上下文
    context_parts = []
    sources = []
    for r in results:
        src = r["source"]
        sources.append(src)
        context_parts.append(f"【{src}】\n{r['content']}")
    context = "\n\n".join(context_parts)

    # 4. 拼 Prompt
    prompt = f"""{SYSTEM_PROMPT}

参考资料：
{context}

工程师的问题：{question}
"""

    # 5. 调模型
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response["message"]["content"]
    except Exception as e:
        answer = f"调用模型出错：{e}"
        sources = []

    return {
        "answer": answer,
        "sources": list(set(sources)),
        "blocked": False
    }


if __name__ == "__main__":
    tests = [
        "LBE-2000 均衡电流异常怎么排查？",
        "通讯中断怎么办？",
        "直流屏绝缘告警怎么处理？",
        "今天天气怎么样？",
    ]

    for q in tests:
        print(f"\n{'='*60}")
        print(f"问题：{q}")
        result = ask(q)
        print(f"\n回答：\n{result['answer']}")
        print(f"\n来源：{result['sources']}")
        if result.get("blocked"):
            print(f"[拦截原因] {result.get('reason')}")