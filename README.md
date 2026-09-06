# STEM教师教育“教-学-研”一体化智能体 · 前端演示 Demo

> 技术栈：Python 3.10.11 + Streamlit 1.61.1 + streamlit-agraph 0.0.45  
> 定位：可独立演示、可连接真实后端的 Streamlit 前端联调原型  
> 依赖约束：禁止新增第三方库；HTTP 请求使用 Streamlit 已依赖的 `requests`

本项目包含 7 个页面、1 个稳定业务接口和 4 种智能体类型。没有后端时可使用内置 Mock 数据完整演示；后端可用时，可通过环境变量切换到真实接口。真实请求失败会保留输入和已有结果，并停留在原视图显示错误；Mock 仅在用户主动选择后只读展示。

---

## 一、启动与运行模式

### 1. Mock 演示模式

```powershell
cd C:\Users\szsjdn\Desktop\街边挂帅
streamlit run app.py --server.port 8502
```

本机 8501 已被用户自己的旧 Streamlit 实例占用，因此开发、测试和验收统一使用 8502：<http://localhost:8502>。

### 2. 真实后端模式

运行前设置可选环境变量，无需修改页面代码：

```powershell
$env:STEM_MOCK_MODE = "false"
$env:STEM_API_BASE = "https://stem-agent-gfcqvhpopr.cn-hangzhou.fcapp.run"
Remove-Item Env:STEM_API_TOKEN -ErrorAction SilentlyContinue
streamlit run app.py --server.port 8502
```

| 环境变量 | 是否必填 | 说明 |
|---|---|---|
| `STEM_MOCK_MODE` | 否 | `true` 使用内置 Mock；`false` 请求真实后端；未设置时使用 `config.py` 默认值 |
| `STEM_API_BASE` | 否 | 后端基础地址；默认使用当前测试部署地址，不包含 `/api/agent-chat` |
| `STEM_API_TOKEN` | 否 | 测试令牌；设置后通过请求头 `X-Token` 发送，未设置时不发送该请求头 |

当前 v1.3.0 云端联调不启用 `X-Token`。后续启用时，令牌不得写入源码、提交记录、截图或公开日志；公网部署应使用平台 Secrets/环境变量。

启动前可访问 <https://stem-agent-gfcqvhpopr.cn-hangzhou.fcapp.run/health>，确认返回 `STEM-Agent`、版本 `1.3.0`。前端仍访问 <http://localhost:8502>，由 Streamlit 服务端请求云端接口，不依赖两台电脑之间的局域网直连。

---

## 二、文件职责

| 文件 | 职责 |
|---|---|
| `config.py` | `MOCK_MODE`、API 配置、7 页导航、图谱 6 子域、节点配色、全局色板、四大智能体和演示动线 |
| `components.py` | 全站 CSS、Iconify lucide 内联图标、会话状态、公共卡片与图谱组件、统一接口网关及 Mock 降级 |
| `pages.py` | 7 个页面函数与全部内置 Mock 数据，包括 61 实体/61 关系图谱、碳中和教案、诊断报告和科研方案 |
| `app.py` | 页面配置、样式与状态初始化、固定侧边栏、7 页导航和页面分发 |
| `.streamlit/config.toml` | Streamlit 控件主题；打包时不能遗漏该隐藏目录 |
| [API接口文档.md](API接口文档.md) | 统一智能体接口及扩展接口的稳定字段、超时和错误契约 |
| [后端联调交接清单.md](后端联调交接清单.md) | 后端 P0/P1 工作、最近联调状态、请求示例、交付物和联合验收清单 |
| [演示动线文档.md](演示动线文档.md) | 约 2 分 55 秒的答辩与录屏脚本 |

严格保持四文件 Python 架构，不拆分或新增业务 Python 模块。

---

## 三、七页与跨页闭环

1. 首页·项目总览：项目定位、四大智能体、整体架构和演示主线入口。
2. 跨学科教学模拟实训：接收授课文本，展示虚拟学生反馈、心流指标和多模态信号。
3. 智能教学诊断与反思：支持粘贴纯文本、上传 TXT 或使用内置样例，生成循证诊断与图谱溯源。
4. 跨学科课程设计工作台：完成“AI 初生成 → 真实编辑并提交人工迭代 → 素养校验”三步流程。
5. 教育研究孵化助手：将教学痛点转化为研究选题、综述提纲、问卷和实验方案。
6. 技术底座·知识图谱引擎：展示内置 61 实体、61 关系和 6 个子域；本轮不连接后端图谱接口。
7. 成果与价值：展示四大智能体价值、成长轨迹和明确标记为 Mock 的示例数据。

推荐主线是：

```text
工作台生成并编辑教案
    ├─ 送入教学模拟 → 课堂互动与心流反馈
    └─ 送入智能诊断 → 问题、归因、建议与溯源
                              └─ 带入科研孵化 → 研究方案
```

各页面仍保留独立输入和内置样例，因此不按主线操作也能单页演示。诊断页本轮只接收纯文本和 TXT；不承诺 DOCX/PDF 解析。前端读取 TXT 后向后端发送纯文本，不上传文件本体。

---

## 四、正式接口

四个业务页面统一调用 `POST /api/agent-chat`，请求 Body 仅包含 `question` 和 `agent_type`。

