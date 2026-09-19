# 朗尔设备运维 AI Agent

基于 Qwen2.5 7B + RAG 的工业设备故障排查助手。

## 功能

- 故障诊断：输入故障描述，输出结构化排查报告
- 知识库检索：支持 LBE 均衡器、直流屏、放电设备
- 分层兜底：强相关 RAG、弱相关引导、无关通用话术
- 敏感词拦截：违规内容拒答

## 技术栈

- LLM：Qwen2.5 7B（Ollama）
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
  docs/
    sop/          # 排查 SOP 文档
    manuals/      # 设备手册
  data/
    chroma_db/    # 向量库
  agent.py        # 核心逻辑
  retriever.py    # 检索
  indexer.py      # 索引构建
  app.py          # Streamlit 界面
  test_batch.py   # 测试脚本
\`\`\`

## 测试结果

20 题测试，通过率 XX%。