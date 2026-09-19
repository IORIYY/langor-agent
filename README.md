# 朗尔设备运维 AI Agent

基于 Qwen2.5 7B + LangGraph 三分离状态机的工业设备故障排查助手。

## 功能

- **故障诊断**：输入故障描述，输出结构化排查报告
- **知识库检索**：支持 LBE 均衡器、直流屏、放电设备
- **分层兜底**：强相关 RAG、弱相关引导、无关通用话术
- **敏感词拦截**：违规内容拒答

## 架构（LangGraph 三分离状态机）

\`\`\`
IntentNode → PlannerNode → ExecutorNode → ReviewerNode → OutputFormatterNode
                                  ↑              │
                                  └── need_more_info
\`\`\`

- **IntentNode**：意图解析（fault/knowledge/workorder/boundary）
- **PlannerNode**：任务规划，决定调哪些工具
- **ExecutorNode**：执行工具（rag_search + fault_case_match）
- **ReviewerNode**：独立评审，四维校验（完整性、一致性、权威性、幻觉）
- **OutputFormatterNode**：生成结构化报告

## 技术栈

- LLM：Qwen2.5 7B（Ollama）
- 编排：LangGraph
- Embedding：BAAI/bge-small-zh-v1.5
- 向量库：ChromaDB
- 框架：LangChain
- 前端：Streamlit

## 运行

\`\`\`bash
pip install -r requirements.txt
python indexer.py
streamlit run app.py
\`\`\`

## 项目结构

\`\`\`
langor-agent/
  agent/              # LangGraph Agent
    state.py          # 状态定义
    prompts.py        # 所有 Prompt
    llm.py            # LLM 调用封装
    tools.py          # 工具层
    nodes.py          # 5 个节点实现
    graph.py          # 状态机
  docs/sop/           # 排查 SOP
  data/chroma_db/     # 向量库
  agent.py            # 旧版（单次 RAG）
  retriever.py        # 检索
  indexer.py          # 索引
  app.py              # Streamlit 界面
  test_stage2.py      # 阶段2测试
\`\`\`

## 测试结果

阶段 2：10 题测试，通过率 80%。