# STEM 教师教育智能体前端接口文档

版本：V1.0
依据：《STEM教师教育智能体前端接口说明.docx》

## 1. 稳定接口

前端四个业务页面统一调用：

```text
POST /api/agent-chat
Content-Type: application/json
```

当前测试基础地址：

```text
https://stem-agent-gfcqvhpopr.cn-hangzhou.fcapp.run
```

完整地址：

```text
https://stem-agent-gfcqvhpopr.cn-hangzhou.fcapp.run/api/agent-chat
```

后端内部 `/api/chat` 由讯飞星辰工作流和 STEM 教育插件使用，前端不得直接调用。

## 2. 环境配置

| 环境变量 | 作用 | 默认值 |
|---|---|---|
| `STEM_MOCK_MODE` | `true` 使用内置 Mock；`false` 请求真实后端 | `true` |
| `STEM_API_BASE` | 后端基础地址，不包含接口路径 | 当前测试部署地址 |
| `STEM_API_TOKEN` | 可选测试令牌，通过 `X-Token` 发送 | 空 |

PowerShell 联调示例：

```powershell
$env:STEM_MOCK_MODE = "false"
$env:STEM_API_BASE = "https://stem-agent-gfcqvhpopr.cn-hangzhou.fcapp.run"
streamlit run app.py --server.port 8502
```

## 3. 请求格式

请求 Body 只能包含两个核心业务字段：

```json
{
  "question": "教师的问题",
  "agent_type": "lesson_design"
}
```

- `question`：用户输入以及页面整理出的必要上下文。
- `agent_type`：由当前页面固定决定，前端不自行识别或猜测。

## 4. 四个页面与 agent_type

| 前端页面 | 配置键 | agent_type |
|---|---|---|
| 跨学科教学模拟实训 | `sim_flow` | `learning_support` |
| 跨学科课程设计工作台 | `workbench_design` | `lesson_design` |
| 智能教学诊断与反思 | `diag_report` | `classroom_diagnosis` |
| 教育研究孵化助手 | `research_plan` | `education_research` |

`config.API_ENDPOINTS` 保留四个页面语义键，但四个值都映射到 `/api/agent-chat`；`config.AGENT_TYPES` 负责固定页面与智能体类型的对应关系。

## 5. 返回格式

当前稳定返回：

```json
{
  "answer": "智能体生成的完整回答……",
  "agent_type": "lesson_design"
}
```

未来可向后兼容增加来源字段：

```json
{
  "answer": "智能体生成的完整回答……",
  "agent_type": "classroom_diagnosis",
  "sources": [],
  "graph_sources": []
}
```

前端必须校验：

1. `answer` 是非空字符串；
2. `agent_type` 是约定值，并与本次请求一致；
3. `sources`、`graph_sources` 缺失时按空数组处理；
4. 契约异常、网络失败或非 2xx 响应时回退当前页面的 Mock 数据。

## 6. 页面适配规则

- 教学模拟：`answer` 展示为学习辅导智能体的本轮课堂建议；心流与多模态数值仍由前端演示模型生成。
- 智能诊断：`answer` 展示为真实诊断结论；仅在有可用溯源数据时显示图谱溯源入口。
- 课程设计：初生成和人工迭代的 `answer` 作为完整 Markdown 教案；素养校验的 `answer` 作为校验结论。
- 科研孵化：`answer` 作为完整研究方案展示。
- 当来源字段存在时，页面追加“回答依据”卡片。

## 7. 加载、超时与错误处理

- 连接超时：10 秒。
- 读取超时：180 秒，避免 GraphRAG、向量检索、工作流和 LoRA 生成被 10 秒或 20 秒的短超时中断。
- 真实请求期间显示“智能体正在检索知识并生成回答……”。
- 页面不展示后端堆栈、内部配置或完整异常详情。
- 错误响应常见格式为 `{"detail": "错误信息"}`；前端统一显示友好状态并自动回退 Mock。

## 8. 基础联调验收

四种 `agent_type` 分别发送一次请求，满足以下条件即通过基础联调：

1. 请求方法为 POST，路径为 `/api/agent-chat`；
2. Body 仅包含 `question` 和 `agent_type`；
3. 返回 HTTP 2xx JSON 对象；
4. `answer` 非空；
5. 返回的 `agent_type` 与请求一致；
6. 页面有加载反馈，失败后可恢复且不会泄露内部异常。

回答质量评测由后端侧另行进行。

## 9. 前端扩展接口（待后端同步）

### 9.1 音频转写

```text
POST /api/transcribe
Content-Type: multipart/form-data
文件字段：file
```

成功响应：

```json
{
  "text": "识别后的授课文本"
}
```

前端支持 WAV、MP3、M4A、OGG、WebM。失败时保留音频和手动文本输入，不影响四智能体接口。

### 9.2 跨会话内容档案

`workspace_id` 由前端生成，为不包含个人信息的 UUID。状态对象只包含业务输入与生成结果，不包含上传文件、Token 或后端连接状态。

```text
GET /api/frontend-state/{workspace_id}
```

返回：

```json
{
  "state": {}
}
```

新档案也必须返回 HTTP 200 和空 `state`；不要用 404 表示空档案，否则前端会判断为接口尚未启用。

```text
PUT /api/frontend-state/{workspace_id}
Content-Type: application/json
```

请求：

```json
{
  "state": {
    "sim_teacher_input": "授课文本",
    "diag_lesson_text": "课例文本",
    "ws_lesson": "生成的 Markdown 教案",
    "research_result": {}
  }
}
```

成功响应：

```json
{
  "success": true
}
```

手动清除：

```text
DELETE /api/frontend-state/{workspace_id}
```

成功响应：

```json
{
  "success": true
}
```