| 页面 | agent_type | answer 的页面用途 |
|---|---|---|
| 教学模拟 | `learning_support` | 本轮课堂互动与学习支持建议 |
| 智能诊断 | `classroom_diagnosis` | 课堂诊断结论与改进建议 |
| 课程工作台 | `lesson_design` | 完整教案或素养校验结论 |
| 科研孵化 | `education_research` | 完整教育研究方案 |

知识图谱后端接口不属于本轮正式接口，图谱页继续使用内置数据。稳定字段见[《API 接口文档》](API接口文档.md)，后端当前任务和验收顺序见[《后端联调交接清单》](后端联调交接清单.md)。

后端不可达、超时、返回非 JSON、业务报错或字段异常时，前端保留输入、已有结果和业务阶段，停留在发起操作的视图显示错误。存在兜底时，用户可主动进入“查看 Mock 示例”的只读预览；Mock 不覆盖业务数据，也不计作真实成功。Mock 数据只用于功能演示，成果页不得将其描述为真实实证结果。

---

## 五、设计体系

| 角色 | 规范 |
|---|---|
| 页面底色 | 深灰 `#0B1016` + 冷蓝/暖橙低透明径向微光 + 3%–5% SVG 噪点 |
| 工作区 | `rgba(18,25,34,.86)` 深色玻璃面板，20–24px 大圆角、极细浅色边框与柔和阴影 |
| 内容卡片 | `rgba(25,35,46,.66)` 半透明深色卡片；标题 `#EDF3F7`，次级文字 `#9DACB9` |
| 侧边栏 | DeepSeek 式 260px 工作栏：七模块导航 + 底部全局内容管理，选中态使用冷蓝细指示条 |
| 点缀 | 功能蓝 `#4D9FD1` / `#65AED8`，研究提示暖橙 `#C28B62`，状态绿 `#6FAF8D` |

强约束：禁紫/靛蓝；禁 Emoji 功能图标；功能图标统一使用 Lucide/Material 线形图标；禁纯平背景和均分三卡模板；全站动画统一使用 `cubic-bezier(.1,.9,.2,1)`，不得出现 `ease-in-out`。

---

## 六、后端小白协作方式

后端不要一开始同时处理模型、RAG、Neo4j 和接口联调，按两步完成：

1. 固定 JSON 阶段：先实现一个 `POST /api/agent-chat`，根据四种 `agent_type` 返回非空 `answer` 和原 `agent_type`。
2. 真实能力阶段：固定回答联调通过后，再逐个接入星辰工作流、GraphRAG、向量检索或 LoRA，保持前端稳定字段不变。

云端联调优先验证统一智能体接口和长期档案生命周期；音频转写因真实 ASR 凭证尚未配置，不作为部署成败的首要判断项，HTTP 503 属于当前预期。具体接口示例和联合验收清单见[《后端联调交接清单》](后端联调交接清单.md)。

---

## 七、改完必须自动验证

所有检查全绿才算完成：

```powershell
# 1. 编译
python -m py_compile config.py components.py pages.py app.py

# 2. AppTest 冒烟
# 临时 .py 脚本写入 %TEMP%，运行后删除。
# 覆盖：7 页 radio 切换；工作台真实编辑和 ws_stage 递进；
# 工作台向模拟/诊断传递；模拟互动 flow 变化；诊断样例、报告和溯源弹窗；
# 图谱 6 子域和节点选择；诊断结果带入科研并生成。

# 3. 真实服务
streamlit run app.py --server.headless true --server.port 8502
# 轮询 /_stcore/health 返回 ok、首页 HTTP 200、日志无 traceback，然后终止本次验证进程。
```

接口网关还应通过标准库 mock 覆盖：正常响应、超时、HTTP 500、非 JSON、业务错误、缺字段、非法数值和可选 `X-Token`。TXT 输入覆盖 UTF-8、UTF-8 BOM、GB18030、空文件、乱码及超长内容。

---

## 八、本机环境注意事项

1. 8501 被用户自己的旧 Streamlit 实例占用，验证一律使用 8502。
2. AppTest 的 `session_state` 是 `SafeSessionState`，不支持 `.get()`；使用 `try/except` 读取。
3. PowerShell 中不要用 `python -c` 承载中文、多行或复杂引号；一律写临时 `.py` 后执行。
4. 预览服务运行时修改 `components.py` 可能触发 `ReplaceFileW EIO`；先停止本次预览服务再修改。
5. 修改 `.streamlit/config.toml` 或新增 CSS 后必须重启 Streamlit。
6. 按钮宽度使用 `width="stretch"`；溯源弹窗使用 `@st.dialog`；架构图使用 `st.mermaid_chart`。

---

## 九、交接提示词

```text
继续维护这个 Streamlit 项目，路径：C:\Users\szsjdn\Desktop\街边挂帅
请先完整阅读 README.md，再按 config.py → components.py → app.py → pages.py 的顺序阅读代码。
技术栈固定为 Python 3.10.11、streamlit==1.61.1、streamlit-agraph==0.0.45，禁止新增第三方库。
严格保持 config/components/pages/app 四文件架构和现有侧边栏、色彩及交互约束。
接口契约见《API接口文档.md》，后端任务见《后端联调交接清单.md》，演示路线见《演示动线文档.md》；真实接口失败必须保留原视图与错误，Mock 只允许主动只读查看。
改完必须执行 README 第七节全部验证，端口统一使用 8502，全绿才算完成。
```
