# -*- coding: utf-8 -*-
"""pages.py — 7 个页面渲染函数 + 全量 Mock 数据集

页面清单（与 config.NAV_ITEMS 一一对应）：
01 page_overview  首页·项目总览
02 page_simulation 跨学科教学模拟实训
03 page_diagnosis  智能教学诊断与反思
04 page_workbench  跨学科课程设计工作台【演示主线】
05 page_research  教育研究孵化助手
06 page_kg     技术底座·知识图谱引擎
07 page_value    成果与价值

说明：
- 本文件所有业务数据均为 Mock 示例数据（MOCK_MODE 总开关见 config.py）；
- 数据出口统一走 components.api_gate()，联调时仅需关闭 MOCK_MODE 并实现网关，
 页面布局无需任何改动；
- 演示主线（课程设计 → 知识图谱）全程以「碳中和跨学科教学」为统一案例，
 业务数据与图谱数据全链路打通。
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET

import streamlit as st
import config
import components as comp


def _agent_payload(agent_key: str, question: str) -> dict:
  """按稳定契约构造唯一允许发送给后端的两个字段。"""
  return {
    "question": question.strip(),
    "agent_type": config.AGENT_TYPES[agent_key],
  }


def _render_agent_sources(result: dict):
  """兼容后端未来新增的文档来源与图谱来源字段。"""
  if not isinstance(result, dict):
    return
  sources = result.get("sources") if isinstance(result.get("sources"), list) else []
  graph_sources = (
    result.get("graph_sources") if isinstance(result.get("graph_sources"), list) else []
  )
  if not sources and not graph_sources:
    return
  lines = []
  if sources:
    lines.append(f"文档来源：{comp.safe_text('；'.join(map(str, sources)))}")
  if graph_sources:
    lines.append(f"图谱来源：{comp.safe_text('；'.join(map(str, graph_sources)))}")
  comp.info_card(
    "回答依据",
    lines,
    icon_name="database",
    tone=config.COLORS["accent"],
    light=True,
  )

# =====================================================================
# 一、知识图谱 Mock 数据（依据《多源异构领域知识引擎》原表构建）
# =====================================================================
KG_DATA = {
  # ---- 1. 教育理论本体子图 ----
  "edu_theory": {
    "nodes": [
      {"id": "tpack", "label": "TPACK框架", "type": "理论", "domain": "教育理论本体",
       "desc": "整合技术的学科内容教学知识框架：TPACK = 学科内容知识(CK) + 教学法知识(PK) + 技术知识(TK) 的有机融合，而非简单叠加", "size": 30},
      {"id": "ck", "label": "学科内容知识·CK", "type": "理论", "domain": "教育理论本体", "desc": "教师对学科本体知识的掌握深度"},
      {"id": "pk", "label": "教学法知识·PK", "type": "理论", "domain": "教育理论本体", "desc": "通用教学策略与课堂组织方法"},
      {"id": "tk", "label": "技术知识·TK", "type": "理论", "domain": "教育理论本体", "desc": "信息技术工具及其教学应用能力"},
      {"id": "bloom", "label": "布卢姆认知目标分类", "type": "理论", "domain": "教育理论本体",
       "desc": "认知目标六层次：记忆 → 理解 → 应用 → 分析 → 评价 → 创造", "size": 28},
      {"id": "l_mem", "label": "记忆层", "type": "概念", "domain": "教育理论本体", "desc": "识记与复述类认知活动"},
      {"id": "l_und", "label": "理解层", "type": "概念", "domain": "教育理论本体", "desc": "解释、举例、分类、比较等理解活动"},
      {"id": "l_app", "label": "应用层", "type": "概念", "domain": "教育理论本体", "desc": "将概念迁移到新情境执行"},
      {"id": "l_ana", "label": "分析层", "type": "概念", "domain": "教育理论本体", "desc": "分解要素、辨析关系与因果"},
      {"id": "l_eva", "label": "评价层", "type": "概念", "domain": "教育理论本体", "desc": "基于标准作出判断与论证"},
      {"id": "l_cre", "label": "创造层", "type": "概念", "domain": "教育理论本体", "desc": "重组要素生成新方案"},
      {"id": "zpd", "label": "最近发展区理论", "type": "理论", "domain": "教育理论本体",
       "desc": "教学应走在发展前面：在现有水平与潜在水平之间提供适当支架", "size": 26},
      {"id": "meta", "label": "元认知理论", "type": "理论", "domain": "教育理论本体", "desc": "对自身认知过程的监控、反思与调节"},
      {"id": "reflect", "label": "教学反思", "type": "理论", "domain": "教育理论本体", "desc": "教师对教学设计与实施的回溯性思考"},
    ],
    "edges": [
      ("tpack", "ck", "组成"), ("tpack", "pk", "组成"), ("tpack", "tk", "组成"),
      ("bloom", "l_mem", "包含"), ("bloom", "l_und", "包含"), ("bloom", "l_app", "包含"),
      ("bloom", "l_ana", "包含"), ("bloom", "l_eva", "包含"), ("bloom", "l_cre", "包含"),
      ("zpd", "meta", "关联"), ("meta", "reflect", "支撑"),
    ],
  },
  # ---- 2. 跨学科概念与能力映射子图 ----
  "concept_map": {
    "nodes": [
      {"id": "carbon_neutral", "label": "碳中和", "type": "概念", "domain": "跨学科概念映射",
       "desc": "跨学科融合三元组：碳中和 = 化学碳循环 + 生物生态系统 + 地理能源分布 + 物理热力学", "size": 34},
      {"id": "chem_cycle", "label": "化学碳循环", "type": "概念", "domain": "跨学科概念映射", "desc": "碳元素在大气圈/水圈/岩石圈/生物圈间的化学迁移路径"},
      {"id": "bio_eco", "label": "生物生态系统", "type": "概念", "domain": "跨学科概念映射", "desc": "光合作用固碳、呼吸作用释碳与食物链碳传递"},
      {"id": "geo_energy", "label": "地理能源分布", "type": "概念", "domain": "跨学科概念映射", "desc": "能源资源的地域分布与碳排放的空间格局"},
      {"id": "phys_thermo", "label": "物理热力学", "type": "概念", "domain": "跨学科概念映射", "desc": "能量守恒与转化、温室效应中的辐射平衡"},
      {"id": "math_model", "label": "数学建模", "type": "概念", "domain": "跨学科概念映射", "desc": "用函数/统计模型刻画碳排放趋势与减排路径"},
      {"id": "eng_think", "label": "工程思维", "type": "概念", "domain": "跨学科概念映射", "desc": "约束条件下的方案设计、迭代与评估"},
      {"id": "sci_lit", "label": "科学思维素养", "type": "素养", "domain": "跨学科概念映射", "desc": "物理热力学 → 科学思维素养（STEM 课标素养映射）"},
      {"id": "soc_lit", "label": "社会责任素养", "type": "素养", "domain": "跨学科概念映射", "desc": "碳中和 → 社会责任素养（可持续发展观念）"},
      {"id": "inq_lit", "label": "探究实践素养", "type": "素养", "domain": "跨学科概念映射", "desc": "提出问题、设计实验、收集证据、得出结论"},
      {"id": "miscon_heat", "label": "学生迷思·热量即温度", "type": "问题", "domain": "跨学科概念映射", "desc": "学生认知迷思：混淆“热量”与“温度”两个概念"},
      {"id": "miscon_model", "label": "学生迷思·建模畏难", "type": "问题", "domain": "跨学科概念映射", "desc": "学生认知迷思：难以将数学模型迁移到社科情境"},
    ],
    "edges": [
      ("carbon_neutral", "chem_cycle", "融合"), ("carbon_neutral", "bio_eco", "融合"),
      ("carbon_neutral", "geo_energy", "融合"), ("carbon_neutral", "phys_thermo", "融合"),
      ("phys_thermo", "sci_lit", "素养映射"), ("carbon_neutral", "soc_lit", "素养映射"),
      ("chem_cycle", "miscon_heat", "易发迷思"), ("math_model", "miscon_model", "易发迷思"),
      ("math_model", "eng_think", "关联"), ("sci_lit", "inq_lit", "协同"),
    ],
  },
  # ---- 3. 跨学科教学案例子图 ----
  "case_lib": {
    "nodes": [
      {"id": "case_cn", "label": "碳中和跨学科教案", "type": "案例", "domain": "跨学科教学案例",
       "desc": "七跨七融：主题融合(物理+化学+生物+地理) + 方法融合(探究式学习) + 素养融合(科学思维+社会责任)", "size": 32},
      {"id": "qiqiao", "label": "七跨七融标签体系", "type": "概念", "domain": "跨学科教学案例", "desc": "跨学科课例的多维标签框架"},
      {"id": "tag_theme", "label": "主题融合", "type": "概念", "domain": "跨学科教学案例", "desc": "物理热力学 + 化学碳循环 + 生物生态系统 + 地理能源分布"},
      {"id": "tag_method", "label": "方法融合", "type": "概念", "domain": "跨学科教学案例", "desc": "探究式学习 + 问题链驱动"},
      {"id": "tag_lit", "label": "素养融合", "type": "概念", "domain": "跨学科教学案例", "desc": "科学思维 + 社会责任"},
      {"id": "inquiry", "label": "探究式学习", "type": "方法", "domain": "跨学科教学案例", "desc": "以问题驱动、证据建构为核心的学习方式"},
      {"id": "problem_chain", "label": "问题链驱动", "type": "方法", "domain": "跨学科教学案例", "desc": "由浅入深的问题序列串联教学主线"},
      {"id": "record_carbon", "label": "课堂实录·校园碳足迹调查", "type": "案例", "domain": "跨学科教学案例", "desc": "脱敏转录：学生围绕校园碳足迹数据展开小组探究"},
      {"id": "conflict_strategy", "label": "冲突解决策略", "type": "方法", "domain": "跨学科教学案例", "desc": "认知冲突出现时的引导与化解策略模板"},
      {"id": "reflect_teacher", "label": "教师反思记录", "type": "案例", "domain": "跨学科教学案例", "desc": "授课教师对融合设计与实施的反思要点"},
    ],
    "edges": [
      ("case_cn", "tag_theme", "标注"), ("case_cn", "tag_method", "标注"), ("case_cn", "tag_lit", "标注"),
      ("qiqiao", "tag_theme", "包含"), ("qiqiao", "tag_method", "包含"), ("qiqiao", "tag_lit", "包含"),
      ("case_cn", "inquiry", "采用"), ("case_cn", "problem_chain", "采用"),
      ("case_cn", "record_carbon", "包含"), ("conflict_strategy", "inquiry", "支撑"),
      ("reflect_teacher", "case_cn", "反思对象"),
    ],
  },
  # ---- 4. 课堂教学行为模式子图 ----
  "behavior": {
    "nodes": [
      {"id": "leap", "label": "概念跃迁过大", "type": "问题", "domain": "课堂行为模式",
       "desc": "新手教师典型问题：概念跃迁过大 = 认知阶梯缺失 + 学生困惑 + 调整策略(分解概念)", "size": 30},
      {"id": "no_ladder", "label": "认知阶梯缺失", "type": "问题", "domain": "课堂行为模式", "desc": "未在现有水平与目标概念之间搭建中间支架"},
      {"id": "stu_confuse", "label": "学生困惑", "type": "问题", "domain": "课堂行为模式", "desc": "多模态可观测的认知困惑状态（皱眉/迟疑/追问）"},
      {"id": "fix_decompose", "label": "调整策略·分解概念", "type": "方法", "domain": "课堂行为模式", "desc": "将大概念分解为阶梯式子概念逐一突破"},
      {"id": "fast_speech", "label": "语速过快", "type": "行为", "domain": "课堂行为模式", "desc": "多模态教学行为特征：语速过快诱发认知负荷升高"},
      {"id": "question_chain_s", "label": "提问链策略", "type": "行为", "domain": "课堂行为模式", "desc": "优秀课堂互动策略：分层递进的提问设计"},
      {"id": "group_coop", "label": "小组合作策略", "type": "行为", "domain": "课堂行为模式", "desc": "优秀课堂互动策略：异质分组与角色分工"},
      {"id": "mm_behavior", "label": "多模态教学行为特征", "type": "行为", "domain": "课堂行为模式", "desc": "语音/视觉/交互三维度的教学行为指纹"},
    ],
    "edges": [
      ("leap", "no_ladder", "归因"), ("leap", "stu_confuse", "导致"),
      ("fix_decompose", "leap", "缓解"), ("stu_confuse", "fix_decompose", "触发调整"),
      ("fast_speech", "stu_confuse", "加剧"), ("question_chain_s", "group_coop", "配合"),
      ("mm_behavior", "fast_speech", "特征包含"),
    ],
  },
  # ---- 5. 教育科研方法子图 ----
  "research": {
    "nodes": [
      {"id": "qual", "label": "质性研究", "type": "方法", "domain": "教育科研方法", "desc": "访谈、观察、文本分析等解释性研究范式"},
      {"id": "quant", "label": "量化研究", "type": "方法", "domain": "教育科研方法", "desc": "量表测量、统计推断等验证性研究范式"},
      {"id": "dbr", "label": "设计型研究(DBR)", "type": "方法", "domain": "教育科研方法",
       "desc": "设计—实施—评估—迭代的循证改进范式", "size": 26},
      {"id": "survey_design", "label": "问卷设计", "type": "方法", "domain": "教育科研方法", "desc": "构念操作化与量表编制规范"},
      {"id": "exp_design", "label": "实验设计", "type": "方法", "domain": "教育科研方法", "desc": "准实验前测-后测对照设计"},
      {"id": "writing", "label": "学术写作规范", "type": "方法", "domain": "教育科研方法", "desc": "选题—文献—方法—结论的写作链条"},
      {"id": "interview", "label": "访谈提纲", "type": "方法", "domain": "教育科研方法", "desc": "半结构化访谈工具设计"},
      {"id": "pain_transfer", "label": "教学问题·跨学科迁移困难", "type": "问题", "domain": "教育科研方法",
       "desc": "学生难以将数学模型应用于社科案例（课堂认知冲突数据锚点）", "size": 26},
      {"id": "topic_transfer", "label": "研究选题·数学模型迁移机制研究", "type": "方法", "domain": "教育科研方法",
       "desc": "“教学问题-研究选题”关联三元组：迁移困难 → 《数学模型在社科教学中的迁移机制研究》", "size": 30},
    ],
    "edges": [
      ("pain_transfer", "topic_transfer", "问题-选题转化"),
      ("topic_transfer", "dbr", "采用范式"), ("dbr", "survey_design", "配套工具"),
      ("dbr", "exp_design", "配套工具"), ("quant", "survey_design", "支撑"),
      ("qual", "interview", "支撑"), ("writing", "topic_transfer", "写作规范"),
    ],
  },
  # ---- 6. 师范生成长循证评估子库 ----
  "growth": {
    "nodes": [
      {"id": "stu_a", "label": "师范生A", "type": "评估", "domain": "成长循证评估",
       "desc": "成长轨迹：ITRS前测60分 → 教案迭代3版 → 诊断报告(概念跃迁过大) → 后测80分", "size": 30},
      {"id": "itrs_pre", "label": "ITRS前测·60分", "type": "评估", "domain": "成长循证评估", "desc": "ITRS 量表前测得分（干预前基线）"},
      {"id": "itrs_post", "label": "ITRS后测·80分", "type": "评估", "domain": "成长循证评估", "desc": "ITRS 量表后测得分（干预后 +20 分）"},
      {"id": "lesson_iter", "label": "教案迭代·3版", "type": "评估", "domain": "成长循证评估", "desc": "人机协同迭代 3 版的过程性记录"},
      {"id": "diag_leap", "label": "诊断报告·概念跃迁过大", "type": "评估", "domain": "成长循证评估", "desc": "实训诊断过程数据：识别“概念跃迁过大”问题"},
      {"id": "growth_track", "label": "成长轨迹图谱", "type": "评估", "domain": "成长循证评估",
       "desc": "师范生A → ITRS得分提升 → 跨学科概念掌握度提升 → 案例难度提升", "size": 28},
      {"id": "concept_mastery", "label": "跨学科概念掌握度", "type": "评估", "domain": "成长循证评估", "desc": "对跨学科融合三元组的理解与迁移水平"},
      {"id": "case_difficulty", "label": "案例难度提升", "type": "评估", "domain": "成长循证评估", "desc": "按能力分层推送的案例难度自适应升级"},
    ],
    "edges": [
      ("stu_a", "itrs_pre", "前测"), ("stu_a", "itrs_post", "后测"),
      ("stu_a", "lesson_iter", "迭代记录"), ("stu_a", "diag_leap", "诊断数据"),
      ("growth_track", "stu_a", "汇聚"), ("itrs_post", "concept_mastery", "正相关"),
      ("concept_mastery", "case_difficulty", "推动"),
    ],
  },
}

# 跨子域关联边（仅在“全局总览”合并视图中出现，虚线表示）
KG_CROSS_EDGES = [
  ("carbon_neutral", "case_cn", "案例关联", True),
  ("case_cn", "sci_lit", "素养达成", True),
  ("tpack", "phys_thermo", "学科内容知识", True),
  ("leap", "zpd", "理论溯源", True),
  ("question_chain_s", "bloom", "策略依据", True),
  ("diag_leap", "leap", "诊断关联", True),
  ("growth_track", "topic_transfer", "数据支撑", True),
  ("stu_confuse", "dbr", "研究触发", True),
]


def _build_overview():
  """合并 6 大子域为全局总览视图（去重 + 追加跨域边）。"""
  nodes, seen, edges = [], set(), []
  for dom in config.KG_SUBDOMAINS:
    for n in KG_DATA[dom["id"]]["nodes"]:
      if n["id"] not in seen:
        seen.add(n["id"])
        nodes.append(dict(n))
    edges.extend(KG_DATA[dom["id"]]["edges"])
  edges.extend(KG_CROSS_EDGES)
  return {"nodes": nodes, "edges": edges}


KG_OVERVIEW = _build_overview()

# 诊断页「图谱溯源」局部子图：问题 → 理论 → 案例 可溯源链路
TRACE_GRAPH = {
  "nodes": [
    {"id": "p1", "label": "问题①提问仅覆盖记忆/理解层", "type": "问题", "domain": "诊断报告",
     "desc": "32 次课堂提问中 28 次为复述类问题，缺少分析/评价层触发", "size": 30},
    {"id": "p2", "label": "问题②概念跃迁过大", "type": "问题", "domain": "诊断报告",
     "desc": "由“温室效应现象”直接跃迁至“热力学计算”，学生困惑峰值出现在第 17 分钟", "size": 30},
    {"id": "p3", "label": "问题③跨学科简单相加", "type": "问题", "domain": "诊断报告",
     "desc": "化学与地理环节各自独立，缺少融合任务串联", "size": 30},
    {"id": "t1", "label": "布卢姆认知目标分类", "type": "理论", "domain": "教育理论本体", "desc": "理论锚点：提问层次应覆盖记忆→创造六层"},
    {"id": "t2", "label": "最近发展区理论", "type": "理论", "domain": "教育理论本体", "desc": "理论锚点：教学应走在发展前面，搭建认知支架"},
    {"id": "t3", "label": "TPACK框架", "type": "理论", "domain": "教育理论本体", "desc": "理论锚点：学科内容知识与教学法、技术的有机整合"},
    {"id": "c1", "label": "优质提问链课例", "type": "案例", "domain": "跨学科教学案例", "desc": "支撑案例：记忆→理解→应用→分析 四层问题链设计示范"},
    {"id": "c2", "label": "碳中和教案·七跨七融", "type": "案例", "domain": "跨学科教学案例", "desc": "支撑案例：主题融合 + 方法融合 + 素养融合的完整样例"},
    {"id": "c3", "label": "认知阶梯搭建策略模板", "type": "案例", "domain": "课堂行为模式", "desc": "支撑案例：分解概念、逐级支架的行为模板"},
    {"id": "b1", "label": "认知阶梯缺失", "type": "行为", "domain": "课堂行为模式", "desc": "行为归因：未搭建中间概念支架"},
  ],
  "edges": [
    ("p1", "t1", "理论溯源"), ("t1", "c1", "案例支撑"),
    ("p2", "t2", "理论溯源"), ("t2", "c3", "案例支撑"), ("p2", "b1", "行为归因"),
    ("p3", "t3", "理论溯源"), ("t3", "c2", "案例支撑"),
  ],
}

# =====================================================================
# 二、课程设计工作台 Mock 数据（演示主线 · 碳中和案例）
# =====================================================================
LESSON_TEMPLATE = """## 跨学科教学设计 · 《碳中和：校园绿色行动》

