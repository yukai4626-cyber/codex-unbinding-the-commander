# -*- coding: utf-8 -*-
"""app.py — 统一启动入口

启动方式：
    streamlit run app.py
访问地址（默认）：
    http://localhost:8501

职责：
1. 首行 set_page_config（宽屏布局）；
2. 注入全局 CSS、初始化会话状态；
3. 渲染侧边栏：项目品牌区、导航单选菜单、Mock 模式徽章、3 分钟演示动线、页脚；
4. 按导航 id 字典分发调用 pages.py 中对应的页面渲染函数。

架构（4 文件模块化）：
    config.py      全局配置（导航 / Mock 开关 / 后端地址 / 色板 / 子域）
    components.py  公共组件（CSS / 仪表盘 / 图谱渲染 / API 网关）
    pages.py       7 个页面渲染函数 + 全量 Mock 数据
    app.py         本文件：启动入口与页面调度
"""

import streamlit as st

import config
import components as comp
import pages

# ---- 首行必须为 set_page_config（宽屏适配） ----
st.set_page_config(
    page_title=config.PROJECT_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

comp.inject_css()
comp.init_session_state()

# ========================= 侧边栏 =========================
with st.sidebar:
    # 顶部品牌区：柔和米白渐变衔接侧栏背景，文字自然换行，不使用功能图标。
    st.markdown(
        """<div class="dsh-brand">
        <div class="dsh-brand-eyebrow">STEM TEACHER EDUCATION</div>
        <div class="dsh-brand-title">STEM 教师教育</div>
        <div class="dsh-brand-rule"></div>
        <div class="dsh-brand-sub"><span>“教 · 学 · 研”</span><span>一体化智能体</span></div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.divider()

    # 导航单选菜单（key=nav_radio，页面内跳转按钮亦写入该状态实现联动）
    nav_ids = [item["id"] for item in config.NAV_ITEMS]
    name_map = {item["id"]: item for item in config.NAV_ITEMS}

    def _nav_label(pid):
        item = name_map[pid]
        # 纯文本导航名称：前置 emoji 图标已移除，仅保留导航文字
        # “★演示主线”标记由 inject_css 中的 CSS 伪元素统一渲染在条目右上角
        return item["name"]

    st.radio(
        "页面导航",
        nav_ids,
        format_func=_nav_label,
        key="nav_radio",
        label_visibility="collapsed",
    )

    st.divider()
    comp.mock_badge()
    comp.backend_badge()

    runtime_label = "Mock 演示版" if config.MOCK_MODE else "真实后端模式"
    st.markdown(
        f'<div class="dsh-foot">STEM教师教育一体化智能体<br>{config.VERSION} · {runtime_label}<br>'
        f'统一接口：{config.API_BASE}/api/agent-chat</div>',
        unsafe_allow_html=True,
    )

# ========================= 页面调度 =========================
PAGE_FUNCS = {
    "01": pages.page_overview,
    "02": pages.page_simulation,
    "03": pages.page_diagnosis,
    "04": pages.page_workbench,
    "05": pages.page_research,
    "06": pages.page_kg,
    "07": pages.page_value,
}

current = st.session_state.get("nav_radio", "01")
render = PAGE_FUNCS.get(current, pages.page_overview)
render()
