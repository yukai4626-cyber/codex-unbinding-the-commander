# STEM教师教育“教-学-研”一体化智能体 · 前端演示 Demo

> 技术栈：Python 3.10.11 + Streamlit 1.61.1 + streamlit-agraph 0.0.45  
> 定位：可独立演示、可连接真实后端的 Streamlit 前端联调原型  
> 依赖约束：禁止新增第三方库；HTTP 请求使用 Streamlit 已依赖的 `requests`

本项目包含 7 个页面和 4 个正式业务接口。没有后端时可使用内置 Mock 数据完整演示；后端可用时，可通过环境变量切换到真实接口，单个接口失败会自动回退对应 Mock 数据。

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
$env:STEM_API_BASE = "http://127.0.0.1:8000"
$env:STEM_API_TOKEN = "测试令牌"
streamlit run app.py --server.port 8502
```

| 环境变量 | 是否必填 | 说明 |
|---|---|---|
| `STEM_MOCK_MODE` | 否 | `true` 使用内置 Mock；`false` 请求真实后端；未设置时使用 `config.py` 默认值 |
| `STEM_API_BASE` | 否 | 后端基础地址，例如 `http://127.0.0.1:8000` |
| `STEM_API_TOKEN` | 否 | 测试令牌；设置后通过请求头 `X-Token` 发送，未设置时不发送该请求头 |

令牌不得写入源码、提交记录、截图或公开日志。公网部署时应使用平台 Secrets/环境变量，并配置后端 HTTPS 地址。

---

## 二、文件职责

| 文件 | 职责 |
|---|---|
| `config.py` | `MOCK_MODE`、API 配置、7 页导航、图谱 6 子域、节点配色、全局色板、四大智能体和演示动线 |
| `components.py` | 全站 CSS、Iconify lucide 内联图标、会话状态、公共卡片与图谱组件、统一接口网关及 Mock 降级 |
| `pages.py` | 7 个页面函数与全部内置 Mock 数据，包括 61 实体/61 关系图谱、碳中和教案、诊断报告和科研方案 |
| `app.py` | 页面配置、样式与状态初始化、固定侧边栏、7 页导航和页面分发 |
| `.streamlit/config.toml` | Streamlit 控件主题；打包时不能遗漏该隐藏目录 |
| `API接口文档.md` | 4 个正式业务接口、字段契约、错误约定和后端联调方法 |
| `演示动线文档.md` | 约 2 分 55 秒的答辩与录屏脚本 |

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

| 页面 | 接口 | 主要返回内容 |
|---|---|---|
| 教学模拟 | `POST /api/sim/flow` | 心流指标、状态、虚拟学生反馈和多模态信号 |
| 智能诊断 | `POST /api/diag/report` | 问题、归因、建议和溯源子图 |
| 课程工作台 | `POST /api/workbench/design` | 三步阶段、完整教案、ITRS/STEM 评估和结论 |
| 科研孵化 | `POST /api/research/plan` | 研究选题、综述提纲、问卷和实验设计 |

知识图谱后端接口不属于本轮正式接口，图谱页继续使用内置数据。完整契约见《API接口文档.md》。

后端不可达、超时、返回非 JSON、业务报错或字段异常时，前端显示降级状态并使用对应 Mock 数据，不能让页面崩溃。Mock 数据只用于功能演示，成果页不得将其描述为真实实证结果。

---

## 五、设计体系

| 角色 | 规范 |
|---|---|
| 页面底色 | 浅米 `#F4F0E8` + 暖色径向微光 + 4% SVG 噪点，背景永不纯平 |
| 内容方块 | 深色 `rgba(34,38,48,.85)` + 噪点；标题和正文使用白色系 |
| 图谱分类文字 | `#FDFBF6` 浅色方块、浅描边、`#3A3129` 深字；颜色只作语义圆点或文字 |
| 侧边栏 | 米色 `#E8DFCF`、白色条目卡、暖棕选中底、蓝色指示条；侧边栏保持现状 |
| 点缀 | 暖棕 `#8C6E4A` / `#A67C52`，状态绿 `#2F8F4E` |

强约束：禁紫/靛蓝；禁 Emoji 功能图标；功能图标统一使用 Iconify 内联 SVG；全站动画统一使用 `cubic-bezier(.1,.9,.2,1)`，不得出现 `ease-in-out`。

---

## 六、后端小白协作方式

后端不要一开始同时处理模型、RAG、Neo4j 和接口联调，按两步完成：

1. 固定 JSON 阶段：先实现 4 个 POST 路径，接收规定 JSON，并返回与《API接口文档.md》示例同结构的固定数据。
2. 真实能力阶段：前后端固定数据联调通过后，再逐个把固定数据替换为模型、RAG 或 Neo4j 结果，字段名和类型不变。

联调顺序固定为：课程工作台 → 智能诊断 → 教学模拟 → 科研孵化。后端需提供 BaseURL、是否启用 `X-Token`、测试令牌、启动方法和可联调时间。

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
接口契约见《API接口文档.md》，演示路线见《演示动线文档.md》；真实接口失败必须自动回退 Mock。
改完必须执行 README 第七节全部验证，端口统一使用 8502，全绿才算完成。
```