**学段**：{grade}　|　**主题**：{topic}　|　**课时**：{hours} 课时　|　**类型**：跨学科项目式学习

**七跨七融标签**：`主题融合`（物理热力学+化学碳循环+生物生态系统+地理能源分布）｜`方法融合`（探究式学习+问题链驱动）｜`素养融合`（科学思维+社会责任）

---

### 一、情境导入 · 校园碳足迹大调查（约 8 分钟）
以校园真实数据切入，制造认知冲突：
- 食堂日均厨余 **120 kg**；教室空调能耗高峰集中在 14:00—16:00；
- 驱动性问题：**“我们的校园，如何一步步实现碳中和？”**

### 二、问题链设计（约 10 分钟）
1. **Q1（化学）**：“碳”在校园里走过哪些旅程？——认识化学碳循环；
2. **Q2（地理）**：校园的碳排放最终“排”向了哪里？——能源分布与空间格局；
3. **Q3（生物）**：植物能帮我们“吸”回多少碳？——生态系统固碳；
4. **Q4（物理）**：用什么物理量度量能量的流动？——热力学与温室效应；
5. **Q5（工程/数学）**：设计可行的校园碳中和方案需要哪些数据？——数学建模与工程决策。

### 三、实验与活动设计
| 活动 | 学科融合点 | 素养指向 |
|---|---|---|
| 活动一：碳循环模拟实验 | 化学 + 生物 | 科学思维、探究实践 |
| 活动二：校园绿植固碳量测算 | 生物 + 数学 | 数学建模、证据意识 |
| 活动三：光伏发电 vs 空调能耗核算 | 物理 + 工程 | 工程思维、社会责任 |

### 四、评价量表（七跨七融观测点）
| 素养维度 | 观测指标 | 评价方式 |
|---|---|---|
| 科学思维 | 能基于证据解释碳循环与能量流动 | 问题链作答 + 方案答辩 |
| 数学建模 | 能用函数拟合校园碳排放趋势 | 固碳量测算报告 |
| 工程实践 | 能提出可执行的减排方案 | 方案发布会互评 |
| 社会责任 | 关注碳减排与可持续发展 | 家庭碳账本记录 |

### 五、反思与延伸
小组方案发布会（互评 + 教师点评）→ 课后延伸：**家庭碳账本** 一周记录挑战。
"""

EDIT_MARK_MD = """---

> ### 人工迭代修正记录（人主导 · Human-in-the-Loop）
> 1. 问题链由 **3 问扩展为 5 问**，补齐“应用—分析”层级（对应布卢姆认知目标分类）；
> 2. 增加**热力学实验安全预案**与器材清单，降低实验风险；
> 3. 将“教师讲授碳循环”调整为**学生模拟实验 + 模型建构**，降低认知负荷。
"""

CHECK_MARK_MD = """---

