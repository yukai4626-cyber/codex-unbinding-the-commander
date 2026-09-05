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


def _select_module(pid):
    """切换主模块并退出全局内容管理。"""
    st.session_state["nav_radio"] = pid
    st.session_state["shell_mode"] = "workspace"


def _open_management():
    """保留当前主模块，在右侧工作区打开内容管理。"""
    st.session_state["shell_mode"] = "manage"


# ========================= 侧边栏 =========================
with st.sidebar:
    st.markdown(
        """<div class="dsh-brand">
        <div class="dsh-brand-eyebrow">STEM TEACHER EDUCATION</div>
        <div class="dsh-brand-title">STEM 教师教育</div>
        <div class="dsh-brand-rule"></div>
        <div class="dsh-brand-sub"><span>“教 · 学 · 研”</span><span>一体化智能体</span></div>
        </div>""",
        unsafe_allow_html=True,
    )
    current_nav = st.session_state.get("nav_radio", "01")
    shell_mode = st.session_state.get("shell_mode", "workspace")
    with st.container(key="module_navigation"):
        for item in config.NAV_ITEMS:
            active = shell_mode == "workspace" and current_nav == item["id"]
            st.button(
                item["name"],
                key=f"main_nav_{item['id']}",
                icon=item.get("material_icon", ":material/apps:"),
                type="primary" if active else "secondary",
                width="stretch",
                on_click=_select_module,
                args=(item["id"],),
            )

    with st.container(key="sidebar_footer"):
        st.button(
            "内容管理",
            key="open_management",
            icon=":material/folder_managed:",
            type="primary" if shell_mode == "manage" else "secondary",
            width="stretch",
            on_click=_open_management,
        )
        comp.mock_badge()
        comp.backend_badge()

        runtime_label = "Mock 演示版" if config.MOCK_MODE else "真实后端模式"
        st.markdown(
            f'<div class="dsh-foot">{config.VERSION} · {runtime_label}<br>'
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
with st.container(key="workspace"):
    if st.session_state.get("shell_mode") == "manage":
        content = comp.management_frame()
        with content:
            comp.persistence_controls()
            comp.save_status()
    else:
        view, content = comp.page_frame(current)
        with content:
            with st.container(key=f"view_body_{current}_{view}"):
                comp.request_notice(current)
                if not comp.render_mock_preview(current):
                    render(view)
            comp.save_status()
