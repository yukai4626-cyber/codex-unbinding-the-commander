# STEM 教师教育智能体前端接口文档

版本：V1.0
依据：《STEM教师教育智能体前端接口说明.docx》

后端实现优先级、最近联调状态和联合验收步骤见[《后端联调交接清单》](后端联调交接清单.md)。

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
- 后端应支持至少约 25,000 个 Unicode 字符的 `question`；前端不增加 `action`、会话 ID 或其他阶段字段。

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

可选来源字段使用可直接展示的字符串数组：

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
4. `sources`、`graph_sources` 存在时必须是可直接展示的字符串数组；
5. 契约异常、网络失败或非 2xx 响应时，保留输入、已有结果和当前流程阶段，并停留在发起操作的视图显示错误。

真实请求失败不计作成功，也不自动覆盖为 Mock。存在兜底的页面仅在用户主动点击“查看 Mock 示例”后只读展示，并提供返回原视图的入口。

## 6. 页面适配规则

- 教学模拟：`answer` 展示为学习辅导智能体的本轮课堂建议；心流与多模态数值仍由前端演示模型生成。
- 智能诊断：`answer` 展示为真实诊断结论；仅在有可用溯源数据时显示图谱溯源入口。
- 课程设计：初生成和人工迭代的 `answer` 作为完整 Markdown 教案；素养校验的 `answer` 作为校验结论。
- 科研孵化：`answer` 作为完整研究方案展示。
- 当来源字段存在时，页面追加“回答依据”卡片。
- `trace`、`itrs`、`stem`、`stage` 等旧结构化字段不属于当前稳定返回契约；图谱、心流、多模态及评分指标仍使用前端明确标注的本地演示数据。

## 7. 加载、超时与错误处理

- 连接超时：10 秒。
- 读取超时：180 秒，避免 GraphRAG、向量检索、工作流和 LoRA 生成被 10 秒或 20 秒的短超时中断。
- 真实请求期间显示“智能体正在检索知识并生成回答……”。
- 页面不展示后端堆栈、内部配置或完整异常详情。
- 错误响应使用非 2xx 和 JSON `{"detail": "错误信息"}`；前端显示友好状态并保留本次错误，不自动跳转或推进业务阶段。
- 后端不得用 HTTP 200 返回空回答、错误对象、`success: false` 或错误的 `agent_type`。

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

### 本轮体验与档案约定（2026-09-02）

- 路径及 `question` / `agent_type` 不变，不改图谱契约。科研仍是引导填写后一次生成，状态键仍为 `research_pain`。
- 音频上限 50 MB，先预览转写，再选择替换或追加；最多回填 5,000 字，超长需确认，完整文本可下载。Mock 明确标为示例，不代表实际识别。后端需同步网关限制、超时和五种音频格式支持。
- TXT / DOCX 上限 10 MB；DOCX 正文 XML 解压后上限 20 MB。表格保留行和单元格分隔，最终仅发送最多 20,000 字纯文本，不上传原文档给智能体。
- 对话完整保存；智能体请求使用课例摘录（2,400 字）、匹配的诊断结论（1,600 字）、最近 6 条对话（每条最多 900 字）及本轮问题。旧报告不作为新课例证据。
- 真实请求失败保留问题，Mock 建议单独标注，不计入已发送消息。
- 每类输入、结果只保留最新内容，对话不截断；转写文本、对话草稿纳入 `state`，原始上传文件、Token、临时 `_ui_` 控件键不进入档案。
- GET 新档案必须返回 `200 {"state": {}}`；404 视为接口不可用，不自动写入空档案。
- PUT / DELETE 成功返回 `2xx {"success": true}` 或 HTTP 204；不以仅有 HTTP 200 作为成功确认。
- 重连发现远端内容时，用户选择恢复远端或保留本次内容，不自动覆盖。
- JSON 备份为 `{"format_version":1,"exported_at":"UTC ISO时间","state":{...}}`，上限 10 MB；兼容旧的 `{"state":{...}}`。字段与类型校验通过并确认后导入当前 workspace，不覆盖其身份。
- 输入失焦或按 Ctrl+Enter 提交后才可保存；未提交键入内容不保证保存。接口失败时只承诺当前会话保留，并提供手动备份。
- 仅清空本次会话会生成新 workspace，旧远端不变；远端删除必须确认成功后才清空本地并更换 workspace。
- 旧档案缺失新字段时使用默认值；后端需支持业务 state 扩展及容量限制，禁止静默截断。
- workspace UUID 不是用户认证。公开使用前后端仍需实现档案归属、访问控制和并发写入策略；当前版本不保证多人同时编辑同一档案不会相互覆盖。

#### 本轮联调记录（2026-09-02，仅代表当次环境）

- Python 3.10.11 / Streamlit 1.61.1 / streamlit-agraph 0.0.45；四文件编译、七页及关键流程 AppTest 通过。
- 从本机 8502 网页输入研究问题，`education_research` 返回 HTTP 200，完整方案显示正常。
- 从诊断页发送教师问题，`classroom_diagnosis` 返回 HTTP 200，对话显示正常。
- 已验证的真实智能体请求仅限上述科研生成和诊断教师对话。课程设计初生成/人工迭代/素养校验、诊断报告、教学模拟以及后端变更后的科研生成均需重新从网页验证。
- 从网页上传 WAV 并点击转写，`POST /api/transcribe` 返回 HTTP 404；已验证错误提示，不代表真实识别可用。
- 网页自动读取 `GET /api/frontend-state/{workspace_id}` 返回 HTTP 404；长期恢复待后端实现，不能宣称已验证成功。
- 网页 DOCX 正文及表格导入、JSON 备份下载与确认恢复通过。恢复不改变当前 workspace。
- 持久化成功、失败、重连、删除等分支使用替身响应测试；未对真实后端执行 DELETE。
- 本轮不验证四智能体全链路内部的 GraphRAG / LoRA 执行情况，不以回答成功推断这些内部步骤已运行。

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
单文件上限为 50 MB；网关上传限制必须覆盖 multipart 编码开销。无效、超限和不支持格式应返回明确的非 2xx JSON `detail`。

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

PUT 使用本次 `state` 完整覆盖当前档案，上限 10 MB，禁止静默截断。后端将通过大小限制的 JSON 对象原样保存和返回。

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

DELETE 建议保持幂等；PUT 和 DELETE 也可使用 HTTP 204 表示成功。