### 素养对齐校验结果（AI 校验 · 可溯源）
- **结论**：素养对齐校验通过，综合达标率 **92%**
- **证据链**：科学思维 ← 问题链 Q4/Q5（物理热力学 → 科学思维素养）；社会责任 ← 情境导入与方案发布会（碳中和 → 社会责任素养）；数学建模 ← 活动二固碳量测算；
- **待强化**：工程实践维度（70%）建议增加“光伏方案原型搭建”环节，强化 Human-in-the-Loop 迭代。
"""

CHECK_CONCLUSION = (
  "结论：素养对齐校验通过，综合达标率 92%。"
  "证据链：科学思维 ← 问题链 Q4/Q5（物理热力学 → 科学思维素养）；社会责任 ← 情境导入与方案发布会（碳中和 → 社会责任素养）；数学建模 ← 活动二固碳量测算。"
  "待强化：工程实践维度（70%）建议增加“光伏方案原型搭建”环节。"
)

ITRS_DIMS = [
  ("跨学科教学设计能力", 82.0, "#8C6E4A"),
  ("教学实施与调控能力", 75.0, "#A67C52"),
  ("技术融合应用能力", 78.0, "#6B6252"),
  ("元认知反思能力", 80.0, "#7A8B6F"),
]
STEM_DIMS = [
  ("科学思维", 86.0, "#8C6E4A"),
  ("数学建模", 72.0, "#A67C52"),
  ("工程实践", 70.0, "#6B6252"),
  ("技术应用", 81.0, "#7A8B6F"),
  ("社会责任", 90.0, "#4F5D4A"),
]

# =====================================================================
# 三、智能诊断 Mock 报告
# =====================================================================
DIAG_REPORT = {
  "meta": "课例主题：碳中和跨学科教学 ｜ 数据源：课例文本（Mock 示例）",
  "problems": [
    {
      "id": "P1",
      "title": "提问层次集中于低阶认知",
      "evidence": "32 次课堂提问中 28 次为复述/识记类问题，仅覆盖布卢姆“记忆 / 理解”层。",
      "cause": "问题链设计缺乏“分析 / 评价 / 创造”层支架，未触发高阶思维。",
      "suggest": "引入“比较碳排放方案优劣（评价层）”“设计校园减排路线图（创造层）”类问题。",
      "anchor": "布卢姆认知目标分类",
    },
    {
      "id": "P2",
      "title": "概念跃迁过大 · 认知阶梯缺失",
      "evidence": "从“温室效应现象”直接跃迁至“热力学计算”，虚拟学生困惑峰值出现在第 17 分钟。",
      "cause": "违反最近发展区理论：未在现象与公式之间搭建中间概念支架。",
      "suggest": "分解概念：先做“温度—热量”辨析，再引入能量守恒，最后进入定量计算。",
      "anchor": "最近发展区理论",
    },
    {
      "id": "P3",
      "title": "跨学科“简单相加”而非融合",
      "evidence": "化学碳循环与地理能源环节各自独立，缺少融合任务串联，学生无法建立跨学科关联。",
      "cause": "TPACK 框架中的学科内容知识（CK）整合不足，多学科知识呈“拼盘”状态。",
      "suggest": "以“校园碳中和方案”总任务串联多学科，参照碳中和案例子图的“七跨七融”标签重构。",
      "anchor": "TPACK框架",
    },
  ],
  "conclusion": (
    "反向归因结论：以 AI 虚拟学生实时认知困惑数据为锚点，反向定位出三处教学缺陷——"
    "① 提问层次偏低（32 问中 28 问为低阶复述）；② 第 17 分钟出现概念跃迁过大（认知阶梯缺失）；"
    "③ 跨学科环节呈“拼盘式”拼接。三项结论均有教育理论锚点与优秀案例支撑，全部可溯源。"
  ),
  "suggests": [
    "按布卢姆六层次重构问题链，保证每 10 分钟出现 1 个分析层以上问题",
    "在第 12—18 分钟区间插入“温度—热量—能量守恒”三级支架",
    "以总任务驱动融合：将三节独立环节合并为“校园碳中和方案”项目式任务",
  ],
}

# =====================================================================
# 四、教学模拟实训 Mock 数据
# =====================================================================
SIM_THEMES = ["碳中和·跨学科教学（主线案例）", "丝绸之路·文史地融合", "智慧校园·工程实践"]

VIRTUAL_STUDENTS = [
  {"name": "小雨", "role": "概念跃迁困惑", "emoji": "brain", "color": "#8C6E4A", "msgs": [
    "老师，为什么升温会让冰川融化？热量和温度到底有什么区别呀……",
    "我还是分不清“碳循环”里碳到底是怎么从大气跑到植物里的……",
    "如果温度不变，热量还会传递吗？我想不通。",
  ]},
  {"name": "小航", "role": "跨学科迁移障碍", "emoji": "sigma", "color": "#A67C52", "msgs": [
    "老师，为什么要用数学公式算碳排放？我们不是在学地理吗……",
    "这个函数图像我看懂了，但和碳中和有什么关系？",
    "数学模型好抽象，能不能直接给结论呀？",
  ]},
  {"name": "思思", "role": "高参与探究型", "emoji": "sparkles", "color": "#4F7A5E", "msgs": [
    "老师！我查到我们学校食堂每天厨余有 120 千克，这个算碳足迹吗？",
    "我们小组想对比光伏发电和空调耗电，可以吗？",
    "植物固碳的速率和季节有关系吗？我们想做个实验验证！",
  ]},
  {"name": "浩然", "role": "边缘参与", "emoji": "moon", "color": "#968D7B", "msgs": [
    "（小声）这个和我们以后当老师有什么关系……",
    "老师讲得有点快，我还没抄完笔记……",
    "这个小组活动，我可以只负责记录吗？",
  ]},
  {"name": "一诺", "role": "批判性提问型", "emoji": "target", "color": "#5C6B7A", "msgs": [
    "老师，为什么先讲化学再讲地理？这两个顺序能换吗？",
    "这个实验只能说明碳循环的一部分吧？还有别的因素没考虑。",
    "如果数据不准确，我们算出来的“碳中和方案”还有意义吗？",
  ]},
]

TEACHER_INPUT_DEMO = (
  "同学们，今天我们一起来学习“碳中和”。首先请大家回忆一下，什么是温室效应？"
  "（等待学生回答）很好。接下来我们直接看热力学的计算公式……"
)


def _reset_flow():
  st.session_state["flow"] = {"load": 46.0, "engage": 55.0, "confuse": 52.0, "flow": 58.0}
  st.session_state["sim_round"] = 0
  st.session_state["flow_status"] = ""
  st.session_state["sim_feedback"] = None
  st.session_state["sim_signals"] = None
  st.session_state["sim_agent_result"] = None


def _mock_flow_result(r):
  """确定性生成本地心流结果，供演示模式或统一接口失败时回退。"""
  f = {
    "engage": float(min(96, 55 + r * 7 + (r % 2) * 4)),
    "confuse": float(max(12, 52 - r * 6 + (r % 3) * 3)),
    "load": float(max(18, 46 - r * 4 + (r % 2) * 2)),
    "flow": float(min(97, 58 + r * 6 + (r % 2) * 2)),
  }
  status = "深度心流" if f["flow"] >= 75 else ("心流平稳" if f["flow"] >= 55 else "心流偏低")
  return {"flow": f, "status": status, "feedback": None, "signals": None}


def _bounded_percentage(value, fallback):
  """将接口百分比收敛到 0—100；非法值回退到对应 Mock 数值。"""
  try:
    number = float(value)
  except (TypeError, ValueError):
    number = float(fallback)
  return min(100.0, max(0.0, number))


def _advance_flow(theme, utterance):
  """模拟学生互动：统一调用 /api/agent-chat，失败自动回退本地互动数据。"""
  r = st.session_state["sim_round"] + 1
  mock_res = _mock_flow_result(r)
  question = (
    "请作为 STEM 教师学习辅导智能体，根据下面的授课主题和教师话语，"
    "指出学生可能出现的认知困惑，并给出下一轮课堂互动建议。\n"
    f"授课主题：{theme}\n"
    f"教师话语：{(utterance or '')[:300]}\n"
    f"当前互动轮次：第 {r} 轮"
  )
  res = comp.api_gate(
    config.API_ENDPOINTS["sim_flow"],
    _agent_payload("sim_flow", question),
    mock_result=mock_res,
  )
  if not comp.accept_result("02", res, "interaction", "interaction"):
    return
  st.session_state["sim_round"] = r
  if not isinstance(res, dict):
    res = mock_res
  is_real = comp.is_agent_response(res)
  flow = mock_res["flow"] if is_real else res.get("flow")
  st.session_state["flow"] = {
    key: _bounded_percentage(
      flow.get(key) if isinstance(flow, dict) else None,
      fallback,
    )
    for key, fallback in mock_res["flow"].items()
  }
  st.session_state["flow_status"] = (
    "学习辅导智能体已生成本轮课堂建议"
    if is_real else str(res.get("status", "") or "")
  )
  feedback = (
    [{"name": "学习辅导智能体", "role": "课堂互动建议", "text": res["answer"]}]
    if is_real else res.get("feedback")
  )
  signals = None if is_real else res.get("signals")
  st.session_state["sim_feedback"] = feedback if isinstance(feedback, list) else None
  st.session_state["sim_signals"] = signals if isinstance(signals, list) else None
  st.session_state["sim_agent_result"] = res if is_real else None


def _sim_signals():
  r = st.session_state["sim_round"]
  f = st.session_state["flow"]
  return [
    ("语音韵律", "韵律紧张度", max(15.0, 48 - r * 3 - f["confuse"] * 0.1), "mic", "#8C6E4A"),
    ("面部表情", "积极表情占比", min(96.0, 50 + f["engage"] * 0.4 + r * 2), "smile", "#A67C52"),
    ("视觉注意力", "注视焦点稳定度", min(95.0, 45 + f["engage"] * 0.45), "eye", "#6B6252"),
    ("生理唤醒", "心率唤醒强度", max(10.0, 55 + f["load"] * 0.3 - r * 2), "heart-pulse", "#7A8B6F"),
    ("交互行为", "举手/提问频次", min(95.0, 35 + f["engage"] * 0.5 + r * 3), "hand", "#4F5D4A"),
  ]


# =====================================================================
# 五、教育研究孵化 Mock 数据
# =====================================================================
RESEARCH_TOPIC_MD = """## 研究选题

### 《基于课堂认知冲突数据的数学模型迁移机制研究——以“碳中和”跨学科教学为例》

**选题依据**
1. **数据驱动**：教学模拟实训全流程捕获的多模态认知冲突数据表明，学生“跨学科迁移困难”高频出现（本案例中第 17 分钟困惑峰值即源于此）；
2. **图谱支撑**：经教育科研方法子图自动关联，“教学问题—研究选题”三元组命中“设计型研究（DBR）”范式；
3. **闭环价值**：研究成果可反哺知识图谱（沉淀迁移障碍的教学策略），服务师范生全周期培养。

**创新点**
- 以**课堂微观认知冲突数据**为研究锚点，区别于传统经验型选题；
- 建立“教学问题 → 科研选题 → 工具初稿”的**图谱化自动孵化链路**。

**研究范式**：设计型研究（Design-Based Research，DBR）
"""

DEFAULT_RESEARCH_PAIN = (
  "学生难以将数学模型应用于社科案例：在“碳中和”教学中，学生能解数学题，"
  "但无法把函数模型迁移到碳排放趋势分析上，课堂认知冲突数据在第 17 分钟出现困惑峰值。"
)

LIT_OUTLINE_MD = """## 文献综述提纲

1. **数学建模教学与迁移困境研究**
  - 数学建模素养的课程定位与培养路径
  - 跨学科迁移障碍的认知机理（迷思概念、表征转换）
2. **认知冲突与学习机制研究**
  - 认知冲突的多模态观测指标（表情 / 语音 / 交互）
  - 冲突强度与学习成效的关系实证
3. **设计型研究（DBR）范式**
  - DBR 的方法论基础与迭代设计原则
  - DBR 在教育技术研究中的应用案例
4. **“碳中和”跨学科课程研究**
  - 七跨七融标签体系与融合教学设计
  - 跨学科项目式学习的效果评估
5. **研究述评与空白**
  - 现有研究多聚焦“教”，缺乏从课堂数据到科研选题的闭环证据
"""

SURVEY_DRAFT_MD = """## 问卷初稿（ITRS 衍生 · 数学建模迁移维度）

**引言**：亲爱的同学，本问卷用于了解你在“碳中和”跨学科学习中的真实体验，答案无对错之分，仅用于教学研究。

| 题项 | 完全不符 → 完全符合 |
|---|---|
| 1. 我能将函数模型与校园碳排放问题建立联系 | 1—2—3—4—5 |
| 2. 面对社科情境，我知道从哪里入手建立数学模型 | 1—2—3—4—5 |
| 3. 我能解释数学模型中每个参数的实际含义 | 1—2—3—4—5 |
| 4. 当模型与现实数据不符时，我会主动修正模型 | 1—2—3—4—5 |
| 5. 我愿意在后续学习中继续尝试数学建模任务 | 1—2—3—4—5 |

**计分**：Likert 5 级计分；第 1—4 题构成“迁移能力”分量表，第 5 题为“迁移倾向”单题。
"""

EXP_DRAFT_MD = """## 实验设计初稿（准实验 · 前测—后测对照）

