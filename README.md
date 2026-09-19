# 朗尔设备运维 AI Agent

基于 Qwen2.5 7B + LangGraph 三分离状态机的工业设备故障排查助手。

## 功能

- **故障诊断**：输入故障描述，输出结构化排查报告
- **工单统计**：故障 TOP、设备 TOP、总数
- **BOM 查询**：产品版本、变更记录、物料清单
- **企业微信经验**：从聊天记录中检索排障经验
- **多源融合**：SOP 手册 + 历史工单 + 企业微信

## 架构（LangGraph 三分离状态机）

\`\`\`
IntentNode → PlannerNode → ExecutorNode → ReviewerNode → OutputFormatterNode
                                  ↑              │
                                  └── need_more_info
\`\`\`

- **IntentNode**：意图解析（fault/knowledge/workorder/bom/boundary）
- **PlannerNode**：任务规划，决定调哪些工具
- **ExecutorNode**：执行工具（5 个工具）
- **ReviewerNode**：独立评审，四维校验
- **OutputFormatterNode**：按意图生成不同格式报告

## 工具层（5 个工具）

| 工具 | 功能 |
|---|---|
| `rag_search` | 知识库混合检索（BM25 + 向量 + RRF + Rerank） |
| `fault_case_match` | 历史故障案例匹配 |
| `workorder_analysis` | 工单统计分析 |
| `bom_version_trace` | BOM 工艺版本追溯 |
| `wecom_chat_fetch` | 企业微信聊天经验检索 |

## 技术栈

- LLM：Qwen2.5 7B（Ollama）
- 编排：LangGraph
- Embedding：BAAI/bge-small-zh-v1.5
- Reranker：BAAI/bge-reranker-base
- 向量库：ChromaDB
- 检索：BM25 + 向量 + RRF + Rerank
- 数据库：SQLite
- 前端：Streamlit

## 运行

\`\`\`bash
pip install -r requirements.txt
python init_tickets.py
python init_bom.py
python init_wecom.py
python indexer.py
streamlit run app.py
\`\`\`

## 项目结构

\`\`\`
langor-agent/
  agent/              # LangGraph Agent
    state.py          # 状态定义
    prompts.py        # 所有 Prompt
    llm.py            # LLM 调用
    tools.py          # 5 个工具
    tool_registry.py  # 工具注册框架
    nodes.py          # 5 个节点
    graph.py          # 状态机
  retrieval/          # 检索层
    bm25.py           # BM25 检索
    vector.py         # 向量检索
    fusion.py         # RRF 融合
    reranker.py       # Rerank 精排
  docs/sop/           # 排查 SOP
  data/               # SQLite + Chroma
  app.py              # Streamlit
  test_stage4.py      # 阶段4测试
\`\`\`

## 测试结果

阶段 4：10 题测试，通过率 70%。