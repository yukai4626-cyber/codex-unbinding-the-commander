# API 接口文档（V2.0）

> 项目：STEM教师教育“教-学-研”一体化智能体 · 前端演示系统  
> 适用对象：初次参与前后端联调的后端与前端同学  
> 版本：V2.0 ｜ 2026-08-27 ｜ 状态：四个正式接口待逐项联调

本文档只约定本轮需要实现的 4 个业务接口。知识图谱页继续使用前端内置的 61 实体/61 关系数据，`/api/kg/subgraph` 不属于本轮交付范围。

---

## 一、先理解最简单的联调方式

后端按两个阶段开发，先跑通格式，再接入智能能力：

1. **固定 JSON 阶段**：创建 4 个 POST 路径。收到前端请求后，先直接返回本文档示例中的固定 JSON。此时不要求模型、RAG 或 Neo4j 可用。
2. **真实能力阶段**：固定 JSON 与前端联调成功后，再按接口逐个替换为模型、RAG 或 Neo4j 的真实结果。替换时保持字段名和字段类型不变。

推荐联调顺序：课程工作台 → 智能诊断 → 教学模拟 → 科研孵化。不要等四个接口全部完成后才第一次联调。

---

## 二、统一约定

| 项目 | 约定 |
|---|---|
| BaseURL | 本地默认 `http://127.0.0.1:8000`；联调时由后端提供实际地址 |
| 请求方式 | 4 个接口全部使用 `POST` |
| 数据格式 | 请求和响应均为 UTF-8 JSON，`Content-Type: application/json` |
| 超时 | 前端最长等待 10 秒 |
| 鉴权 | 可选请求头 `X-Token`；不鉴权时前端不发送该请求头 |
| Markdown | 教案与研究方案可返回 Markdown；不要返回未约定的 HTML |

### 前端环境变量

前端支持以下可选环境变量：

| 变量 | 说明 |
|---|---|
| `STEM_MOCK_MODE` | `true` 只使用 Mock；`false` 请求真实后端 |
| `STEM_API_BASE` | 后端基础地址 |
| `STEM_API_TOKEN` | 可选测试令牌，设置后作为 `X-Token` 请求头发送 |

例如在 PowerShell 中：

```powershell
$env:STEM_MOCK_MODE = "false"
$env:STEM_API_BASE = "http://127.0.0.1:8000"
$env:STEM_API_TOKEN = "测试令牌"
streamlit run app.py --server.port 8502
```

令牌不能写入代码、公开文档、截图或日志。

### 成功与失败响应

成功时返回 HTTP 200 和业务 JSON。失败时返回非 2xx 状态码，响应尽量统一为：

```json
{
  "error": "INVALID_REQUEST",
  "message": "lesson_text 不能为空"
}
```

不要用“HTTP 200 + 一段普通字符串”表示失败。前端遇到连接失败、超时、非 2xx、非 JSON、业务错误或字段异常时，会提示降级并使用相应 Mock 数据，页面不会中断。

---

## 三、接口一：课程设计工作台

### `POST /api/workbench/design`

三个步骤共用一个接口，通过 `action` 区分。建议后端先实现该接口，因为它是演示主线。

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `action` | string | 是 | `generate` 初生成、`revise` 迭代、`check` 校验 |
| `grade` | string | 是 | `小学`、`初中` 或 `高中` |
| `topic` | string | 是 | 课程主题 |
| `hours` | int | 是 | 课时数，范围 1–8 |
| `lesson_md` | string | 条件必填 | `revise` 和 `check` 时必须传入用户当前编辑后的完整教案；`generate` 时可不传或传空字符串 |

初生成请求：

```json
{
  "action": "generate",
  "grade": "初中",
  "topic": "碳中和·跨学科项目式学习",
  "hours": 4
}
```

人工编辑后的迭代请求：

```json
{
  "action": "revise",
  "grade": "初中",
  "topic": "碳中和·跨学科项目式学习",
  "hours": 4,
  "lesson_md": "# 用户已编辑的完整教案\n\n这里是完整正文……"
}
```

### 响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `stage` | int | `generate` 返回 1、`revise` 返回 2、`check` 返回 3 |
| `lesson_md` | string | 本次处理后的完整教案 Markdown，不能为空 |
| `itrs` | object | ITRS 四维评分，分值 0–100；通常在 `check` 时返回 |
| `stem` | object | STEM 五维评分，分值 0–100；通常在 `check` 时返回 |
| `conclusion` | string | 素养校验结论；通常在 `check` 时返回 |

