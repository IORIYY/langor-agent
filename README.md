# 朗尔设备运维 AI Agent

基于 Qwen2.5 7B + LangGraph 三分离状态机的工业设备故障排查助手。

## 核心能力

- **故障诊断**：输入故障描述，输出结构化排查报告
- **工单统计**：故障 TOP、设备 TOP、总数
- **BOM 查询**：产品版本、变更记录、物料清单
- **企业微信经验**：从聊天记录检索排障经验
- **多源融合**：SOP + 历史工单 + 企业微信 + 长期记忆
- **多轮对话**：支持追问，保持上下文

## 架构

### 三分离状态机（LangGraph）

```
IntentNode → PlannerNode → ExecutorNode → ReviewerNode → OutputFormatter
                  ↑                            │
                  └──────── need_more_info ────┘
```

- **IntentNode**：意图识别（fault/workorder/bom/knowledge/boundary）
- **PlannerNode**：任务规划，决定调哪些工具
- **ExecutorNode**：执行工具
- **ReviewerNode**：独立评审，三分支（pass / need_more_info / fail）
- **OutputFormatter**：按意图生成结构化报告

### 检索层（4 层）

```
BM25 关键词 → 向量检索 → RRF 融合 → Rerank 精排
```

### 工具层（6 个工具）

| 工具 | 功能 |
|---|---|
| `rag_search` | 知识库混合检索 |
| `fault_case_match` | 历史故障案例匹配 |
| `workorder_analysis` | 工单统计分析 |
| `bom_version_trace` | BOM 工艺版本追溯 |
| `wecom_chat_fetch` | 企业微信聊天经验 |
| `memory_search` | 长期记忆检索 |

### 三层记忆

- **短期会话**：`chat_history`
- **任务工作**：`AgentState`
- **长期结构化**：SQLite（含压缩 + 软遗忘）

## 量化指标

| 指标 | 数值 |
|---|---|
| Evals 通过率 | 95% |
| 意图识别 | 100% |
| 工具调用 | 90% |
| 要点命中 | 95% |

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

```bash
pip install -r requirements.txt
python init_tickets.py    # 建工单库
python init_bom.py        # 建 BOM 库
python init_wecom.py      # 建企业微信库
python init_memory.py     # 建记忆库
python indexer.py         # 建向量库
streamlit run app_agent.py
```

## 项目结构

```
langor-agent/
  agent/              # LangGraph Agent
    state.py          # 状态定义
    prompts.py        # 所有 Prompt
    llm.py            # LLM 调用
    tools.py          # 6 个工具
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
  app_agent.py        # Streamlit（三分离版）
  eval_runner.py      # Evals 执行
  eval_regression.py  # 回归测试
```

## 项目亮点

1. **三分离防幻觉**：Planner 规划、Executor 执行、Reviewer 独立评审
2. **混合检索**：BM25 + 向量 + RRF + Rerank
3. **多源融合**：SOP + 工单 + 企微 + 长期记忆
4. **三层记忆**：短期 + 任务 + 长期
5. **Agent Evals**：20 题测试集 + 四维评估 + 回归拦截
6. **工具降级**：单数据源挂了不中断主流程
7. **按意图区分输出**：故障诊断 / 工单统计 / BOM 查询不同模板

## 测试

```bash
python eval_runner.py       # 跑 20 题评估
python eval_regression.py   # 回归测试（对比上次）
```

评估报告保存在本地 `data/eval_report.md`（data 目录不上传 GitHub）。