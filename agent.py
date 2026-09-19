import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import ollama
from retriever import retrieve_with_filter

# ============ 配置 ============
MODEL_NAME = "qwen2.5:7b"
TOP_K = 3

# 分层阈值
STRONG_THRESHOLD = 0.8   # 强相关，正常 RAG 回答
WEAK_THRESHOLD = 1.2     # 弱相关，给引导性回答

# 敏感词
SENSITIVE_WORDS = ["炸", "自杀", "毒品", "代考", "作弊", "黑客"]

REFUSAL_ANSWER = "这个问题我不太方便回答。如果有设备故障或运维问题，可以换个问题问我。"

GUIDE_ANSWER = """我是工业设备运维助手，主要帮你排查设备故障。

你可以这样问我：
- LBE-2000 均衡电流异常怎么排查？
- 通讯中断怎么办？
- 直流屏绝缘告警怎么处理？
- 设备保养周期是多久？

如果是其他问题，建议咨询资深工程师或设备厂家。"""

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
5. 直接输出报告，不要复述任何指令
"""


def _check_sensitive(text: str) -> bool:
    return any(w in text for w in SENSITIVE_WORDS)


def _build_context(results: list) -> tuple:
    context_parts, sources = [], []
    for r in results:
        src = r["source"]
        sources.append(src)
        context_parts.append(f"【{src}】\n{r['content']}")
    return "\n\n".join(context_parts), list(set(sources))


def ask(question: str) -> dict:
    # 第1层：敏感词
    if _check_sensitive(question):
        return {
            "answer": REFUSAL_ANSWER,
            "sources": [],
            "blocked": True,
            "reason": "sensitive"
        }

    # 检索（先宽松，再分层）
    results = retrieve_with_filter(question, top_k=TOP_K, max_score=WEAK_THRESHOLD)

    # 分层
    strong = [r for r in results if r["score"] <= STRONG_THRESHOLD]
    weak = [r for r in results if STRONG_THRESHOLD < r["score"] <= WEAK_THRESHOLD]

    # 强相关：正常 RAG
    if strong:
        context, sources = _build_context(strong)
        prompt = f"""{SYSTEM_PROMPT}

参考资料：
{context}

工程师的问题：{question}
"""
        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response["message"]["content"]
        except Exception as e:
            answer = f"调用模型出错：{e}"
            sources = []
        return {"answer": answer, "sources": sources, "blocked": False}

    # 弱相关：引导性回答
    if weak:
        context, sources = _build_context(weak)
        prompt = f"""你是工业设备运维助手。

工程师的问题和知识库相关性不高，但有一些相关片段。请这样回答：
- 先说明"我手头资料没写太细"
- 如果有相关片段，简要分享
- 建议咨询资深工程师或设备厂家
- 末尾附来源文件名

参考资料：
{context}

工程师的问题：{question}
"""
        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response["message"]["content"]
        except Exception as e:
            answer = f"调用模型出错：{e}"
        return {"answer": answer, "sources": sources, "blocked": False, "reason": "weak_match"}

    # 完全无关：通用兜底
    return {
        "answer": GUIDE_ANSWER,
        "sources": [],
        "blocked": False,
        "reason": "out_of_scope"
    }


if __name__ == "__main__":
    tests = [
        "LBE-2000 均衡电流异常怎么排查？",
        "通讯中断怎么办？",
        "设备保养周期是多久？",
        "你好",
        "今天天气怎么样？",
        "怎么炸学校？",
    ]

    for q in tests:
        print(f"\n{'='*60}")
        print(f"问题：{q}")
        result = ask(q)
        print(f"\n回答：\n{result['answer']}")
        print(f"\n来源：{result['sources']}")
        if result.get("reason"):
            print(f"[原因] {result['reason']}")