`check` 响应示例：

```json
{
  "stage": 3,
  "lesson_md": "# 碳中和跨学科教案\n\n这里是校验后的完整教案……",
  "itrs": {
    "跨学科教学设计能力": 82,
    "教学实施与调控能力": 75,
    "技术融合应用能力": 78,
    "元认知反思能力": 80
  },
  "stem": {
    "科学思维": 86,
    "数学建模": 72,
    "工程实践": 70,
    "技术应用": 81,
    "社会责任": 90
  },
  "conclusion": "素养对齐校验通过，建议继续补充数学建模证据。"
}
```

前端生成后允许用户真实编辑教案。后端不能假设 `revise` 或 `check` 收到的是上一次原样返回值，必须处理用户修改后的完整 `lesson_md`。

---

## 四、接口二：智能教学诊断

### `POST /api/diag/report`

用户可以粘贴纯文本、上传 TXT 或选择内置样例。TXT 由前端读取成字符串，后端只接收文本，不接收文件。

本轮不支持 DOCX/PDF 上传或解析，也不要求后端实现文件解析。

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `lesson_text` | string | 是 | 课例纯文本，不能为空，前端最多发送 20,000 字 |
| `modalities` | array | 是 | 数据来源；本轮正式允许并默认发送 `["text"]` |

请求示例：

```json
{
  "lesson_text": "本节课以校园碳排放调查为任务，学生分组记录用电数据……",
  "modalities": ["text"]
}
```

### 响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `meta` | string | 课例概况和数据来源说明 |
| `problems` | array | 诊断问题列表 |
| `conclusion` | string | 反向归因总结论 |
| `suggests` | array | 改进建议字符串列表 |
| `trace` | object | 与本次报告对应的局部溯源子图 |

`problems` 每项结构：

```json
{
  "id": "P1",
  "title": "提问层次集中于低阶认知",
  "evidence": "课堂提问主要要求学生复述概念。",
  "cause": "问题链缺少分析与评价层支架。",
  "suggest": "加入比较、论证和方案评价任务。",
  "anchor": "布卢姆认知目标分类"
}
```

完整响应示例：

```json
{
  "meta": "课例主题：碳中和跨学科教学；数据源：文本",
  "problems": [
    {
      "id": "P1",
      "title": "提问层次集中于低阶认知",
      "evidence": "课堂提问主要要求学生复述概念。",
      "cause": "问题链缺少分析与评价层支架。",
      "suggest": "加入比较、论证和方案评价任务。",
      "anchor": "布卢姆认知目标分类"
    }
  ],
  "conclusion": "主要问题是认知任务层级和跨学科证据链不足。",
  "suggests": ["按认知层级重构问题链", "补充数据分析和工程权衡任务"],
  "trace": {
    "nodes": [
      {"id": "p1", "label": "低阶提问", "type": "问题", "desc": "提问以复述为主"},
      {"id": "t1", "label": "布卢姆认知目标分类", "type": "理论", "desc": "认知目标分层"},
      {"id": "c1", "label": "优质提问链课例", "type": "案例", "desc": "高阶问题链案例"}
    ],
    "edges": [
      ["p1", "t1", "理论溯源"],
      ["t1", "c1", "案例支撑"]
    ]
  }
}
```

`trace.edges` 中的起点和终点 ID 必须存在于 `trace.nodes`。报告与 `trace` 应在同一次响应中返回，确保弹窗展示的是本次诊断结果。

---

## 五、接口三：教学模拟

### `POST /api/sim/flow`

用户点击课堂互动后请求一次，返回本轮心流指标、虚拟学生反馈和多模态信号。

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `theme` | string | 是 | 授课主题 |
| `utterance` | string | 是 | 当前授课文本片段，前端最多发送 300 字 |
| `round` | int | 是 | 当前互动轮次，从 1 起 |

请求示例：

```json
{
  "theme": "碳中和·跨学科教学",
  "utterance": "同学们，请根据校园用电数据估算本月碳排放。",
  "round": 2
}
```

### 响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `flow` | object | `load`、`engage`、`confuse`、`flow` 四个 0–100 数值 |
| `status` | string | 状态文案，例如“深度心流”“心流平稳”“心流偏低” |
| `feedback` | array | 虚拟学生反馈列表 |
| `signals` | array | 多模态信号列表，各项 `value` 为 0–100 |

响应示例：