- **研究问题**：基于课堂认知冲突数据的干预能否提升师范生数学建模迁移能力？
- **对象**：某师范院校 30 名师范生（实验组 15 人 / 对照组 15 人）
- **设计**：准实验前测—后测对照设计（干预周期 4 周）
- **干预**：实验组使用“教学模拟实训 + 诊断反思 + 课程设计工作台”全流程；对照组使用常规微格教学
- **工具**：ITRS 量表（前后测）+ 认知冲突日志 + 半结构化访谈提纲
- **分析**：配对样本 t 检验 + 效应量（Cohen's d）+ 访谈编码质性分析
"""

# =====================================================================
# 六、成果价值页 Mock 数据
# =====================================================================
LANDING_STATS = [
  ("2 所", "试点师范院校", "+1 所筹备中", "school"),
  ("45 人", "覆盖师范生", "≥5 人/轮测试", "graduation-cap"),
  ("120 份", "生成跨学科教案", "含 18 份碳中和教案", "file-text"),
  ("8,500+", "图谱三元组", "6 大子域持续扩充", "database"),
  ("90 份", "智能诊断报告", "循证诊断全覆盖", "search"),
  ("18 项", "科研选题孵化", "教学问题自动转化", "flask-conical"),
]

ITRS_PRE = [62.3, 64.1, 60.8, 58.9]
ITRS_POST = [78.5, 76.2, 79.3, 75.8]
ITRS_DIM_NAMES = ["跨学科教学设计", "教学实施与调控", "技术融合应用", "元认知反思"]


def _goto(pid):
  st.session_state["nav_radio"] = pid


# =====================================================================
# 页面 01 · 首页·项目总览
# =====================================================================
def page_overview(view):
  if view == "intro":
    lead, pulse = st.columns([1.65, 1], gap="large")
    with lead:
      comp.section_title("项目定位")
      st.write(config.PROJECT_POSITION)
      st.caption("围绕教学模拟、诊断反思、课程设计与科研孵化开展教师实践。")
      st.button("进入课程设计工作台", type="primary", on_click=_goto, args=("04",), key="overview_start")
    with pulse:
      comp.info_card(
        "当前演示闭环",
        ["课程设计 → 教学模拟", "课例诊断 → 反思改进", "教学问题 → 教育研究"],
        icon_name="route", tone=config.COLORS["primary"],
      )
      comp.mock_badge()
  elif view == "architecture":
      comp.section_title("系统整体架构", "应用层 → 能力层 → 知识图谱底座 → 教-学-研闭环")
      st.mermaid_chart("""%%{init: {"theme": "base", "themeVariables": {
      "fontFamily": "Segoe UI, Microsoft YaHei, sans-serif",
      "background": "#121922",
      "primaryColor": "#19232E",
      "primaryTextColor": "#EDF3F7",
      "primaryBorderColor": "#4D9FD1",
      "lineColor": "#7792A4",
      "clusterBkg": "#111A23",
      "clusterBorder": "#304757",
      "edgeLabelBackground": "#121922"
    }}}%%
    graph TD
     subgraph APP["应用层 · 四大业务智能体"]
      A1["高保真跨学科教学模拟智能体"]
      A2["因材施教智能教学诊断与反思智能体"]
      A3["人机协同跨学科课程设计智能工作台"]
      A4["课堂数据驱动教育研究孵化智能伙伴"]
     end
     subgraph CAP["能力层 · 核心引擎"]
      C1["全维度多模态感知框架"]
      C2["图增强双路 GraphRAG"]
      C3["学生认知反向归因引擎"]
      C4["心流自适应引擎"]
      C5["Human-in-the-Loop 协同机制"]
     end
     subgraph KG["技术底座 · 多源异构动态语义知识图谱"]
      K1["教育理论本体"]
      K2["跨学科概念映射"]
      K3["跨学科教学案例"]
      K4["课堂行为模式"]
      K5["教育科研方法"]
      K6["师范生成长评估"]
     end
     APP --> CAP --> KG
     A1 -->|实训多模态数据| A2
     A2 -->|诊断反哺设计| A3
     A3 -->|教学问题转化| A4
     A4 -->|研究成果沉淀| KG
     KG -->|图谱驱动仿真| A1
     classDef appNode fill:#192631,stroke:#4D9FD1,color:#EDF3F7,stroke-width:1.4px
     classDef capNode fill:#202A33,stroke:#C28B62,color:#EDF3F7,stroke-width:1.4px
     classDef kgNode fill:#17232C,stroke:#6FAF8D,color:#EDF3F7,stroke-width:1.4px
     class A1,A2,A3,A4 appNode
     class C1,C2,C3,C4,C5 capNode
     class K1,K2,K3,K4,K5,K6 kgNode
     style APP fill:#101820,stroke:#304757,color:#EDF3F7,stroke-width:1px
     style CAP fill:#101820,stroke:#304757,color:#EDF3F7,stroke-width:1px
     style KG fill:#101820,stroke:#304757,color:#EDF3F7,stroke-width:1px
     linkStyle default stroke:#7792A4,stroke-width:1.2px,color:#C5D0D8
    """)
  elif view == "capabilities":
    capability_columns = st.columns([1.15, .85], gap="large")
    for i, ag in enumerate(config.AGENTS):
      with capability_columns[0 if i in (0, 3) else 1]:
        with st.container(border=True):
          st.subheader(ag["name"])
          st.write(ag["advantage"])
          with st.expander("详细说明", key="capability_" + ag["page_id"]):
            for line in ag["breakthroughs"]:
              st.write(line)
          st.button("进入页面", key="jump_" + ag["page_id"], on_click=_goto, args=(ag["page_id"],))


def _start_simulation():
  """开始一次新模拟；此操作只重置本地状态，不请求接口。"""
  _reset_flow()
  st.session_state["sim_started"] = True
  comp.set_view("02", "interaction")


def _transcribe_sim_audio():
  """在控件创建前执行转写回调，安全更新授课文本 widget 状态。"""
  uploaded = st.session_state.get("sim_audio_file")
  if uploaded is None:
    return
  audio_bytes = uploaded["data"]
  if len(audio_bytes) > 50 * 1024 * 1024:
    st.session_state["sim_transcribe_notice"] = "音频超过 50 MB，请压缩或分段上传。"
    return
  transcript = comp.transcribe_audio(uploaded["name"], audio_bytes, uploaded["type"])

  if transcript:
    st.session_state["sim_transcript"] = transcript


def _apply_transcript(append=False):
  transcript = st.session_state.get("sim_transcript", "").strip()
  previous = st.session_state.get("sim_teacher_input", "").strip()
  text = f"{previous}\n\n{transcript}" if append and previous else transcript
  if len(text) > 5000 and not st.session_state.get("sim_transcribe_truncate"):
    return
  st.session_state["sim_teacher_input"] = text[:5000]
  st.session_state["sim_transcribe_notice"] = "已追加到授课文本。" if append else "已替换授课文本。"


def _audio_changed():
  uploaded = st.session_state.get("sim_audio_upload")
  st.session_state["sim_audio_file"] = ({"name": uploaded.name, "type": uploaded.type or "audio/wav", "data": uploaded.getvalue()} if uploaded is not None else None)
  st.session_state["sim_transcribe_notice"] = "待转写：确认音频后点击转写按钮。"
  st.session_state["sim_transcript"] = ""
  st.session_state.pop("sim_transcribe_truncate", None)


def page_simulation(view):
  st.session_state.setdefault("sim_theme", SIM_THEMES[0])
  theme = st.session_state["sim_theme"]
  teacher_input = st.session_state.get("sim_teacher_input", "")
  if view == "prepare":
    comp.section_title("授课输入区")
    theme = comp.draft_widget("selectbox", "实训主题", options=SIM_THEMES, key="sim_theme")
    teacher_input = comp.draft_widget("text_area",
      "语音 / 文本授课输入",
      height=130,
      placeholder="输入你的授课片段（语音识别文本或手动录入）……",
      key="sim_teacher_input",
    )
    audio_upload = st.file_uploader(
      "上传授课音频",
      type=["wav", "mp3", "m4a", "ogg", "webm"],
      max_upload_size=50,
      help="上传后可试听；转写调用 POST /api/transcribe，先预览返回的 text，再选择替换或追加。",
      key="sim_audio_upload",
      on_change=_audio_changed,
    )
    audio_file = st.session_state.get("sim_audio_file")
    if audio_file is not None:
      audio_bytes = audio_file["data"]
      st.caption(f"{audio_file['name']} · {len(audio_bytes) / 1024 / 1024:.2f} MB · 上限 50 MB")
      st.audio(audio_bytes, format=audio_file["type"] or "audio/wav")
      st.button(
        "转写音频（先预览）",
        width="stretch",
        key="sim_transcribe_btn",
        on_click=_transcribe_sim_audio,
        disabled=len(audio_bytes) > 50 * 1024 * 1024,
      )
    if st.session_state.get("sim_transcribe_notice"):
      st.caption(st.session_state["sim_transcribe_notice"])
    if st.session_state.get("sim_transcript"):
      transcript = comp.draft_widget("text_area", "检查并编辑转写结果", key="sim_transcript", height=150)
      st.download_button("下载完整转写文本", transcript, file_name="transcript.txt", mime="text/plain")
      previous = st.session_state.get("sim_teacher_input", "").strip()
      combined = len(previous) + len(transcript) + (2 if previous else 0)
      truncate = False
      if max(combined, len(transcript)) > 5000:
        st.warning("回填授课文本最多 5,000 字。请编辑缩短，或确认截取；完整转写仍可下载。")
        truncate = comp.draft_widget("checkbox", "允许只回填前 5,000 字", key="sim_transcribe_truncate")
      replace_col, append_col = st.columns(2)
      with replace_col:
        st.button("替换授课文本", on_click=_apply_transcript, disabled=not transcript.strip() or (len(transcript) > 5000 and not truncate), key="sim_transcript_replace", width="stretch")
      with append_col:
        st.button("追加到末尾", on_click=_apply_transcript, args=(True,), disabled=not transcript.strip() or (combined > 5000 and not truncate), key="sim_transcript_append", width="stretch")
    st.button(
      "开始模拟授课",
      type="primary", width="stretch",
      on_click=_start_simulation,
      key="sim_start_btn",
      disabled=not teacher_input.strip(),
    )
    if st.session_state["sim_started"]:
      round_text = (
        "等待第 1 轮学生互动"
        if st.session_state["sim_round"] == 0
        else f'已完成第 {st.session_state["sim_round"]} 轮学生互动'
      )
      st.markdown(
        f'<div class="dsh-flow-status" style="background:rgba(47,143,78,.16); color:#9ED9AC; border:1px solid rgba(47,143,78,.35);">'
        f'{comp.icon("activity", 14, "#9ED9AC")} 模拟授课进行中 · {round_text}</div>',
        unsafe_allow_html=True,
      )
    st.caption("点击“开始模拟授课”只初始化课堂；点击互动按钮后才会请求统一智能体接口。")
  elif not st.session_state["sim_started"]:
    comp.empty_view("02", "请先准备授课内容并开始模拟。")
  elif view == "interaction":
    st.caption("心流指标与虚拟学生画像为本地 Mock 示例；真实接口仅提供课堂建议。")
    left, right = st.columns([1.3, 1])
    with left:
      comp.section_title("虚拟学生反馈面板", "5 名性格化虚拟学生 · 认知仿真画像")
      if not st.session_state["sim_started"]:
        comp.info_card(
          "等待授课",
          ["开始模拟授课后，5 名虚拟学生将基于“跨学科概念与能力映射子图”生成差异化画像，",
           "实时反馈概念跃迁困惑、跨学科知识迁移障碍等认知状态。"],
          icon_name="timer", tone=config.COLORS["text_3"],
        )
      else:
        r = st.session_state["sim_round"]
        fb = st.session_state.get("sim_feedback")
        if fb:
          # 真实模式下展示 /api/agent-chat 的 answer；Mock 模式展示本地虚拟学生话术。
          palette = ["#8C6E4A", "#A67C52", "#4F7A5E", "#968D7B", "#5C6B7A"]
          for i, item in enumerate(x for x in fb if isinstance(x, dict)):
            name = comp.safe_text(item.get("name", "虚拟学生"))
            role = comp.safe_text(item.get("role", "课堂反馈"))
            text = comp.safe_text(item.get("text", ""))
            color = palette[i % len(palette)]
            st.markdown(
              f"""<div class="dsh-bubble" style="border-left-color:{color};">
              <div class="dsh-bubble-head">
              <b>{name}</b>
              <span class="dsh-bubble-role">{role}</span></div>
              <div class="dsh-bubble-body">“{text}”</div></div>""",
              unsafe_allow_html=True,
            )
        else:
          for s in VIRTUAL_STUDENTS:
            idx = min(r, len(s["msgs"]) - 1)
            student_name = comp.safe_text(s["name"])
            student_role = comp.safe_text(s["role"])
            student_msg = comp.safe_text(s["msgs"][idx])
            st.markdown(
              f"""<div class="dsh-bubble" style="border-left-color:{s['color']};">
              <div class="dsh-bubble-head"><span style="display:inline-flex;align-items:center;">{comp.icon(s["emoji"], 18, s["color"])}</span>
              <b>{student_name}</b>
              <span class="dsh-bubble-role" style="background:{s['color']};">{student_role}</span></div>
              <div class="dsh-bubble-body">“{student_msg}”</div></div>""",
              unsafe_allow_html=True,
            )
        _render_agent_sources(st.session_state.get("sim_agent_result"))
    with right:
      comp.section_title("心流自适应仪表盘", "认知负荷 / 参与度 / 困惑度 / 心流指数")
      comp.flow_dashboard(st.session_state["flow"], st.session_state.get("flow_status") or None)
      st.button(
        "触发一轮学生互动",
        type="secondary", width="stretch",
        disabled=not st.session_state["sim_started"],
        on_click=_advance_flow, args=(theme, teacher_input),
        key="sim_interact_btn",
      )
      st.caption("每次点击请求一轮课堂建议；失败保留本轮状态，可主动查看只读示例。")
  elif view == "data":
    st.caption("Mock 示例 · 以下多模态信号为本地演示数据，非音频或摄像头实测。")
    comp.section_title("多模态感知数据栏", "语音 + 视觉 + 交互 · 三模态时序特征提取")
    if not st.session_state["sim_started"]:
      st.caption("开始模拟授课后，展示 5 路多模态信号实时数值。")
    else:
      sigs = st.session_state.get("sim_signals")
      cols = st.columns(5)
      if sigs:
        palette = ["#8C6E4A", "#A67C52", "#6B6252", "#7A8B6F", "#4F5D4A"]
        icons = ["mic", "smile", "eye", "heart-pulse", "hand"]
        valid_signals = [s for s in sigs if isinstance(s, dict)][:5]
        for i, s in enumerate(valid_signals):
          with cols[i]:
            comp.signal_bar(
              comp.safe_text(s.get("name", "信号")),
              _bounded_percentage(s.get("value"), 0),
              note=comp.safe_text(s.get("note", "")),
              color=palette[i % 5], icon=icons[i % 5],
            )
      else:
        for i, (name, note, val, icon, color) in enumerate(_sim_signals()):
          with cols[i]:
            comp.signal_bar(name, val, note=note, color=color, icon=icon)


def _diagnosis_sample_text():
  """返回可直接编辑的内置文本课例。"""
  return LESSON_TEMPLATE.format(
    grade="初中",
    topic="碳中和·跨学科项目式学习",
    hours=4,
  )


def _decode_txt(raw):
  """按约定尝试 UTF-8-SIG 与 GB18030，返回（文本, 编码）或（None, None）。"""
  for encoding in ("utf-8-sig", "gb18030"):
    try:
      return raw.decode(encoding), encoding.upper()
    except UnicodeDecodeError:
      continue
  return None, None


def _extract_docx_text(raw):
  """仅用标准库提取 DOCX 正文与表格文字，不新增第三方依赖。"""
  try:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
      entry = archive.getinfo("word/document.xml")
      if entry.file_size > 20 * 1024 * 1024:
        raise ValueError("DOCX 正文解压后超过 20 MB，请拆分文档。")
      if entry.flag_bits & 1:
        raise ValueError("不支持加密 DOCX，请另存为未加密文件。")
      xml_bytes = archive.read("word/document.xml")
    if b"<!DOCTYPE" in xml_bytes or b"<!ENTITY" in xml_bytes:
      raise ValueError("DOCX 含不支持的 XML 声明。")
    root = ET.fromstring(xml_bytes)
  except (KeyError, OSError, ET.ParseError, zipfile.BadZipFile):
    raise ValueError("DOCX 已损坏或不是有效的 Word 文档。")
  ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
  lines = []
  def paragraph_text(paragraph):
    return "".join(node.text or "" if node.tag == f"{ns}t" else "\t" if node.tag == f"{ns}tab" else "\n" if node.tag in (f"{ns}br", f"{ns}cr") else "" for node in paragraph.iter()).strip()

  def blocks(parent):
    for child in parent:
      if child.tag == f"{ns}p":
        text = paragraph_text(child)
        if text:
          lines.append(text)
      elif child.tag == f"{ns}tbl":
        for row in child.findall(f"{ns}tr"):
          cells = [" / ".join(paragraph_text(p) for p in cell.iter(f"{ns}p")) for cell in row.findall(f"{ns}tc")]
          if any(cells):
            lines.append(" | ".join(cells))
      else:
        blocks(child)
  body = root.find(f"{ns}body")
  if body is not None:
    blocks(body)
  result = "\n".join(lines).strip()
  if not result:
    raise ValueError("文档没有可提取文字，可能为空或仅含图片；暂不支持 OCR。")
  return result


def _read_lesson_upload(uploaded):
  """按扩展名读取诊断页上传文件，统一返回（纯文本, 读取方式）。"""
  raw = uploaded.getvalue()
  if len(raw) > 10 * 1024 * 1024:
    raise ValueError("教学文件超过 10 MB，请拆分后上传。")
  if not raw:
    raise ValueError("文件为空，请重新选择。")
  if uploaded.name.lower().endswith(".docx"):
    return _extract_docx_text(raw), "DOCX"
  text, encoding = _decode_txt(raw)
  if text is None:
    raise ValueError("TXT 无法解码，请另存为 UTF-8 或 GB18030。")
  if not text.strip():
    raise ValueError("TXT 没有可提取文字。")
  return text, encoding


def _apply_lesson_upload():
  pending = st.session_state.get("diag_upload_pending")
  if pending:
    st.session_state["diag_lesson_text"] = pending["text"][:20000]
    st.session_state["diag_input_source"] = pending["source"]
    st.session_state["diag_upload_notice"] = f"已填入 {min(len(pending['text']), 20000):,} 字。"
    st.session_state.pop("diag_upload_pending", None)


def _discard_lesson_upload():
  st.session_state.pop("diag_upload_pending", None)
  st.session_state["diag_upload_notice"] = "已保留原课例文字，未替换。"


def _use_diagnosis_sample():
  st.session_state["diag_lesson_text"] = _diagnosis_sample_text()
  st.session_state["diag_input_source"] = "内置碳中和样例"


def _normalise_diagnosis_result(result):
  """为页面缓存补齐诊断报告必需字段，保留可用的真实后端内容。"""
  if not isinstance(result, dict):
    result = {}
  if comp.is_agent_response(result):
    return {
      "meta": "真实后端 · STEM 课堂诊断智能体",
      "problems": [],
      "conclusion": result["answer"],
      "suggests": [],
      "trace": None,
      "agent_type": result["agent_type"],
      "sources": result.get("sources", []),
      "graph_sources": result.get("graph_sources", []),
      "_real_response": True,
    }
  problems = result.get("problems")
  problems = [p for p in problems if isinstance(p, dict)] if isinstance(problems, list) else []
  suggests = result.get("suggests")
  suggests = suggests if isinstance(suggests, list) else DIAG_REPORT["suggests"]
  trace = result.get("trace")
  if not (
    isinstance(trace, dict)
    and isinstance(trace.get("nodes"), list)
    and isinstance(trace.get("edges"), list)
  ):
    trace = TRACE_GRAPH
  return {
    "meta": result.get("meta") or DIAG_REPORT["meta"],
    "problems": problems or DIAG_REPORT["problems"],
    "conclusion": result.get("conclusion") or DIAG_REPORT["conclusion"],
    "suggests": suggests,
    "trace": trace,
  }


def _clear_diagnosis_chat():
  """只清空教师对话，不影响课例和已生成的诊断报告。"""
  st.session_state["diag_chat_history"] = []
  st.session_state["diag_chat_confirm"] = False
  st.session_state["diag_chat_error"] = ""
  st.session_state["diag_chat_preview"] = ""


def _set_chat_example(text):
  st.session_state["diag_chat_question"] = text


def _send_diagnosis_chat():
  question = st.session_state.get("diag_chat_question", "").strip()
  if not question:
    return
  history = st.session_state.setdefault("diag_chat_history", [])
  lesson = st.session_state.get("diag_lesson_text", "")
  current_report = st.session_state.get("diag_result") if lesson == st.session_state.get("diag_input_snapshot") else None
  prompt = _diagnosis_chat_prompt(question, history, lesson, current_report)
  response = comp.api_gate(
    endpoint=config.API_ENDPOINTS["diag_report"],
    payload=_agent_payload("diag_report", prompt),
    mock_result={"answer": _diagnosis_chat_mock(question), "agent_type": config.AGENT_TYPES["diag_report"]},
  )
  status, detail = st.session_state.get("backend_status") or ("down", "未知错误")
  if status not in {"ok", "mock"}:
    st.session_state["diag_chat_error"] = f"发送失败：{detail}。问题已保留，可以重试；未添加重复消息。"
    st.session_state["diag_chat_preview"] = _diagnosis_chat_mock(question)
    return
  answer = response.get("answer", "")
  if not isinstance(answer, str) or not answer.strip():
    st.session_state["diag_chat_error"] = "发送失败：回答为空，问题已保留。"
    return
  history.extend([{"role": "teacher", "content": question},
                  {"role": "assistant", "content": answer.strip(), "source": "mock" if status == "mock" else "real"}])
  st.session_state["diag_chat_question"] = ""
  st.session_state["diag_chat_error"] = ""
  st.session_state["diag_chat_preview"] = ""


def _diagnosis_chat_prompt(question, history, lesson_text, diagnosis_result):
  """把有限的页面上下文压缩进单轮请求，支持无状态后端连续对话。"""
  context = []
  if lesson_text.strip():
    context.append(f"当前课例摘录：\n{lesson_text.strip()[:2400]}")
  if isinstance(diagnosis_result, dict) and diagnosis_result.get("conclusion"):
    context.append(f"最近诊断结论：\n{str(diagnosis_result['conclusion']).strip()[:1600]}")
  recent = history[-6:] if isinstance(history, list) else []
  if recent:
    dialogue = []
    for item in recent:
      if not isinstance(item, dict):
        continue
      role = "教师" if item.get("role") == "teacher" else "智能体"
      content = str(item.get("content", "")).strip()[:900]
      if content:
        dialogue.append(f"{role}：{content}")
    if dialogue:
      context.append("最近对话：\n" + "\n".join(dialogue))
  background = "\n\n".join(context) or "暂无课例或诊断报告，请直接根据教师描述提供建议。"
  return (
    "请作为 STEM 课堂诊断与教师反思智能体，与教师进行连续对话。"
    "回答应通俗、具体、可执行；先判断问题，再给课堂观察要点和下一步建议。"
    "若证据不足，请明确提出一到两个需要教师补充的信息。\n\n"
    f"{background}\n\n教师本轮问题：\n{question.strip()}"
  )


def _diagnosis_chat_mock(question):
  return (
    f"我理解你当前关注的是“{question.strip()[:80]}”。建议先记录一项可观察证据，"
    "例如学生回答、任务完成时间或典型错误；随后只调整一个教学变量，"
    "如提问层级、示例跨度或小组支架，并在下一轮课堂中对照观察。"
    "如果你能补充具体学段和课堂现象，我可以继续把建议细化成可直接执行的步骤。"
  )


def _diagnosis_chat_html(value):
  """安全呈现后端常见 Markdown 结构，不直接执行后端返回的 HTML。"""
  rendered = []
  for raw_line in str(value or "").splitlines():
    line = comp.safe_text(raw_line.strip())
    line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
    if not line:
      rendered.append('<div class="dsh-chat-space"></div>')
    elif line in ("---", "———"):
      rendered.append('<hr class="dsh-chat-rule">')
    elif re.match(r"^#{1,4}\s+", line):
      title = re.sub(r"^#{1,4}\s+", "", line)
      rendered.append(f'<div class="dsh-chat-heading">{title}</div>')
    elif re.match(r"^-\s+", line):
      item = re.sub(r"^-\s+", "", line)
      rendered.append(f'<div class="dsh-chat-point"><span>•</span><div>{item}</div></div>')
    elif re.match(r"^\d+[\.、]\s*", line):
      match = re.match(r"^(\d+[\.、])\s*(.*)", line)
      rendered.append(
        f'<div class="dsh-chat-point"><span>{match.group(1)}</span><div>{match.group(2)}</div></div>'
      )
    else:
      rendered.append(f'<div class="dsh-chat-paragraph">{line}</div>')
  return "".join(rendered)


def _render_diagnosis_chat():
  """教师就课堂问题与 classroom_diagnosis 智能体连续对话。"""
  history = st.session_state.setdefault("diag_chat_history", [])
  st.markdown('<div id="teacher-dialogue"></div>', unsafe_allow_html=True)
  with st.container(border=True, key="diag_chat_panel"):
    title_col, clear_col = st.columns([5, 1])
    with title_col:
      comp.section_title("教师—智能体对话", "围绕课堂问题连续追问，自动关联当前课例与诊断结论")
    with clear_col:
      clear_confirmed = comp.draft_widget("checkbox", "确认清空", key="diag_chat_confirm")
      st.button(
        "清空对话", type="secondary", width="stretch",
        disabled=not bool(history) or not clear_confirmed, on_click=_clear_diagnosis_chat,
        key="diag_chat_clear",
      )

    lesson = st.session_state.get("diag_lesson_text", "")
    current_report = bool(st.session_state.get("diag_result")) and lesson == st.session_state.get("diag_input_snapshot")
    st.caption(f"本轮上下文：{'当前课例' if lesson.strip() else '无课例'} · {'匹配的诊断报告' if current_report else '不使用旧报告'} · 最近 {min(len(history), 6)} 条对话。完整记录保留，可下载备份。")
    if history:
      visible = st.session_state.get("diag_chat_visible", 12)
      if len(history) > visible and st.button("加载更早记录", key="diag_chat_more"):
        visible += 12
        st.session_state["diag_chat_visible"] = visible
      st.caption(f"当前显示最近 {min(visible, len(history))} / {len(history)} 条消息")
      bubbles = []
      for item in history[-visible:]:
        if not isinstance(item, dict):
          continue
        is_teacher = item.get("role") == "teacher"
        row_class = "is-teacher" if is_teacher else "is-agent"
        role_label = "教师" if is_teacher else "诊断智能体 · Mock 示例" if item.get("source") == "mock" else "诊断智能体" if item.get("source") == "real" else "诊断智能体 · 历史记录（来源未标注）"
        icon_name = "users" if is_teacher else "brain"
        content = _diagnosis_chat_html(item.get("content", ""))
        bubbles.append(
          f'<div class="dsh-chat-row {row_class}">'
          f'<div class="dsh-chat-avatar">{comp.icon(icon_name, 16)}</div>'
          f'<div class="dsh-chat-bubble"><span class="dsh-chat-role">{role_label}</span>{content}</div>'
          f'</div>'
        )
      st.markdown(f'<div class="dsh-chat-list">{"".join(bubbles)}</div>', unsafe_allow_html=True)
    else:
      comp.info_card(
        "可以从一个具体课堂困惑开始",
        ["例如：学生在小组探究时只抄答案，我应该怎样调整任务和提问？"],
        icon_name="brain", tone=config.COLORS["accent"], light=True,
      )

    for i, example in enumerate(["学生小组探究时只抄答案，如何调整任务？", "怎样判断学生真的理解了跨学科概念？"]):
      st.button(example, key=f"diag_chat_example_{i}", on_click=_set_chat_example, args=(example,))
    if st.session_state.get("diag_chat_error"):
      st.error(st.session_state["diag_chat_error"])
      if st.session_state.get("diag_chat_preview"):
        with st.expander("参考示例（Mock，非真实回答，未计入对话）"):
          st.write(st.session_state["diag_chat_preview"])
    question = comp.draft_widget("text_area",
        "描述你在课堂中遇到的问题",
        placeholder="请尽量说明学段、教学内容和学生的具体表现……",
        height=100, max_chars=2000, key="diag_chat_question",
      )
    st.button("发送给诊断智能体" if not st.session_state.get("diag_chat_error") else "重试发送", type="primary", width="stretch", key="diag_chat_send", on_click=_send_diagnosis_chat, disabled=not question.strip())


def _generate_diagnosis():
  lesson_text = st.session_state.get("diag_lesson_text", "")
  if not lesson_text.strip():
    return
  question = (
    "请作为 STEM 课堂诊断智能体，对下面的课例或课堂实录进行诊断。"
    "请分析主要教学问题、课堂证据、可能原因和可执行的改进策略，并给出总结。\n\n"
    f"课例正文：\n{lesson_text[:20000]}"
  )
  rep = comp.api_gate(
    endpoint=config.API_ENDPOINTS["diag_report"],
    payload=_agent_payload("diag_report", question),
    mock_result={**DIAG_REPORT, "trace": TRACE_GRAPH},
  )
  if not comp.accept_result("03", rep, "input", "report"):
    return
  rep = _normalise_diagnosis_result(rep)
  st.session_state["diag_result"] = rep
  st.session_state["diag_trace"] = rep["trace"]
  st.session_state["diag_input_snapshot"] = lesson_text
  st.session_state["diag_generated_source"] = st.session_state["diag_input_source"]
  st.session_state["diag_ready"] = True
  comp.set_view("03", "report")


def page_diagnosis(view):
  st.session_state.setdefault("diag_lesson_text", "")
  st.session_state.setdefault("diag_result", None)
  st.session_state.setdefault("diag_trace", None)
  st.session_state.setdefault("diag_input_snapshot", None)
  st.session_state.setdefault("diag_input_source", "手动输入")
  st.session_state.setdefault("diag_generated_source", "")
  st.session_state.setdefault("diag_upload_signature", None)
  st.session_state.setdefault("diag_upload_notice", "")
  st.session_state.setdefault("diag_chat_history", [])

  lesson_text = st.session_state["diag_lesson_text"]
  if view == "input":
    comp.section_title("课例文本输入", "粘贴文本、上传 TXT / DOCX 或使用内置样例")
    uploaded = st.file_uploader(
      "上传教学设计或课堂对话文本",
      type=["txt", "docx"],
      max_upload_size=10,
      help="TXT 支持 UTF-8、UTF-8 BOM、GB18030；DOCX 由前端提取正文和表格文字，随后仅发送纯文本。",
      key="diag_upload",
    )
    if uploaded is not None:
      raw = uploaded.getvalue()
      signature = (uploaded.name, len(raw), hash(raw))
      if signature != st.session_state["diag_upload_signature"]:
        st.session_state.pop("diag_upload_pending", None)
        try:
          decoded, encoding = _read_lesson_upload(uploaded)
          truncated = len(decoded) > 20000
          file_kind = "DOCX" if uploaded.name.lower().endswith(".docx") else "TXT"
          st.session_state["diag_upload_pending"] = {"text": decoded, "source": f"{file_kind} 上传：{uploaded.name}"}
          suffix = "；填入时保留前 20,000 字" if truncated else ""
          notice = f"已按 {encoding} 提取 {len(decoded):,} 字{suffix}。"
          if not st.session_state.get("diag_lesson_text", "").strip():
            _apply_lesson_upload()
          st.session_state["diag_upload_notice"] = notice
        except ValueError as exc:
          st.session_state["diag_upload_notice"] = f"读取失败：{exc} 原课例未改变。"
        st.session_state["diag_upload_signature"] = signature

    if st.session_state["diag_upload_notice"]:
      if not st.session_state["diag_upload_notice"].startswith("读取失败"):
        st.caption(st.session_state["diag_upload_notice"])
      else:
        st.error(st.session_state["diag_upload_notice"])
    if st.session_state.get("diag_upload_pending"):
      st.warning("已有课例文字。是否用新文件内容替换？")
      st.button("确认替换课例", on_click=_apply_lesson_upload, key="diag_upload_apply", width="stretch")
      st.button("保留原课例", on_click=_discard_lesson_upload, key="diag_upload_cancel", width="stretch")

    lesson_text = comp.draft_widget("text_area",
      "粘贴或编辑课例文本",
      height=230,
      max_chars=20000,
      placeholder="请粘贴课堂实录或教案正文，最多 20,000 字。",
      key="diag_lesson_text",
    )
    st.button(
      "载入内置样例课例",
      type="secondary", width="stretch",
      on_click=_use_diagnosis_sample,
      key="diag_sample_btn",
    )
    st.button("生成诊断报告", type="primary", width="stretch", key="diag_gen_btn",
              disabled=not lesson_text.strip(), on_click=_generate_diagnosis)
  elif view == "chat":
    _render_diagnosis_chat()
  elif view == "report":
    rep = st.session_state["diag_result"]
    if not rep:
      comp.empty_view("03", "诊断报告尚未生成。")
      return
    if lesson_text != st.session_state["diag_input_snapshot"]:
      st.warning("课例内容已变化，当前为上一次报告；请返回课例输入重新生成。")
    with st.container(key="reading_diagnosis"):
      source = st.session_state["diag_generated_source"] or "课例文本"
      st.caption(f"报告来源：{source} · 已缓存，页面切换不会重复请求")
      st.caption(rep.get("meta", ""))
      evidence_column, insight_column = st.columns([1.7, .8], gap="large")
      with evidence_column:
        comp.section_title("问题与课堂证据")
        for p in rep["problems"]:
          comp.info_card(
            f'{comp.safe_text(p.get("id", "?"))} {comp.safe_text(p.get("title", ""))}',
            [f'<b>证据</b>：{comp.safe_text(p.get("evidence", ""))}',
             f'<b>反向归因</b>：{comp.safe_text(p.get("cause", ""))}',
             f'<b>改进建议</b>：{comp.safe_text(p.get("suggest", ""))}'],
            icon_name="triangle-alert", tone=config.COLORS["danger"],
          )
          comp.tag(
            f'理论锚点：{comp.safe_text(p.get("anchor", ""))}',
            color=config.NODE_TYPES["理论"],
          )
        if rep.get("suggests"):
          comp.section_title("改进建议清单")
          for i, suggestion in enumerate(rep.get("suggests", []), start=1):
            st.write(f"{i}. {suggestion}")
      with insight_column:
        comp.section_title("归因与溯源")
        comp.info_card(
          "反向归因结论",
          [comp.safe_text(rep.get("conclusion", ""))],
          icon_name="route", tone=config.COLORS["primary"],
        )
        _render_agent_sources(rep)
        if st.session_state.get("diag_trace"):
          if st.button("查看问题、理论与案例溯源", key="diag_trace_btn", width="stretch"):
            _trace_dialog()


@st.dialog("图谱溯源 · 问题、理论与案例", width="large")
def _trace_dialog():
  """诊断报告关联的局部子图谱弹窗（原“图谱溯源弹窗”）。

  当前统一接口仅在返回可适配的图谱来源时展示真实依据；Mock 模式使用 TRACE_GRAPH。
  """
  comp.section_title("局部溯源子图谱", "诊断问题锚点、教育理论与支撑案例（可选择节点查看详情）")
  data = st.session_state.get("diag_trace") or TRACE_GRAPH
  nodes = [dict(n) for n in data.get("nodes", [])]
  for n in nodes:
    n.setdefault("domain", "后端溯源子图")
    n.setdefault("desc", "")
    n.setdefault("size", 24)
  edges = [tuple(e) for e in data.get("edges", [])]
  with st.container(border=True):
    comp.render_kg(
      nodes, edges,
      height=430, key="trace_kg", hierarchical=True, direction="LR",
    )
  st.markdown(
    f'<div style="margin-top:.3rem;">'
    f'<span class="dsh-tag" style="background:#FDFBF6; color:#3A3129; border:1px solid rgba(0,0,0,0.10);"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{config.NODE_TYPES["问题"]};margin-right:.3rem;"></span>诊断问题</span>'
    f'<span class="dsh-tag" style="background:#FDFBF6; color:#3A3129; border:1px solid rgba(0,0,0,0.10);"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{config.NODE_TYPES["理论"]};margin-right:.3rem;"></span>教育理论锚点</span>'
    f'<span class="dsh-tag" style="background:#FDFBF6; color:#3A3129; border:1px solid rgba(0,0,0,0.10);"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{config.NODE_TYPES["案例"]};margin-right:.3rem;"></span>支撑案例</span>'
    f'<span class="dsh-tag" style="background:#FDFBF6; color:#3A3129; border:1px solid rgba(0,0,0,0.10);"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{config.NODE_TYPES["行为"]};margin-right:.3rem;"></span>行为归因</span>'
    f'</div>',
    unsafe_allow_html=True,
  )


# =====================================================================
# 页面 04 · 跨学科课程设计工作台【演示主线】
# =====================================================================
def _ws_steps_html():
  """三步操作按钮的状态指示（完成 / 当前发光 / 未解锁置灰）。"""
  stage = st.session_state["ws_stage"]
  steps = [
    ("1", "AI 初生成教案", "启发式初生成：基于 ITRS 能力分层推送适配支架"),
    ("2", "人工迭代修正", "人主导迭代：Human-in-the-Loop 实时校验融合漏洞"),
    ("3", "素养对齐校验", "素养对齐智能诊断：内嵌 STEM 素养评估图谱"),
  ]
  parts = []
  for i, (num, name, note) in enumerate(steps):
    if i < stage:
      cls, mark = "dsh-step dsh-step-done", comp.icon("check", 12, "#fff")
    elif i == stage:
      cls, mark = "dsh-step dsh-step-current", comp.icon("play", 12, "#fff")
    else:
      cls, mark = "dsh-step dsh-step-locked", comp.icon("lock", 12, "#98A2B3")
    parts.append(
      f'<div class="{cls}"><span class="dsh-step-num">{mark}</span>'
      f'<div><div style="font-weight:700;">{num} · {name}</div>'
      f'<div style="font-size:.72rem; color:inherit; opacity:.85;">{note}</div></div></div>'
    )
  st.markdown("".join(parts), unsafe_allow_html=True)


def _append_mark_once(text, marker, block):
  """仅在 Mock 教案中追加一次阶段记录。"""
  base = text or ""
  if marker in base:
    return base
  return f"{base.rstrip()}\n\n{block.lstrip()}"


def _current_ws_lesson():
  editor = st.session_state.get("ws_lesson_editor")
  if isinstance(editor, str):
    return editor
  return st.session_state.get("ws_lesson") or ""


def _set_ws_lesson(text):
  lesson = str(text or "")
  st.session_state["ws_lesson"] = lesson
  st.session_state["ws_lesson_editor"] = lesson


def _ws_context(grade, topic, hours):
  return {"grade": grade, "topic": topic.strip(), "hours": int(hours)}


def _send_lesson_to_simulation():
  lesson = _current_ws_lesson().strip()
  if not lesson:
    return
  st.session_state["sim_teacher_input"] = lesson[:300]
  _reset_flow()
  st.session_state["sim_started"] = False
  comp.set_view("02", "prepare")
  st.session_state["nav_radio"] = "02"


def _send_lesson_to_diagnosis():
  lesson = _current_ws_lesson().strip()
  if not lesson:
    return
  st.session_state["diag_lesson_text"] = lesson[:20000]
  st.session_state["diag_input_source"] = "课程设计工作台"
  st.session_state["diag_upload_notice"] = ""
  comp.set_view("03", "input")
  st.session_state["nav_radio"] = "03"


def _apply_itrs_stem(res, fallback_itrs, fallback_stem):
  """将接口返回的 ITRS/STEM 字典转换为达标面板数据（列表 + 配色轮换）。"""
  palette = ["#8C6E4A", "#A67C52", "#6B6252", "#7A8B6F", "#4F5D4A"]
  itrs = res.get("itrs")
  if isinstance(itrs, dict) and itrs:
    st.session_state["ws_itrs"] = [
      (str(k), _bounded_percentage(v, 0), palette[i % len(palette)])
      for i, (k, v) in enumerate(itrs.items())
    ]
  else:
    st.session_state["ws_itrs"] = fallback_itrs
  stem = res.get("stem")
  if isinstance(stem, dict) and stem:
    st.session_state["ws_stem"] = [
      (str(k), _bounded_percentage(v, 0), palette[i % len(palette)])
      for i, (k, v) in enumerate(stem.items())
    ]
  else:
    st.session_state["ws_stem"] = fallback_stem


def _workbench_action(action):
  grade, topic, hours = _workbench_context_values()
  current_context = _ws_context(grade, topic, hours)
  stage = st.session_state["ws_stage"]
  stale = stage > 0 and st.session_state.get("ws_design_context") != current_context
  if action != "generate" and (stale or not _current_ws_lesson().strip() or stage != (1 if action == "iterate" else 2)):
    return
  if action == "generate":
      mock_res = {
        "stage": 1,
        "lesson_md": LESSON_TEMPLATE.format(grade=grade, topic=topic, hours=hours),
        "itrs": {k: v for k, v, _ in ITRS_DIMS},
        "stem": {k: v for k, v, _ in STEM_DIMS},
        "conclusion": None,
      }
      question = (
        "请作为 STEM 教学设计智能体，生成一份可直接编辑的完整 Markdown 教案。"
        "教案应包含教学目标、跨学科概念、项目任务、课堂活动、支架和评价方案。\n"
        f"学段：{grade}\n主题：{topic}\n课时：{hours}"
      )
      res = comp.api_gate(
        config.API_ENDPOINTS["workbench_design"],
        _agent_payload("workbench_design", question),
        mock_result=mock_res,
      )
      if not comp.accept_result("04", res, "prepare" if action == "generate" else "editor", "assessment" if action == "check" else "editor"):
        return
      if not isinstance(res, dict):
        res = mock_res
      is_real = comp.is_agent_response(res)
      _set_ws_lesson(res.get("answer") if is_real else (res.get("lesson_md") or mock_res["lesson_md"]))
      st.session_state["ws_agent_result"] = res if is_real else None
      st.session_state["ws_stage"] = 1
      st.session_state["ws_design_context"] = current_context
      st.session_state["ws_check_conclusion"] = CHECK_CONCLUSION
      _apply_itrs_stem(res, ITRS_DIMS, STEM_DIMS)
      comp.set_view("04", "assessment" if action == "check" else "editor")
  if action == "iterate":
      cur = _current_ws_lesson()
      mock_res = {
        "stage": 2,
        "lesson_md": _append_mark_once(cur, "人工迭代修正记录", EDIT_MARK_MD),
        "itrs": None, "stem": None, "conclusion": None,
      }
      question = (
        "请作为 STEM 教学设计智能体，优化下面这份人工编辑后的教案。"
        "请保留合理内容，修复跨学科融合与活动衔接问题，并返回完整修订版 Markdown 教案。\n"
        f"学段：{grade}\n主题：{topic}\n课时：{hours}\n\n当前教案：\n{cur[:20000]}"
      )
      res = comp.api_gate(
        config.API_ENDPOINTS["workbench_design"],
        _agent_payload("workbench_design", question),
        mock_result=mock_res,
      )
      if not comp.accept_result("04", res, "prepare" if action == "generate" else "editor", "assessment" if action == "check" else "editor"):
        return
      if not isinstance(res, dict):
        res = mock_res
      is_real = comp.is_agent_response(res)
      _set_ws_lesson(res.get("answer") if is_real else (res.get("lesson_md") or mock_res["lesson_md"]))
      st.session_state["ws_agent_result"] = res if is_real else None
      st.session_state["ws_stage"] = 2
      comp.set_view("04", "assessment" if action == "check" else "editor")
  if action == "check":
      cur = _current_ws_lesson()
      mock_res = {
        "stage": 3,
        "lesson_md": _append_mark_once(cur, "素养对齐校验结果", CHECK_MARK_MD),
        "itrs": {k: v for k, v, _ in ITRS_DIMS},
        "stem": {k: v for k, v, _ in STEM_DIMS},
        "conclusion": CHECK_CONCLUSION,
      }
      question = (
        "请作为 STEM 教学设计智能体，对下面教案进行素养对齐校验。"
        "请从科学思维、数学建模、工程实践、技术应用、社会责任等方面给出证据、"
        "不足和改进建议，最后给出总体结论。\n"
        f"学段：{grade}\n主题：{topic}\n课时：{hours}\n\n当前教案：\n{cur[:20000]}"
      )
      res = comp.api_gate(
        config.API_ENDPOINTS["workbench_design"],
        _agent_payload("workbench_design", question),
        mock_result=mock_res,
      )
      if not comp.accept_result("04", res, "prepare" if action == "generate" else "editor", "assessment" if action == "check" else "editor"):
        return
      if not isinstance(res, dict):
        res = mock_res
      is_real = comp.is_agent_response(res)
      _set_ws_lesson(cur if is_real else (res.get("lesson_md") or mock_res["lesson_md"]))
      st.session_state["ws_stage"] = 3
      _apply_itrs_stem(res, ITRS_DIMS, STEM_DIMS)
      st.session_state["ws_check_conclusion"] = (
        res["answer"] if is_real else (res.get("conclusion") or CHECK_CONCLUSION)
      )
      st.session_state["ws_agent_result"] = res if is_real else None
      comp.set_view("04", "assessment" if action == "check" else "editor")


def _workbench_context_values():
  return (st.session_state.setdefault("ws_grade", "初中"),
          st.session_state.setdefault("ws_topic", "碳中和·跨学科项目式学习"),
          st.session_state.setdefault("ws_hours", 4))


def _reset_workbench():
  st.session_state["ws_stage"] = 0
  _set_ws_lesson("")
  st.session_state["ws_design_context"] = None
  st.session_state["ws_itrs"] = ITRS_DIMS
  st.session_state["ws_stem"] = STEM_DIMS
  st.session_state["ws_check_conclusion"] = CHECK_CONCLUSION
  st.session_state["ws_agent_result"] = None
  comp.set_view("04", "prepare")
  for prefix in ("request_error_", "fallback_", "preview_"):
    st.session_state.pop(prefix + "04", None)


def page_workbench(view):
  grade, topic, hours = _workbench_context_values()
  current_context = _ws_context(grade, topic, hours)
  stage = st.session_state["ws_stage"]
  stale = stage > 0 and st.session_state.get("ws_design_context") != current_context
  st.caption(" → ".join(f"{'✓ ' if stage >= i else ''}{name}" for i, name in enumerate(("AI 初生成", "人工迭代", "素养校验"), 1)))
  if stale:
    st.warning("设计参数已变化，旧教案已保留；请返回设计准备重新初生成。")
  if view == "prepare":
    parameter_column, guide_column = st.columns([1.5, .85], gap="large")
    with parameter_column:
      comp.section_title("设计准备")
      comp.draft_widget("selectbox", "学段", options=["小学", "初中", "高中"], key="ws_grade")
      comp.draft_widget("text_input", "主题", key="ws_topic")
      comp.draft_widget("slider", "课时", min_value=1, max_value=8, key="ws_hours")
      st.button("AI 初生成", key="ws_b1", type="primary", width="stretch", on_click=_workbench_action, args=("generate",))
      st.button("重置演示流程", key="ws_reset", width="stretch", disabled=stage == 0, on_click=_reset_workbench)
    with guide_column:
      comp.section_title("人机协同路径")
      comp.info_card(
        "三阶段设计约束",
        ["01 · AI 提供可编辑的教案起点", "02 · 师范生修订后再提交迭代", "03 · 完成 ITRS 与 STEM 素养校验"],
        icon_name="route", tone=config.COLORS["accent"],
      )
  elif view == "editor":
    if not _current_ws_lesson():
      comp.empty_view("04", "教案尚未生成。")
      return
    with st.container(key="reading_lesson"):
      mode = comp.draft_widget("radio", "教案显示", options=["编辑 Markdown", "预览教案"], horizontal=True, key="lesson_display")
      if mode == "编辑 Markdown":
        comp.draft_widget("text_area", "教案 Markdown（可直接编辑）", height=520, key="ws_lesson_editor")
      else:
        st.markdown(_current_ws_lesson())
      _render_agent_sources(st.session_state.get("ws_agent_result"))
      st.caption("三步按序解锁；当前编辑内容用于人工迭代、素养校验和跨页传递。")
      st.button("提交人工迭代", key="ws_b2", disabled=stage != 1 or stale or not _current_ws_lesson().strip(),
                on_click=_workbench_action, args=("iterate",))
      st.button("素养校验", key="ws_b3", disabled=stage != 2 or stale or not _current_ws_lesson().strip(),
                on_click=_workbench_action, args=("check",))
      st.button("送入教学模拟", key="ws_send_sim", disabled=stale, on_click=_send_lesson_to_simulation)
      st.button("送入智能诊断", key="ws_send_diag", disabled=stale, on_click=_send_lesson_to_diagnosis)
  elif view == "assessment":
    if stage == 0:
      comp.empty_view("04", "尚无素养评估结果。")
      return
    st.caption("ITRS 与 STEM 数值为内置 Mock 示例；真实接口的校验结论单独展示。")
    col1, col2 = st.columns(2)
    with col1:
      st.markdown('<div style="font-weight:700; color:#ffffff; margin-bottom:.3rem;">ITRS 师范生教学能力（四维）</div>', unsafe_allow_html=True)
      for name, val, color in st.session_state["ws_itrs"]:
        comp.signal_bar(comp.safe_text(name), val, note="达标率", color=color)
    with col2:
      st.markdown('<div style="font-weight:700; color:#ffffff; margin-bottom:.3rem;">STEM 核心素养（五维）</div>', unsafe_allow_html=True)
      for name, val, color in st.session_state["ws_stem"]:
        comp.signal_bar(comp.safe_text(name), val, note="达标率", color=color)

    if st.session_state["ws_stage"] < 3:
      comp.info_card(
        "待校验",
        ["当前为 AI 预估达标率。完成“素养校验”后，将输出结论与可溯源证据链。"],
        icon_name="timer", tone=config.COLORS["text_3"],
      )
    else:
      comp.info_card(
        "校验结论与证据链",
        [f"<b>{comp.safe_text(st.session_state['ws_check_conclusion'])}</b>"],
        icon_name="check", tone=config.COLORS["success"],
      )


def _diagnosis_to_research_pain():
  """把最近一次诊断缓存压缩为科研问题描述。"""
  report = st.session_state.get("diag_result")
  if not isinstance(report, dict):
    return ""
  lines = ["以下教学问题来自最近一次智能诊断："]
  problems = report.get("problems")
  if isinstance(problems, list):
    for problem in (p for p in problems if isinstance(p, dict)):
      title = str(problem.get("title", "")).strip()
      cause = str(problem.get("cause", "")).strip()
      suggest = str(problem.get("suggest", "")).strip()
      if title:
        lines.append(f"- 问题：{title}")
      if cause:
        lines.append(f"  归因：{cause}")
      if suggest:
        lines.append(f"  建议：{suggest}")
  conclusion = str(report.get("conclusion", "")).strip()
  if conclusion:
    lines.append(f"诊断结论：{conclusion}")
  return "\n".join(lines)[:2000]


def _import_diagnosis_to_research():
  comp.set_view("05", "input")
  pain = _diagnosis_to_research_pain()
  if not pain:
    return
  _queue_research_input(pain, "最近一次诊断结果")


def _queue_research_input(text, source):
  st.session_state["research_pending"] = {"text": text[:2000], "source": source}
  if not st.session_state.get("research_pain", "").strip():
    _apply_research_input()


def _apply_research_input():
  pending = st.session_state.pop("research_pending", None)
  if not pending:
    return
  pain = pending["text"]
  st.session_state["research_pain"] = pain
  st.session_state["research_imported_pain"] = pain
  st.session_state["research_input_source"] = pending["source"]


def _cancel_research_input():
  st.session_state.pop("research_pending", None)


def _normalise_research_result(result):
  mock = {
    "topic_md": RESEARCH_TOPIC_MD,
    "lit_md": LIT_OUTLINE_MD,
    "survey_md": SURVEY_DRAFT_MD,
    "exp_md": EXP_DRAFT_MD,
  }
  if not isinstance(result, dict):
    return mock
  if comp.is_agent_response(result):
    return {
      "answer": result["answer"],
      "agent_type": result["agent_type"],
      "sources": result.get("sources", []),
      "graph_sources": result.get("graph_sources", []),
      "_real_response": True,
    }
  normalised = {}
  for key, fallback in mock.items():
    value = result.get(key)
    normalised[key] = value if isinstance(value, str) and value.strip() else fallback
  return normalised


def _generate_research():
  pain = st.session_state.get("research_pain", "")
  if not pain.strip():
    return
  source = _research_source()
  mock_res = {
    "topic_md": RESEARCH_TOPIC_MD,
    "lit_md": LIT_OUTLINE_MD,
    "survey_md": SURVEY_DRAFT_MD,
    "exp_md": EXP_DRAFT_MD,
  }
  question = (
    "请作为 STEM 教育科研智能体，把下面教学实践中值得研究的现象或问题，"
    "转化为一份可执行的小型教育研究方案。"
    "请包含研究选题与依据、研究问题、文献综述提纲、研究方法、样本与过程、"
    "问卷或访谈工具初稿、数据分析思路和预期成果。\n\n"
    f"教学现象或研究问题：\n{pain[:2000]}"
  )
  result = comp.api_gate(
    endpoint=config.API_ENDPOINTS["research_plan"],
    payload=_agent_payload("research_plan", question),
    mock_result=mock_res,
  )
  if not comp.accept_result("05", result, "input", "result"):
    return
  st.session_state["research_result"] = _normalise_research_result(result)
  st.session_state["research_input_snapshot"] = pain
  st.session_state["research_generated_source"] = source
  st.session_state["research_ready"] = True
  comp.set_view("05", "result")


def _research_source():
  source = st.session_state.get("research_input_source", "独立输入")
  if source == "最近一次诊断结果" and st.session_state.get("research_pain") != st.session_state.get("research_imported_pain"):
    return "诊断结果带入后编辑"
  return source


def page_research(view):
  st.session_state.setdefault("research_result", None)
  st.session_state.setdefault("research_input_snapshot", None)
  st.session_state.setdefault("research_input_source", "独立输入")
  st.session_state.setdefault("research_generated_source", "")
  st.session_state.setdefault("research_imported_pain", "")

  if view == "input":
    comp.section_title("教育研究问题输入", "从教学现象出发 · 图谱关联科研方法子域")
    st.markdown('<div class="dsh-research-hints"><span>学段 · 在哪个年级？</span><span>课堂现象 · 发生了什么？</span><span>学生表现 · 有哪些证据？</span><span>教师观察 · 想弄清什么？</span></div>', unsafe_allow_html=True)
    st.button("载入研究问题示例", key="research_sample", on_click=_queue_research_input, args=(DEFAULT_RESEARCH_PAIN, "内置示例"))
    if st.session_state.get("research_pending"):
      st.warning("已有研究问题。确认替换后，旧方案仍会保留并标注输入已变化。")
      st.button("确认替换研究问题", key="research_apply", on_click=_apply_research_input)
      st.button("保留原研究问题", key="research_cancel", on_click=_cancel_research_input)
    pain = comp.draft_widget("text_area",
      "回想你的教学实践，有哪些现象或问题值得进一步研究？",
      height=150,
      max_chars=2000,
      placeholder=(
        "例如：初中科学课的小组探究中，部分学生只记录答案，很少解释推理过程。"
        "请尽量说明学段、课堂现象、学生表现和你的观察。"
      ),
      key="research_pain",
    )
    imported = st.session_state["research_imported_pain"]
    source = st.session_state["research_input_source"]
    if source == "最近一次诊断结果" and pain != imported:
      source = "诊断结果带入后编辑"
    st.caption(f"当前来源：{source} · 最多 2,000 字")
    if st.session_state.get("diag_result") and st.session_state.get("diag_lesson_text") != st.session_state.get("diag_input_snapshot"):
      st.caption("最近诊断基于旧课例，带入前请核对内容。")
    st.button("带入最近诊断结果", key="research_import_diag_btn", disabled=not isinstance(st.session_state.get("diag_result"), dict), on_click=_import_diagnosis_to_research)
    st.button("生成研究方案", key="research_btn", type="primary", disabled=not pain.strip(), on_click=_generate_research)
  elif view == "result":
    result = st.session_state["research_result"]
    if not result:
      comp.empty_view("05", "研究方案尚未生成。")
      return
    if st.session_state.get("research_pain") != st.session_state["research_input_snapshot"]:
      st.warning("研究问题已变化，当前为上一次方案；请返回研究问题重新生成。")
    st.caption("方案来源：" + (st.session_state["research_generated_source"] or "独立输入"))
    text = result["answer"] if comp.is_agent_response(result) else "\n\n".join(result[k] for k in ("topic_md", "lit_md", "survey_md", "exp_md"))
    st.download_button("下载研究方案", text, file_name="research-plan.md", mime="text/markdown", key="research_download")
    with st.container(key="reading_research"):
      if comp.is_agent_response(result):
        st.markdown(result["answer"])
        _render_agent_sources(result)
      else:
        st.caption("Mock 示例方案 · 非真实智能体回答")
        choices = {"研究选题": "topic_md", "文献综述提纲": "lit_md", "问卷与实验设计初稿": "survey_md"}
        section = comp.draft_widget("radio", "方案章节", options=list(choices), horizontal=True, key="research_section")
        st.markdown(result[choices[section]])
        if section == "问卷与实验设计初稿":
          st.markdown(result["exp_md"])


def _domain_label(dom_id):
  if dom_id == "all":
    return config.KG_ALL_NAME
  for d in config.KG_SUBDOMAINS:
    if d["id"] == dom_id:
      return d["name"]
  return dom_id


def page_kg(view):
  domain = comp.draft_widget("selectbox", "切换知识子域", options=["all"] + config.KG_SUBDOMAIN_IDS,
                             format_func=_domain_label, key="kg_domain")
  data = KG_OVERVIEW if domain == "all" else KG_DATA[domain]
  st.caption("内置示例知识图谱 · 当前子域在三个视图间保留")
  if view == "browse":
    graph_column, detail_column = st.columns([2.2, .8], gap="large")
    with graph_column:
      st.markdown(
        f'<div style="margin-bottom:.5rem;">'
        + "".join(
          f'<span class="dsh-tag" style="background:#FDFBF6; color:#3A3129; border:1px solid rgba(0,0,0,0.10);">'
          f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{c};margin-right:.3rem;"></span>'
          f'{comp.safe_text(t)}</span>'
          for t, c in config.NODE_TYPES.items()
        )
        + "</div>",
        unsafe_allow_html=True,
      )
      comp.render_kg(data["nodes"], data["edges"], height=560, key="kg_main")
    with detail_column:
      comp.section_title("节点快速查看")
      comp.node_detail_panel(data["nodes"], data["edges"], key=f"kg_browse_detail_{domain}")
  elif view == "detail":
    comp.node_detail_panel(data["nodes"], data["edges"], key=f"kg_node_detail_{domain}")
  elif view == "about":
    total_n = len(KG_OVERVIEW["nodes"])
    total_e = len(KG_OVERVIEW["edges"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
      comp.stat_card(f"{total_n}", "实体总数", "全局总览", icon_name="layers")
    with c2:
      comp.stat_card(f"{total_e}", "关系总数", "含 8 条跨域关联", icon_name="git-fork")
    with c3:
      comp.stat_card("6", "知识子域", "多源异构融合", "database")
    with c4:
      comp.stat_card("8", "覆盖学科", "理化生地数工+教育", icon_name="globe")
    if domain == "all":
      comp.info_card(
        "全局总览（合并视图）",
        ["6 大子域合并视图：虚线边表示跨子域关联（如 碳中和 → 碳中和跨学科教案 → 科学思维素养）。",
         "切换左侧选择器可查看各子域独立子图与核心内容说明。"],
        icon_name="layers", tone=config.COLORS["primary"], light=True,
      )
    else:
      d = next(x for x in config.KG_SUBDOMAINS if x["id"] == domain)
      data = KG_DATA[domain]
      comp.info_card(
        f'{comp.safe_text(d["name"])}（{len(data["nodes"])} 实体 / {len(data["edges"])} 关系）',
        [f'<b>核心内容</b>：{comp.safe_text(d["core"])}',
         f'<b>作用</b>：{comp.safe_text(d["func"])}',
         f'<b>关联</b>：{comp.safe_text(d["rel"])}'],
        icon_name="database", tone=config.COLORS["accent"], light=True,
      )


def page_value(view):
  if view in ("impact", "evaluation"):
    st.caption("Mock 示例数据 · 数量、前后测及成长案例仅用于演示，不代表真实实证结论。")
  if view == "features":
    comp.section_title("四大创新点", "源自四大智能体的新增硬核技术突破")
    cols = st.columns(2)
    for i, ag in enumerate(config.AGENTS):
      with cols[i % 2]:
        agent_name = comp.safe_text(ag["name"])
        lines = [comp.safe_text(b) for b in ag["breakthroughs"]]
        advantage = comp.safe_text(ag["advantage"])
        st.markdown(
          f"""<div class="dsh-info">
          <div class="dsh-info-title">{comp.icon(ag["icon"], 18, config.COLORS["primary"])}
          <span style="border-left:3px solid {config.COLORS['primary']}; padding-left:.5rem;">{agent_name}</span></div>
          {''.join(f'<div class="dsh-info-line" style="font-size:.82rem;">{l}</div>' for l in lines)}
          <div style="font-size:.8rem; color:#3A3129; background:#FDFBF6; border:1px solid rgba(0,0,0,.10); border-radius:8px; padding:.55rem .7rem; margin-top:.55rem; line-height:1.6;">
           <b>答辩差异点</b>：{advantage}</div></div>""",
          unsafe_allow_html=True,
        )
  elif view == "impact":
    comp.section_title("落地成效", "试点应用数据（Mock 示例，联调后接入实证台账）")
    comp.info_card(
      "Mock 示例数据",
      ["本页数量、前后测和成长案例均用于演示页面能力，不代表已完成的真实实证结论。"],
      icon_name="triangle-alert", tone=config.COLORS["warning"], light=True,
    )
    for indexes, widths in (((0, 1, 2), [1.25, 1, .9]), ((3, 4, 5), [.9, 1.2, 1])):
      row = st.columns(widths, gap="medium")
      for column, index in zip(row, indexes):
        value, label, delta, icon = LANDING_STATS[index]
        with column:
          comp.stat_card(value, label, delta, icon)
  elif view == "evaluation":
    comp.section_title("实证评估", "准实验前后测 · ITRS 量表量化对比")
    col_chart, col_case = st.columns([1.6, 1])
    with col_chart:
      with st.container(border=True):
        st.markdown('<div style="font-weight:700; color:#ffffff; margin-bottom:.2rem;">ITRS 前后测对比（Mock 四维均值）</div>', unsafe_allow_html=True)
        st.bar_chart(
          {"维度": ITRS_DIM_NAMES, "前测": ITRS_PRE, "后测": ITRS_POST},
          x="维度", y=["前测", "后测"],
          height=300,
        )
        st.caption("Mock 示例：四维均值由 61.5 提升至 77.5，提升 15.9 分；真实统计结论需在获得原始样本后计算。")
    with col_case:
      comp.info_card(
        "成长轨迹案例 · 师范生A（Mock）",
        ["ITRS 前测 60 分，后测 80 分（提升 20 分）",
         "教案迭代 3 版（人机协同）",
         "诊断报告识别“概念跃迁过大”，据此开展针对性改进",
         "跨学科概念掌握度提升后，推送案例难度自动升级"],
        icon_name="check", tone=config.COLORS["success"],
      )
      comp.info_card(
        "结语",
        ["“教-学-研”三位一体闭环：从教学模拟到诊断反思，从课程设计到科研孵化，",
         "全部数据沉淀于多源异构动态语义知识图谱，实现教师全周期培养。"],
        icon_name="database", tone=config.COLORS["accent"],
      )