```json
{
  "flow": {"load": 38, "engage": 69, "confuse": 31, "flow": 76},
  "status": "深度心流",
  "feedback": [
    {"name": "小雨", "role": "概念跃迁困惑", "text": "老师，排放系数是怎样得到的？"}
  ],
  "signals": [
    {"name": "语音韵律", "value": 33, "note": "韵律紧张度"},
    {"name": "交互行为", "value": 71, "note": "举手与提问频次"}
  ]
}
```

`feedback` 每项使用 `name`、`role`、`text` 三个字符串字段；`signals` 每项使用 `name`、`value`、`note`。不同轮次或不同授课内容应尽量返回有变化的结果。

---

## 六、接口四：教育研究孵化

### `POST /api/research/plan`

输入可来自诊断页的问题、归因和建议，也可由用户独立填写。后端只需处理最终的纯文本 `pain_point`。

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `pain_point` | string | 是 | 教学痛点纯文本，不能为空，最多 2,000 字 |

请求示例：

```json
{
  "pain_point": "学生能够复述碳循环概念，但难以把能耗数据转化为碳排放模型；诊断显示问题链缺少分析和评价层任务。"
}
```

### 响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `topic_md` | string | 研究选题、依据、创新点和研究范式 Markdown |
| `lit_md` | string | 文献综述提纲 Markdown |
| `survey_md` | string | 问卷初稿 Markdown |
| `exp_md` | string | 实验设计初稿 Markdown |

响应示例：

```json
{
  "topic_md": "## 研究选题\n\n《基于课堂认知冲突数据的跨学科问题链研究》",
  "lit_md": "## 文献综述提纲\n\n1. 跨学科迁移研究\n2. 认知冲突研究",
  "survey_md": "## 问卷初稿\n\n1. 我能利用数据解释碳排放问题。",
  "exp_md": "## 实验设计\n\n采用前测、教学干预和后测设计。"
}
```

四个 Markdown 字段均应返回非空字符串。

---

## 七、页面与数据流

| 页面操作 | 接口 | 后续流向 |
|---|---|---|
| 工作台 AI 初生成、提交人工迭代、素养校验 | `/api/workbench/design` | 当前教案可送入模拟或诊断 |
| 模拟课堂互动 | `/api/sim/flow` | 本轮结果保存在前端会话中 |
| 诊断课例文本 | `/api/diag/report` | 问题、归因和建议可带入科研 |
| 生成研究方案 | `/api/research/plan` | 四项 Markdown 结果在前端缓存 |

跨页流转由 Streamlit 前端会话状态完成，不需要后端增加额外接口，也不要求后端保存会话。

---

## 八、后端自检与联调清单

### 第一步：固定 JSON 自检

后端启动后，先确认：

- 4 个 URL 都能接收 POST JSON；
- 中文请求和响应不乱码；
- 每个接口在 10 秒内返回；
- 成功响应是 HTTP 200 JSON；
- 缺少必填参数时返回非 2xx JSON 错误；
- 如果启用 Token，正确 Token 成功，错误 Token 返回 401 或 403。

PowerShell 自测示例：

```powershell
$body = @{
  action = "generate"
  grade = "初中"
  topic = "碳中和·跨学科项目式学习"
  hours = 4
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/workbench/design" `
  -ContentType "application/json" `
  -Body $body
```

如果启用 Token，在命令中增加：

```powershell
-Headers @{ "X-Token" = "测试令牌" }
```

### 第二步：与前端逐接口联调

每个接口依次检查：

1. 正常请求能显示真实结果；
2. 必填字段缺失时错误信息清楚；
3. Token 正确和错误时行为符合约定；
4. 后端返回 500 时前端自动回退 Mock；
5. 后端超时、返回非 JSON或缺少字段时，前端不崩溃；
6. 日志不记录完整课例、个人信息和 Token。

后端需要提供给前端：BaseURL、是否启用 `X-Token`、测试 Token、启动方法、可联调时间，以及每个接口一份真实成功响应。

---

## 九、本轮明确不做

- 不实现知识图谱后端接口；图谱页继续使用前端内置数据。
- 不上传或解析 DOCX/PDF；诊断只使用粘贴文本、TXT 和内置文本样例。
- 不要求第一版就接入模型、RAG、Neo4j、登录或数据库。
- 不增加新的前端第三方依赖。

只要固定 JSON 阶段严格遵守本契约，前后端就能先完成第一次联调；真实能力可以在接口稳定后逐个替换。
