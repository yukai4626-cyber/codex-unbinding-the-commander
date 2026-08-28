# -*- coding: utf-8 -*-
"""components.py — 公共可复用组件沉淀（浅米纸感 + 深炭内容体系）

职责（供 pages.py / app.py 复用，本模块不承载页面业务逻辑）：
1. inject_css()              全局内联样式：浅米纸感、暖色微光、深炭内容块、噪点肌理
2. icon()                    Iconify(lucide) 内联 SVG 渲染（禁 Emoji 功能图标）
3. init_session_state()      集中初始化全部会话状态，统一守卫
4. page_header / section_title / stat_card / info_card / tag / signal_bar  统一样式组件
5. flow_dashboard()          心流自适应仪表盘（渐变进度条 + conic-gradient 环形仪表 + 状态条）
6. render_kg()               streamlit-agraph 图谱渲染封装（按类型着色 + 兜底表格）
7. node_detail_panel()       下拉选择器等价实现“节点点击查看详情”
8. api_gate()                统一接口网关（真实请求 + 字段清洗 + Mock 回退）

设计规范：禁紫/靛蓝、禁纯平背景（噪点+径向微光）、侧边栏保持米色纸感，
禁 Emoji 功能图标、全站缓动统一 cubic-bezier(0.1,0.9,0.2,1)。
"""

import copy
import html
import math

import streamlit as st
import requests
import config
from streamlit_agraph import agraph, Node, Edge, Config as AgraphConfig

_ICONS = {
    'activity': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
    'arrow-right': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14m-7-7l7 7l-7 7"/>',
    'book-open': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v16m8.001-2A2 2 0 0 0 22 17V5a2 2 0 0 0-1.999-2L16 3.002A5 5 0 0 0 12 5a5 5 0 0 0-4-2H4a2 2 0 0 0-2 2v12a2 2 0 0 0 1.999 2H8a5 5 0 0 1 4 2a5 5 0 0 1 4-2z"/>',
    'bookmark': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 3a2 2 0 0 1 2 2v15a1 1 0 0 1-1.496.868l-4.512-2.578a2 2 0 0 0-1.984 0l-4.512 2.578A1 1 0 0 1 5 20V5a2 2 0 0 1 2-2z"/>',
    'brain': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M12 18V5m3 8a4.17 4.17 0 0 1-3-4a4.17 4.17 0 0 1-3 4m8.598-6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"/><path d="M17.997 5.125a4 4 0 0 1 2.526 5.77"/><path d="M18 18a4 4 0 0 0 2-7.464"/><path d="M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"/><path d="M6 18a4 4 0 0 1-2-7.464"/><path d="M6.003 5.125a4 4 0 0 0-2.526 5.77"/></g>',
    'chart-column': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3v16a2 2 0 0 0 2 2h16m-3-4V9m-5 8V5M8 17v-3"/>',
    'chart-no-axes-column': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 21v-6m7 6V3m7 18V9"/>',
    'check': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 6L9 17l-5-5"/>',
    'clipboard-list': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2m4 7h4m-4 5h4m-8-5h.01M8 16h.01"/></g>',
    'database': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></g>',
    'download': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M12 15V3m9 12v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10l5 5l5-5"/></g>',
    'eye': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M2.062 12.348a1 1 0 0 1 0-.696a10.75 10.75 0 0 1 19.876 0a1 1 0 0 1 0 .696a10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></g>',
    'file-down': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/><path d="M14 2v5a1 1 0 0 0 1 1h5m-8 10v-6m-3 3l3 3l3-3"/></g>',
    'file-text': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/><path d="M14 2v5a1 1 0 0 0 1 1h5M10 9H8m8 4H8m8 4H8"/></g>',
    'filter': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M22 3H2l8 9.46V19l4 2v-8.54z"/>',
    'flask-conical': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2M6.453 15h11.094M8.5 2h7"/>',
    'git-fork': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9m6 3v3"/></g>',
    'globe': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20a14.5 14.5 0 0 0 0-20M2 12h20"/></g>',
    'graduation-cap': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0zM22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/></g>',
    'hand': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2m0 4V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2m0 4.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/></g>',
    'heart-pulse': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M2 9.5a5.5 5.5 0 0 1 9.591-3.676a.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5"/><path d="M3.22 13H9.5l.5-1l2 4.5l2-7l1.5 3.5h5.27"/></g>',
    'house': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></g>',
    'layers': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/></g>',
    'lock': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></g>',
    'mic': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M12 19v3m7-12v2a7 7 0 0 1-14 0v-2"/><rect width="6" height="13" x="9" y="2" rx="3"/></g>',
    'moon': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401"/>',
    'play': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"/>',
    'route': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/></g>',
    'scale': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M12 3v18m7-13l3 8a5 5 0 0 1-6 0zV7"/><path d="M3 7h1a17 17 0 0 0 8-2a17 17 0 0 0 8 2h1M5 8l3 8a5 5 0 0 1-6 0zV7m2 14h10"/></g>',
    'school': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M14 21v-3a2 2 0 0 0-4 0v3m8-16.067V21M4 6l7.106-3.79a2 2 0 0 1 1.788 0L20 6"/><path d="m6 11l-3.52 2.147a1 1 0 0 0-.48.854V19a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a1 1 0 0 0-.48-.853L18 11M6 4.933V21"/><circle cx="12" cy="9" r="2"/></g>',
    'search': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="m21 21l-4.34-4.34"/><circle cx="11" cy="11" r="8"/></g>',
    'sigma': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 7V5a1 1 0 0 0-1-1H6.5a.5.5 0 0 0-.4.8l4.5 6a2 2 0 0 1 0 2.4l-4.5 6a.5.5 0 0 0 .4.8H17a1 1 0 0 0 1-1v-2"/>',
    'smile': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2s4-2 4-2M9 9h.01M15 9h.01"/></g>',
    'sparkles': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594zM20 2v4m2-2h-4"/><circle cx="4" cy="20" r="2"/></g>',
    'target': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></g>',
    'test-tube': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.5 2v17.5c0 1.4-1.1 2.5-2.5 2.5s-2.5-1.1-2.5-2.5V2m-1 0h7m-1 14h-5"/>',
    'timer': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M10 2h4m-2 12l3-3"/><circle cx="12" cy="14" r="8"/></g>',
    'triangle-alert': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m21.73 18l-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3M12 9v4m0 4h.01"/>',
    'users': '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M16 3.128a4 4 0 0 1 0 7.744M22 21v-2a4 4 0 0 0-3-3.87"/><circle cx="9" cy="7" r="4"/></g>',
    'wrench': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"/>',
    'zap': '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.914 4a1.5 1.5 0 0 0-2.474-1.561l-9 9A1.5 1.5 0 0 0 5.5 14h4.002a.5.5 0 0 1 .471.666L8.086 20a1.5 1.5 0 0 0 2.475 1.56l9-9A1.5 1.5 0 0 0 18.5 10h-3.997a.5.5 0 0 1-.472-.667z"/>',
}


def icon(name: str, size: int = 16, color: str | None = None) -> str:
    """渲染 Iconify(lucide) 内联 SVG 图标（stroke=currentColor，24×24 视窗）。"""
    body = _ICONS.get(name)
    if not body:
        return ""
    style = f' style="color:{color};" ' if color else ""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" {style} aria-hidden="true">{body}</svg>'
    )


# 模块级引用：避免组件函数内部被同名参数 shadow（icon 参数名与函数名同名）
_ICON_FN = icon


# =====================================================================
# 1. 全局样式（内联 CSS，零外部资源；浅米纸感 + 深炭内容块 + 噪点）
# =====================================================================
CSS = """
<style>
:root {
  --primary: #0078D4;
  --primary-hover: #006ABC;
  --primary-soft: #25A1F4;
  --accent: #A67C52;
  --good: #2F8F4E;
  --warn: #D13438;
  --bg: #F4F0E8;
  --block: rgba(34, 38, 48, 0.85);
  --warm: #C9B18F;
  --warm-deep: #3A342A;
  --border: #ffffff1a;
  --text1: #ffffff;
  --text2: #f0f0f2;
  --text3: #b8bcc6;
  --title: #ffffff;
  --paper-text: #2F261F;
  --paper-muted: #4A3D31;
  --surface-radius: 12px;
  --surface-shadow: 0 8px 28px rgba(35, 27, 20, .12);
  --ease-out-quint: cubic-bezier(0.1, 0.9, 0.2, 1);
  --noise: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0.12'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
}
html, body, .stApp, [class*="css"] {
  font-family: "Segoe UI Variable", "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
}
/* 浅米纸感背景 + 暖色径向微光（低对比柔和），叠 4% 噪点 */
.stApp {
  background-color: var(--bg);
  background-image: radial-gradient(circle at 0 0, rgba(166, 124, 82, 0.10), transparent 40%), var(--noise);
}
[data-testid="stHeader"] { background: rgba(244, 240, 232, .85); backdrop-filter: blur(10px); }
[data-testid="stMainBlockContainer"] {
  max-width: 1480px;
  padding-top: 4.35rem;
  padding-bottom: 4rem;
}

/* 键盘可见焦点：展示模式下仍保留清晰的可访问性反馈 */
button:focus-visible, input:focus-visible, textarea:focus-visible,
[role="tab"]:focus-visible, [role="radio"]:focus-visible {
  outline: 3px solid rgba(0, 120, 212, .34) !important;
  outline-offset: 2px !important;
}

/* ---------- 侧边栏（米色 #E8DFCF · 选中项暖棕底 + 蓝色指示条） ---------- */
[data-testid="stSidebar"] { background-color: #E8DFCF; background-image: var(--noise); border-right: 1px solid #00000014; }
[data-testid="stSidebar"] hr { border-color: #0000001f; margin: .7rem 0; }
[data-testid="stSidebar"] [role="radiogroup"] { display:flex; flex-direction:column; gap:6px; width:100%; outline:none; }
[data-testid="stSidebar"] [role="radiogroup"] label {
  position:relative; display:flex; align-items:center;
  width:100%; min-width:0; height:44px; min-height:44px; max-height:44px;
  box-sizing:border-box; padding:0 12px; margin:0 !important;
  border:1px solid #00000014; border-radius:8px;
  background-color: #ffffffd9; background-image: var(--noise);
  box-shadow: 0 2px 6px #0000000d;
  transition: all .22s var(--ease-out-quint); cursor:pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  transform:translateY(-1px); box-shadow:0 4px 12px #00000014;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display:none !important; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:nth-child(2) {
  flex:1; min-width:0; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
  font-size:.86rem; font-weight:600; color:#4A3D31; line-height:1.35;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {
  font-size:.86rem; font-weight:600; color:#4A3D31; margin:0;
  overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  transform:none; border-color:transparent;
  background-color:#A67C522E; background-image: var(--noise);
  box-shadow: inset 3px 0 0 var(--primary), 0 4px 12px #00000010;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) div,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color:#2F261F !important; font-weight:700; }

/* ★演示主线 标记：右上角蓝色标签 */
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="04"]) > div:nth-child(2) { padding-right:74px; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="04"])::after {
  content:"★ 演示主线";
  position:absolute; top:50%; right:10px; transform:translateY(-50%);
  background:var(--primary); color:#ffffff;
  font-size:.6rem; font-weight:800; letter-spacing:.02em;
  padding:2px 7px; border-radius:6px; white-space:nowrap;
  box-shadow:0 2px 5px rgba(0,120,212,.30);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="04"]):has(input:checked)::after {
  background:var(--primary-hover); color:#fff; box-shadow:none;
}

/* ---------- 页头 / 区块标题（深色块 · 白色标题） ---------- */
.dsh-hero {
  position:relative; overflow:hidden;
  display:flex; align-items:center; gap:1.05rem; padding:1.2rem 1.45rem;
  background-color: var(--block); background-image: var(--noise);
  border:1px solid rgba(255, 255, 255, 0.12); border-radius:var(--surface-radius); margin-bottom:.85rem;
  box-shadow: var(--surface-shadow);
  animation: dshFadeIn .5s var(--ease-out-quint) backwards;
}
.dsh-hero::before {
  content:""; position:absolute; inset:0 auto 0 0; width:4px;
  background:linear-gradient(180deg, #C9B18F, #8C6E4A);
}
.dsh-hero::after {
  content:""; position:absolute; width:210px; height:210px; right:-90px; top:-125px;
  border-radius:50%; border:1px solid rgba(201,177,143,.18);
  box-shadow:0 0 0 34px rgba(201,177,143,.045), 0 0 0 68px rgba(201,177,143,.025);
  pointer-events:none;
}
.dsh-hero-icon {
  position:relative; z-index:1; width:52px; height:52px; min-width:52px; border-radius:10px;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(145deg, rgba(255,255,255,.11), rgba(255,255,255,.045));
  border:1px solid rgba(255,255,255,.17); color:var(--warm);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08);
}
.dsh-hero-copy { position:relative; z-index:1; min-width:0; }
.dsh-hero-kicker {
  color:var(--warm); font-size:.66rem; font-weight:800; letter-spacing:.12em;
  text-transform:uppercase; margin-bottom:.25rem;
}
.dsh-hero-title { font-size:clamp(1.16rem, 2vw, 1.42rem); font-weight:800; color:var(--title); line-height:1.2; letter-spacing:-.015em; }
.dsh-hero-sub { font-size:.82rem; color:var(--text2); margin-top:.3rem; line-height:1.55; }
.dsh-hero-tag {
  position:relative; z-index:1; margin-left:auto; background:#8C6E4A; color:#FDFBF6;
  padding:.28rem .8rem; border-radius:999px; font-size:.75rem; font-weight:700; white-space:nowrap;
  border:1px solid rgba(255,255,255,.10); box-shadow:0 4px 14px rgba(0,0,0,.14);
}
.dsh-section {
  display:inline-flex; align-items:center; flex-wrap:wrap; gap:.35rem .55rem;
  max-width:100%; background-color:rgba(34, 38, 48, 0.85); border:1px solid rgba(255, 255, 255, 0.10);
  border-left:3px solid var(--warm); border-radius:6px;
  padding:.42rem .8rem; margin:.55rem 0 .65rem;
  font-weight:800; font-size:.92rem; color:#ffffff;
  box-shadow:0 2px 8px #00000018;
}
.dsh-section-note { color:#c9ccd3; font-weight:500; font-size:.73rem; line-height:1.45; }

/* ---------- 卡片体系（深色块承载白字 · 原圆角/阴影/尺寸不变） ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
  background-color: var(--block); background-image: var(--noise);
  border:1px solid rgba(255, 255, 255, 0.10) !important; border-radius:var(--surface-radius) !important;
  box-shadow: var(--surface-shadow);
  padding:.45rem .55rem;
  transition: transform .22s var(--ease-out-quint), box-shadow .22s var(--ease-out-quint);
  animation: dshFadeIn .5s var(--ease-out-quint) backwards;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow:0 6px 20px #00000024;
}
@keyframes dshFadeIn { from { opacity:0; transform: translateY(10px);} to {opacity:1; transform: translateY(0);} }

.dsh-stat {
  background-color: var(--block); background-image:var(--noise);
  border:1px solid rgba(255, 255, 255, 0.10); border-radius:var(--surface-radius); padding:1rem 1.1rem; position:relative;
  box-shadow:var(--surface-shadow);
  transition: all .22s var(--ease-out-quint); animation: dshFadeIn .5s var(--ease-out-quint) backwards;
}
.dsh-stat:hover { transform:translateY(-2px); box-shadow:0 6px 20px #00000024; }
.dsh-stat-icon { position:absolute; top:.85rem; right:1rem; color:var(--warm); }
.dsh-stat-value { font-size:1.6rem; font-weight:800; color:var(--text1); line-height:1.15; font-variant-numeric:tabular-nums; }
.dsh-stat-label { font-size:.78rem; color:var(--text2); margin-top:.2rem; }
.dsh-stat-delta { font-size:.7rem; color:#54B95A; margin-top:.28rem; font-weight:600; }

.dsh-info {
  background-color: var(--block); background-image:var(--noise);
  border:1px solid rgba(255, 255, 255, 0.10); border-radius:var(--surface-radius); padding:1.05rem 1.15rem;
  box-shadow:var(--surface-shadow); animation: dshFadeIn .5s var(--ease-out-quint) backwards;
}
.dsh-info-title { font-weight:800; color:var(--title); margin-bottom:.5rem; display:flex; gap:.5rem; align-items:center; }
.dsh-info-line { font-size:.85rem; color:var(--text2); line-height:1.7; margin-bottom:.2rem; }
.dsh-info-line b { color:var(--text1); }

.dsh-tag {
  display:inline-block; padding:.14rem .6rem; border-radius:999px;
  font-size:.72rem; font-weight:700; margin:.1rem .25rem .1rem 0;
}

/* ---------- 进度条 / 环形仪表（暖棕同色系） ---------- */
[data-testid="stProgress"] > div > div > div {
  background-image: linear-gradient(90deg, #8C6E4A, #A67C52) !important;
  transition: width .3s var(--ease-out-quint);
}
.dsh-fbar { margin-bottom:.7rem; }
.dsh-fbar-head { display:flex; justify-content:space-between; font-size:.82rem; font-weight:700; color:var(--text2); margin-bottom:.28rem; }
.dsh-fbar-track { height:9px; background:rgba(255,255,255,.14); border-radius:999px; overflow:hidden; }
.dsh-fbar-fill { height:100%; border-radius:999px; transition: width .3s var(--ease-out-quint); }
.dsh-gauge {
  width:150px; height:150px; border-radius:50%; margin:.2rem auto .5rem;
  background: conic-gradient(#8C6E4A 0deg, #C9B18F calc(var(--p) * 3.6deg), rgba(255,255,255,.14) calc(var(--p) * 3.6deg) 360deg);
  display:flex; align-items:center; justify-content:center;
  box-shadow: 0 10px 24px rgba(0,0,0,.20);
  transition: all .3s var(--ease-out-quint);
}
.dsh-gauge-inner {
  width:110px; height:110px; border-radius:50%; background-color:rgba(34, 38, 48, 0.9);
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  box-shadow: inset 0 2px 8px rgba(0,0,0,.35);
}
.dsh-gauge-value { font-size:1.85rem; font-weight:800; color:var(--text1); line-height:1.1; }
.dsh-gauge-label { font-size:.72rem; color:var(--text3); margin-top:2px; }
.dsh-flow-status { border-radius:8px; padding:.55rem .8rem; font-size:.84rem; font-weight:600; margin-top:.4rem; line-height:1.55; }

/* ---------- 学生反馈气泡（深色块 · 白字） ---------- */
.dsh-bubble {
  background-color: var(--block); background-image:var(--noise);
  border:1px solid rgba(255, 255, 255, 0.10); border-left:4px solid var(--warm);
  border-radius:8px; padding:.6rem .8rem; margin-bottom:.55rem;
  box-shadow:0 4px 16px #00000018; animation: dshFadeIn .4s var(--ease-out-quint) backwards;
}
.dsh-bubble-head { display:flex; align-items:center; gap:.45rem; margin-bottom:.28rem; }
.dsh-bubble-head b { font-size:.85rem; color:var(--title); }
.dsh-bubble-role { font-size:.7rem; color:#fff; background:#8C6E4A; padding:.05rem .5rem; border-radius:999px; }
.dsh-bubble-body { font-size:.84rem; color:var(--text2); line-height:1.6; }

/* ---------- 三步操作步骤指示 ---------- */
.dsh-step {
  border-radius:8px; padding:.55rem .75rem; border:1.5px solid rgba(255, 255, 255, 0.10);
  background-color: rgba(255, 255, 255, 0.04); background-image: var(--noise);
  display:flex; gap:.55rem; align-items:center; margin-bottom:.5rem;
  transition: all .25s var(--ease-out-quint); font-size:.86rem; color:var(--text2);
}
.dsh-step-num {
  width:24px; height:24px; min-width:24px; border-radius:6px;
  display:flex; align-items:center; justify-content:center;
  font-size:.75rem; font-weight:800; color:#fff; background:#4A4A4A;
}
.dsh-step-done { border-color:rgba(47,143,78,.45); background:rgba(47,143,78,.12); color:#9ED9AC; }
.dsh-step-done .dsh-step-num { background:#2F8F4E; }
.dsh-step-current {
  border-color:transparent; background:rgba(166,124,82,.12); color:#E3C9A6; font-weight:800;
  box-shadow: 0 0 0 2px rgba(166,124,82,.28), 0 6px 18px rgba(166,124,82,.14);
}
.dsh-step-current .dsh-step-num { background:#8C6E4A; }
.dsh-step-locked { opacity:.55; background-color:rgba(0,0,0,.30); color:#8A8A8A; }

/* ---------- 按钮分级（暖棕主按钮 · 浅棕描边次按钮） ---------- */
[data-testid="stBaseButton-primary"], .stButton > button[kind="primary"] {
  background: #8C6E4A !important;
  color:#FDFBF6 !important; border:none !important; border-radius:8px !important;
  min-height:2.55rem; font-weight:700; transition: all .22s var(--ease-out-quint);
}
[data-testid="stBaseButton-primary"]:hover, .stButton > button[kind="primary"]:hover {
  background:#A67C52 !important; box-shadow:0 4px 12px rgba(140,110,74,.30);
}
[data-testid="stBaseButton-secondary"], .stButton > button[kind="secondary"] {
  background:transparent !important; color:#C9B18F !important;
  border:1.5px solid rgba(201,177,143,.6) !important; border-radius:8px !important;
  min-height:2.55rem; font-weight:600; transition: all .22s var(--ease-out-quint);
}
[data-testid="stBaseButton-secondary"]:hover { background:rgba(201,177,143,.08) !important; }
[data-testid="stBaseButton-disabled"], .stButton > button[kind="disabled"], .stButton > button:disabled {
  background:#2A2E36 !important; color:#8A8A8A !important; border:none !important; cursor:not-allowed !important;
}

/* ---------- 其余原生组件 ---------- */
[data-testid="stExpander"] {
  background-color: var(--block); border:1px solid rgba(255, 255, 255, 0.10) !important; border-radius:var(--surface-radius) !important;
  box-shadow:var(--surface-shadow);
}
[data-testid="stVerticalBlockBorderWrapper"] label,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stWidgetLabel"] p,
[data-testid="stExpander"] label,
[data-testid="stExpander"] summary { color:var(--text2) !important; }
[data-baseweb="input"] > div, [data-baseweb="textarea"] > div,
[data-baseweb="select"] > div {
  border-radius:8px !important;
  transition:border-color .22s var(--ease-out-quint), box-shadow .22s var(--ease-out-quint);
}
[data-baseweb="input"]:focus-within > div, [data-baseweb="textarea"]:focus-within > div,
[data-baseweb="select"]:focus-within > div {
  border-color:rgba(166,124,82,.85) !important;
  box-shadow:0 0 0 3px rgba(166,124,82,.14) !important;
}
[data-testid="stFileUploaderDropzone"] { border-radius:10px; }
[data-testid="stDialog"] > div:first-child { border-radius:12px !important; }
blockquote {
  background:rgba(47,143,78,.10); border-left:4px solid #2F8F4E; border-radius:0 8px 8px 0;
  padding:.5rem .9rem; margin:.45rem 0; color:#9ED9AC;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:var(--warm); font-weight:700; }
[data-testid="stTabs"] [role="tablist"] { gap:.35rem; }
[data-testid="stTabs"] [role="tab"] { border-radius:7px 7px 0 0; padding-inline:.8rem; }
hr { border-color:#00000014 !important; }
footer { visibility:hidden; }
#MainMenu { visibility:hidden; }

/* ---------- 响应式与减弱动画 ---------- */
@media (max-width: 900px) {
  [data-testid="stMainBlockContainer"] { padding-left:1rem; padding-right:1rem; }
  .dsh-hero { align-items:flex-start; padding:1rem 1.05rem; gap:.8rem; }
  .dsh-hero-tag { margin-left:0; }
  .dsh-hero::after { opacity:.55; }
}
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"] { padding-left:.75rem; padding-right:.75rem; }
  .dsh-hero { flex-wrap:wrap; }
  .dsh-hero-copy { width:calc(100% - 66px); }
  .dsh-hero-tag { margin-left:66px; margin-top:-.15rem; }
  .dsh-section { display:flex; width:100%; box-sizing:border-box; }
  .dsh-section-note { flex-basis:100%; }
  .dsh-stat-value { font-size:1.4rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration:.01ms !important; transition-duration:.01ms !important; }
}

/* ---------- 侧边栏品牌区 / 徽章（米色纸感） ---------- */
.dsh-brand {
  background-color:#ffffffd9; background-image:var(--noise);
  border:1px solid #00000014; border-radius:10px; padding:.85rem .9rem; margin-bottom:.25rem;
  box-shadow:0 2px 6px #0000000d;
}
.dsh-brand-title { font-size:.98rem; font-weight:800; color:#2F261F; }
.dsh-brand-sub { font-size:.73rem; color:#4A3D31; margin-top:.3rem; line-height:1.55; }
.dsh-badge {
  display:inline-flex; align-items:center; gap:.4rem; padding:.28rem .75rem;
  border-radius:8px; font-size:.74rem; font-weight:700;
}
.dsh-foot { font-size:.7rem; color:#4A3D31; padding-top:.4rem; line-height:1.6; }
</style>
"""


def inject_css():
    """注入全局美化样式。"""
    st.markdown(CSS, unsafe_allow_html=True)


def safe_text(value) -> str:
    """将用户输入或后端文本转为可安全插入 HTML 的纯文本。

    公共卡片仍支持页面传入可信的内置 HTML；只在数据来自用户或后端时
    由调用方显式使用本函数，避免破坏现有 ``<b>`` 等可信样式。
    """
    return html.escape("" if value is None else str(value), quote=True)


# =====================================================================
# 2. 会话状态集中初始化
# =====================================================================
def init_session_state():
    """集中初始化全部会话状态，统一守卫，避免跨页状态丢失。"""
    defaults = {
        "nav_radio": "01",                       # 当前导航页 id
        # ---- 课程设计工作台（演示主线）----
        "ws_stage": 0,                           # 0=未开始 1=AI初生成 2=人工迭代 3=素养校验
        "ws_lesson": None,                       # 教案 Markdown 文本
        "ws_itrs": [
            ("跨学科教学设计能力", 82.0, "#8C6E4A"),
            ("教学实施与调控能力", 75.0, "#A67C52"),
            ("技术融合应用能力", 78.0, "#6B6252"),
            ("元认知反思能力", 80.0, "#7A8B6F"),
        ],
        "ws_stem": [
            ("科学思维", 86.0, "#8C6E4A"),
            ("数学建模", 72.0, "#A67C52"),
            ("工程实践", 70.0, "#6B6252"),
            ("技术应用", 81.0, "#7A8B6F"),
            ("社会责任", 90.0, "#4F5D4A"),
        ],
        "ws_check_conclusion": (
            "结论：素养对齐校验通过，综合达标率 92%。"
            "证据链：科学思维 ← 问题链 Q4/Q5（物理热力学 → 科学思维素养）；"
            "社会责任 ← 情境导入与方案发布会（碳中和 → 社会责任素养）；"
            "数学建模 ← 活动二固碳量测算。"
            "待强化：工程实践维度（70%）建议增加“光伏方案原型搭建”环节。"
        ),
        "ws_design_context": None,               # 生成时的学段 / 主题 / 课时快照
        # ---- 教学模拟实训 ----
        "sim_started": False,
        "sim_round": 0,                          # 互动轮次（驱动确定性数值变化）
        "flow": {"load": 46.0, "engage": 55.0, "confuse": 52.0, "flow": 58.0},
        "flow_status": "",                       # 自适应状态文案（后端 /status 可覆盖）
        "sim_feedback": None,                    # 后端返回的虚拟学生反馈（None=用内置话术池）
        "sim_signals": None,                     # 后端返回的多模态信号（None=本地计算）
        "sim_teacher_input": "",                # 工作台传入的可编辑授课片段
        # ---- 智能诊断 ----
        "diag_ready": False,
        "diag_lesson_text": "",                 # 粘贴 / TXT / 跨页传入的课例正文
        "diag_result": None,                     # 本次生成的诊断结果缓存
        "diag_trace": None,                      # 与诊断结果同步的溯源子图
        "diag_input_snapshot": None,             # 生成报告时的输入快照
        # ---- 科研孵化 ----
        "research_ready": False,
        "research_pain": "",                    # 独立输入或诊断带入的教学痛点
        "research_result": None,                 # 本次生成的科研方案缓存
        "research_input_snapshot": None,         # 生成方案时的输入快照
        # ---- 知识图谱 ----
        "kg_domain": "all",                      # 当前图谱子域（all=全局总览）
        # ---- 后端连接状态 ----
        "backend_status": None,                  # ("ok"|"down"|"bad_response", 详情)
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


# =====================================================================
# 3. 统一样式组件
# =====================================================================
def page_header(icon_name: str, title: str, subtitle: str, tag: str | None = None):
    """渐变页头横幅（Iconify 图标 + 标题 + 功能标签）。"""
    tag_html = f'<span class="dsh-hero-tag">{tag}</span>' if tag else ""
    try:
        module_id = str(st.session_state["nav_radio"])
    except (KeyError, AttributeError):
        module_id = "01"
    st.markdown(
        f"""<div class="dsh-hero">
        <div class="dsh-hero-icon">{icon(icon_name, 26)}</div>
        <div class="dsh-hero-copy"><div class="dsh-hero-kicker">模块 {module_id} / 07 · 教—学—研一体化</div>
        <div class="dsh-hero-title">{title}</div><div class="dsh-hero-sub">{subtitle}</div></div>
        {tag_html}</div>""",
        unsafe_allow_html=True,
    )


def section_title(text: str, note: str = ""):
    """左侧暖棕竖线 + 小标题的区块分隔样式。"""
    note_html = f'<span class="dsh-section-note">{note}</span>' if note else ""
    st.markdown(f'<div class="dsh-section"><span>{text}</span>{note_html}</div>', unsafe_allow_html=True)


def stat_card(value, label, delta=None, icon=None, icon_name=None):
    """统一样式统计卡片：数值大号加粗，标签/增量居下，右上角 Iconify 图标点缀。"""
    name = icon_name or icon or "activity"
    d = f'<div class="dsh-stat-delta">{delta}</div>' if delta else ""
    st.markdown(
        f"""<div class="dsh-stat"><div class="dsh-stat-icon">{_ICON_FN(name, 18)}</div>
        <div class="dsh-stat-value">{value}</div>
        <div class="dsh-stat-label">{label}</div>{d}</div>""",
        unsafe_allow_html=True,
    )


def info_card(title: str, lines, icon=None, icon_name=None, tone=None, light=False):
    """统一样式信息卡片。light=True 时为浅色方块（用于知识图谱子域说明等分类文字）。"""
    if light:
        t = tone or "#8C6E4A"
        name = icon_name or icon or None
        head = f'<span style="color:{t};">{_ICON_FN(name, 17)}</span>' if name else ""
        body = "".join(
            f'<div class="dsh-info-line" style="color:#3A3129;">{line}</div>' for line in lines
        )
        st.markdown(
            f"""<div class="dsh-info" style="background-color:#FDFBF6; border:1px solid rgba(0,0,0,.10);
            box-shadow:0 2px 10px rgba(0,0,0,.06);">
            <div class="dsh-info-title" style="color:#2F261F;">{head}
            <span style="border-left:3px solid {t}; padding-left:.5rem;">{title}</span></div>
            {body}</div>""",
            unsafe_allow_html=True,
        )
        return
    t = tone or "#8C6E4A"
    name = icon_name or icon or None
    head = f'<span style="color:{t};">{_ICON_FN(name, 17)}</span>' if name else ""
    body = "".join(f'<div class="dsh-info-line">{line}</div>' for line in lines)
    st.markdown(
        f"""<div class="dsh-info">
        <div class="dsh-info-title">{head}
        <span style="border-left:3px solid {t}; padding-left:.5rem;">{title}</span></div>
        {body}</div>""",
        unsafe_allow_html=True,
    )


def tag(text: str, color: str | None = None):
    """圆角小标签（浅色方块：白底 + 彩色文字 + 浅描边）。"""
    c = color or "#8C6E4A"
    st.markdown(
        f'<span class="dsh-tag" style="background:#FDFBF6; color:{c}; border:1px solid rgba(0,0,0,0.10);">{text}</span>',
        unsafe_allow_html=True,
    )


def signal_bar(label: str, value: float, note: str | None = None, color: str | None = None,
               icon: str | None = None, icon_name: str | None = None):
    """通用渐变进度条（多模态信号栏 / 素养达标面板复用）。"""
    c = color or "#8C6E4A"
    name = icon_name or icon or None
    ic = _ICON_FN(name, 14, c) if name else ""
    note_html = f'<span style="color:{config.COLORS["text_3"]}; font-size:.72rem; font-weight:500;">{note}</span>' if note else ""
    st.markdown(
        f"""<div class="dsh-fbar">
        <div class="dsh-fbar-head"><span>{ic} {label} {note_html}</span><span>{value:.0f}%</span></div>
        <div class="dsh-fbar-track"><div class="dsh-fbar-fill" style="width:{min(max(value, 0), 100):.0f}%; background:linear-gradient(90deg, {c}, {config.COLORS['primary_deep']});"></div></div>
        </div>""",
        unsafe_allow_html=True,
    )


def mock_badge():
    """Mock 模式状态徽章。"""
    if config.MOCK_MODE:
        html = ('<span class="dsh-badge" style="background:#ffffffd9; color:#107C10; border:1px solid #00000014;">'
                '<span style="width:8px;height:8px;border-radius:50%;background:#2F8F4E;display:inline-block;"></span>'
                'Mock 演示模式 · 数据为内置示例</span>')
    else:
        html = ('<span class="dsh-badge" style="background:#ffffffd9; color:#7D630C; border:1px solid #00000014;">'
                '已关闭 Mock · 对接真实后端 ' + safe_text(config.API_BASE) + '</span>')
    st.markdown(html, unsafe_allow_html=True)


def backend_badge():
    """后端连接状态徽章（仅 MOCK_MODE=False 时展示）。"""
    if config.MOCK_MODE:
        return
    try:
        status = st.session_state["backend_status"]
    except (KeyError, AttributeError):
        status = None
    if status is None:
        html = ('<span class="dsh-badge" style="background:#ffffffd9; color:#4A3D31; border:1px solid #00000014;">'
                '后端待请求 · 首次操作后显示连接状态</span>')
    elif status[0] == "ok":
        html = ('<span class="dsh-badge" style="background:#ffffffd9; color:#107C10; border:1px solid #00000014;">'
                f'后端已连接 · 真实数据（{safe_text(status[1])}）</span>')
    elif status[0] == "bad_response":
        html = ('<span class="dsh-badge" style="background:#ffffffd9; color:#D13438; border:1px solid #00000014;">'
                f'后端响应异常（{safe_text(status[1])}）· 已回退 Mock</span>')
    else:
        html = ('<span class="dsh-badge" style="background:#ffffffd9; color:#7D630C; border:1px solid #00000014;">'
                '后端不可用 · 已回退 Mock 兜底</span>')
    st.markdown(html, unsafe_allow_html=True)


# =====================================================================
# 4. 心流自适应仪表盘
# =====================================================================
def flow_dashboard(flow, status=None):
    """心流自适应仪表盘。

    flow: dict(load=认知负荷, engage=课堂参与度, confuse=学生困惑度, flow=综合心流指数)
    status: 可选，后端返回的自适应状态文案；缺省时按心流指数区间自动生成。
    真实模式下 flow 由 /api/sim/flow 返回；Mock 模式下使用确定性内置数值。
    """
    bars = [
        ("认知负荷", flow["load"], "#8C6E4A", "越低越从容"),
        ("课堂参与度", flow["engage"], "#2F8F4E", "越高越好"),
        ("学生困惑度", flow["confuse"], "#C66A5A", "越低越好"),
    ]
    html = []
    for name, val, color, note in bars:
        html.append(
            f"""<div class="dsh-fbar">
            <div class="dsh-fbar-head"><span>{name} <span style="color:{config.COLORS['text_3']}; font-size:.72rem; font-weight:500;">{note}</span></span>
            <span>{val:.0f}%</span></div>
            <div class="dsh-fbar-track"><div class="dsh-fbar-fill" style="width:{min(max(val, 0), 100):.0f}%; background:linear-gradient(90deg, {color}, {config.COLORS['primary_deep']});"></div></div>
            </div>"""
        )
    st.markdown("".join(html), unsafe_allow_html=True)

    f = flow["flow"]
    if status:
        msg = status
    elif f >= 75:
        msg = "深度心流：认知负荷适中、参与度高。建议保持节奏，并适时深化高阶提问。"
    elif f >= 55:
        msg = "心流平稳：学生参与稳定。可插入跨学科迁移任务，适度提升挑战度。"
    else:
        msg = "心流偏低：认知负荷或困惑度过高。建议分解概念、放慢语速并增加即时反馈。"
    if f >= 75:
        tone = "background:rgba(47,143,78,.16); color:#9ED9AC; border:1px solid rgba(47,143,78,.35);"
    elif f >= 55:
        tone = "background:rgba(166,124,82,.14); color:#E3C9A6; border:1px solid rgba(166,124,82,.30);"
    else:
        tone = "background:rgba(214,76,66,.16); color:#F2B8B5; border:1px solid rgba(214,76,66,.35);"
    st.markdown(
        f"""<div style="text-align:center;">
        <div class="dsh-gauge" style="--p:{min(max(f, 0), 100):.0f};">
          <div class="dsh-gauge-inner">
            <div class="dsh-gauge-value">{f:.0f}</div>
            <div class="dsh-gauge-label">综合心流指数</div>
          </div>
        </div></div>
        <div class="dsh-flow-status" style="{tone}">{msg}</div>""",
        unsafe_allow_html=True,
    )


# =====================================================================
# 5. 知识图谱可视化（streamlit-agraph 封装）
# =====================================================================
def render_kg(nodes, edges, height=540, key="kg", hierarchical=False, direction="UD"):
    """图谱画布渲染：按节点类型自动着色，附带节点-关系兜底表格。

    本阶段 nodes/edges 由页面内置的 61 实体 / 61 关系图谱提供。
    """
    if not nodes:
        st.info("当前子域暂无图谱数据。")
        return

    degree = {}
    for e in edges:
        degree[e[0]] = degree.get(e[0], 0) + 1
        degree[e[1]] = degree.get(e[1], 0) + 1

    ag_nodes, ag_edges = [], []
    for n in nodes:
        color = config.NODE_TYPES.get(n.get("type"), config.COLORS["primary"])
        base = n.get("size", 18)
        size = base + degree.get(n["id"], 0) * 1.6
        ag_nodes.append(
            Node(
                id=n["id"],
                label=n["label"],
                title=n.get("desc", ""),
                size=size,
                color=color,
                shape="dot",
                borderWidth=1.5,
                font={"color": "#FFFFFF", "size": 13, "face": "Microsoft YaHei"},
            )
        )
    for e in edges:
        src, dst, rel = e[0], e[1], e[2] if len(e) > 2 else ""
        dashed = len(e) > 3 and e[3]
        ag_edges.append(
            Edge(
                source=src,
                target=dst,
                label=rel,
                arrows="to",
                dashes=dashed,
                color={"color": "#8A8A8A", "highlight": "#C9B18F", "hover": "#A67C52"},
                font={"size": 10, "color": "#b8bcc6", "face": "Microsoft YaHei", "strokeWidth": 2},
            )
        )

    ag_config = AgraphConfig(
        width="100%",
        height=height,
        directed=True,
        physics=not hierarchical,
        hierarchical=hierarchical,
        direction=direction,
        levelSeparation=175,
        nodeSpacing=95,
        nodeHighlightBehavior=True,
        highlightColor={"border": "#C9B18F", "background": "rgba(140,110,74,0.25)"},
        hoverColor={"border": "#A67C52", "background": "rgba(166,124,82,0.25)"},
        nodes={"font": {"color": "#FFFFFF", "size": 13, "face": "Microsoft YaHei"}, "borderWidth": 1, "shadow": False},
        edges={"color": {"color": "#8A8A8A", "highlight": "#C9B18F"}, "smooth": {"enabled": True, "type": "dynamic"}, "selectionWidth": 2},
    )
    agraph(nodes=ag_nodes, edges=ag_edges, config=ag_config)

    with st.expander("节点-关系明细表（画布不可用时的兜底视图）", expanded=False):
        st.caption(f"共 {len(nodes)} 个实体 · {len(edges)} 条关系")
        st.dataframe(
            [{"实体": n["label"], "类型": n.get("type", "-"), "所属子域": n.get("domain", "-"), "描述": n.get("desc", "")} for n in nodes],
            width="stretch", hide_index=True,
        )
        st.dataframe(
            [{"起点": _label_of(nodes, e[0]), "关系": e[2] if len(e) > 2 else "关联", "终点": _label_of(nodes, e[1])} for e in edges],
            width="stretch", hide_index=True,
        )


def _label_of(nodes, node_id):
    for n in nodes:
        if n["id"] == node_id:
            return n["label"]
    return node_id


def node_detail_panel(nodes, edges):
    """通过下拉选择器实现“节点点击查看详情”的等价交互。"""
    if not nodes:
        return
    options = [f'{n["label"]} · {n.get("type", "")}' for n in nodes]
    choice = st.selectbox("选择节点查看详情（等价于画布点击）", options, index=0)
    idx = options.index(choice)
    node = nodes[idx]

    c = config.NODE_TYPES.get(node.get("type"), "#8C6E4A")
    node_type = safe_text(node.get("type", ""))
    node_domain = safe_text(node.get("domain", "全局总览"))
    node_label = safe_text(node.get("label", ""))
    node_desc = safe_text(node.get("desc", "暂无描述"))
    st.markdown(
        f'<span class="dsh-tag" style="background:#FDFBF6; color:{c}; border:1px solid rgba(0,0,0,0.10);">{node_type}</span>'
        f'<span class="dsh-tag" style="background:#FDFBF6; color:#3A3129; border:1px solid rgba(0,0,0,0.10);">{node_domain}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="dsh-info" style="margin-top:.4rem;">'
        f'<div class="dsh-info-title">{icon("file-text", 16)} {node_label}</div>'
        f'<div class="dsh-info-line">{node_desc}</div></div>',
        unsafe_allow_html=True,
    )

    rels = []
    for e in edges:
        relation = safe_text(e[2] if len(e) > 2 else "关联")
        if e[0] == node["id"]:
            other = safe_text(_label_of(nodes, e[1]))
            rels.append(
                f'<span style="display:inline-flex;vertical-align:middle;color:#8C6E4A;">{icon("arrow-right", 13)}</span> '
                f'{other} <span class="dsh-tag" style="background:#FDFBF6; color:#3A3129; border:1px solid rgba(0,0,0,0.10);">{relation}</span>'
            )
        elif e[1] == node["id"]:
            other = safe_text(_label_of(nodes, e[0]))
            rels.append(
                f'<span style="display:inline-flex;vertical-align:middle;color:#8C6E4A;transform:rotate(180deg);">{icon("arrow-right", 13)}</span> '
                f'{other} <span class="dsh-tag" style="background:#FDFBF6; color:#3A3129; border:1px solid rgba(0,0,0,0.10);">{relation}</span>'
            )
    if rels:
        st.markdown(
            f'<div class="dsh-info" style="margin-top:.4rem;"><div class="dsh-info-title">{icon("git-fork", 16)} 关联关系（{len(rels)}）</div>'
            + "".join(f'<div class="dsh-info-line">{r}</div>' for r in rels)
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("该节点暂无关联关系。")


# =====================================================================
# 6. 统一接口网关（MOCK_MODE 一键切换）
# =====================================================================
_MISSING = object()


def _set_backend_status(state: str, detail: str = ""):
    try:
        st.session_state["backend_status"] = (state, detail)
    except Exception:
        pass


def _mock_copy(mock_result):
    """为回退数据创建独立副本，避免页面后续修改污染全局 Mock。"""
    return copy.deepcopy(mock_result)


def _fallback_field(mock_result, key: str, default=None):
    if isinstance(mock_result, dict) and key in mock_result:
        return copy.deepcopy(mock_result[key])
    return copy.deepcopy(default)


def _valid_text(value, *, allow_empty: bool = False) -> bool:
    return isinstance(value, str) and (allow_empty or bool(value.strip()))


def _valid_score(value) -> bool:
    """bool 是 int 的子类，但不应被当作业务分数。"""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        numeric = float(value)
    except (OverflowError, TypeError, ValueError):
        return False
    return math.isfinite(numeric) and 0 <= numeric <= 100


def _text_field(data, mock_result, key: str, issues: list[str], *, optional: bool = False):
    value = data.get(key, _MISSING)
    fallback = _fallback_field(mock_result, key)
    if optional and (value is None or value is _MISSING):
        return fallback
    if _valid_text(value):
        return value
    issues.append(key)
    return fallback


def _score_map_field(data, mock_result, key: str, issues: list[str], *, optional: bool = False):
    value = data.get(key, _MISSING)
    fallback = _fallback_field(mock_result, key)
    if optional and (value is None or value is _MISSING):
        return fallback
    if isinstance(value, dict) and value:
        cleaned = {}
        for name, score in value.items():
            if not _valid_text(name) or not _valid_score(score):
                break
            cleaned[name] = float(score)
        else:
            return cleaned
    issues.append(key)
    return fallback


def _clean_feedback(value):
    if not isinstance(value, list):
        return None
    cleaned = []
    for item in value:
        if not isinstance(item, dict):
            return None
        if not all(_valid_text(item.get(key)) for key in ("name", "role", "text")):
            return None
        cleaned.append({key: item[key] for key in ("name", "role", "text")})
    return cleaned


def _clean_signals(value):
    if not isinstance(value, list):
        return None
    cleaned = []
    for item in value:
        if not isinstance(item, dict):
            return None
        if not _valid_text(item.get("name")) or not _valid_score(item.get("value")):
            return None
        note = item.get("note", "")
        if not _valid_text(note, allow_empty=True):
            return None
        cleaned.append({"name": item["name"], "value": float(item["value"]), "note": note})
    return cleaned


def _clean_flow_response(data, mock_result):
    issues = []
    fallback_flow = _fallback_field(mock_result, "flow", {})
    raw_flow = data.get("flow")
    flow = {}
    for key in ("load", "engage", "confuse", "flow"):
        value = raw_flow.get(key, _MISSING) if isinstance(raw_flow, dict) else _MISSING
        if _valid_score(value):
            flow[key] = float(value)
        else:
            fallback = fallback_flow.get(key, 0.0) if isinstance(fallback_flow, dict) else 0.0
            flow[key] = float(fallback) if _valid_score(fallback) else 0.0
            issues.append(f"flow.{key}")

    cleaned = {
        "flow": flow,
        "status": _text_field(data, mock_result, "status", issues),
    }
    for key, cleaner in (("feedback", _clean_feedback), ("signals", _clean_signals)):
        value = data.get(key, _MISSING)
        parsed = cleaner(value)
        if parsed is None:
            issues.append(key)
            parsed = _fallback_field(mock_result, key)
        cleaned[key] = parsed
    return cleaned, issues


def _clean_problem_list(value):
    if not isinstance(value, list) or not value:
        return None
    fields = ("id", "title", "evidence", "cause", "suggest", "anchor")
    cleaned = []
    for item in value:
        if not isinstance(item, dict) or not all(_valid_text(item.get(key)) for key in fields):
            return None
        cleaned.append({key: item[key] for key in fields})
    return cleaned


def _clean_string_list(value):
    if not isinstance(value, list) or not all(_valid_text(item) for item in value):
        return None
    return list(value)


def _clean_trace(value):
    if not isinstance(value, dict):
        return None
    raw_nodes = value.get("nodes")
    raw_edges = value.get("edges")
    if not isinstance(raw_nodes, list) or not raw_nodes or not isinstance(raw_edges, list):
        return None

    nodes = []
    node_ids = set()
    for node in raw_nodes:
        if not isinstance(node, dict):
            return None
        if not all(_valid_text(node.get(key)) for key in ("id", "label", "type")):
            return None
        desc = node.get("desc", "")
        if not _valid_text(desc, allow_empty=True) or node["id"] in node_ids:
            return None
        node_ids.add(node["id"])
        nodes.append({"id": node["id"], "label": node["label"], "type": node["type"], "desc": desc})

    edges = []
    for edge in raw_edges:
        if not isinstance(edge, (list, tuple)) or len(edge) < 3:
            return None
        source, target, relation = edge[:3]
        if (
            not _valid_text(source)
            or not _valid_text(target)
            or not _valid_text(relation)
            or source not in node_ids
            or target not in node_ids
        ):
            return None
        edges.append([source, target, relation])
    return {"nodes": nodes, "edges": edges}


def _clean_diag_response(data, mock_result):
    issues = []
    cleaned = {
        "meta": _text_field(data, mock_result, "meta", issues),
        "conclusion": _text_field(data, mock_result, "conclusion", issues),
    }
    problems = _clean_problem_list(data.get("problems", _MISSING))
    if problems is None:
        issues.append("problems")
        problems = _fallback_field(mock_result, "problems", [])
    cleaned["problems"] = problems

    suggests = _clean_string_list(data.get("suggests", _MISSING))
    if suggests is None:
        issues.append("suggests")
        suggests = _fallback_field(mock_result, "suggests", [])
    cleaned["suggests"] = suggests

    trace = _clean_trace(data.get("trace", _MISSING))
    if trace is None:
        issues.append("trace")
        trace = _fallback_field(mock_result, "trace")
    cleaned["trace"] = trace
    return cleaned, issues


def _clean_workbench_response(data, mock_result, payload):
    issues = []
    cleaned = {}
    expected_by_action = {"generate": 1, "revise": 2, "check": 3}
    expected_stage = expected_by_action.get(payload.get("action")) if isinstance(payload, dict) else None
    stage = data.get("stage", _MISSING)
    if (
        isinstance(stage, int)
        and not isinstance(stage, bool)
        and stage in (1, 2, 3)
        and (expected_stage is None or stage == expected_stage)
    ):
        cleaned["stage"] = stage
    else:
        issues.append("stage")
        cleaned["stage"] = _fallback_field(mock_result, "stage", expected_stage or 1)

    cleaned["lesson_md"] = _text_field(data, mock_result, "lesson_md", issues)
    is_check = isinstance(payload, dict) and payload.get("action") == "check"
    cleaned["itrs"] = _score_map_field(data, mock_result, "itrs", issues, optional=not is_check)
    cleaned["stem"] = _score_map_field(data, mock_result, "stem", issues, optional=not is_check)
    cleaned["conclusion"] = _text_field(
        data, mock_result, "conclusion", issues, optional=not is_check
    )
    return cleaned, issues


def _clean_research_response(data, mock_result):
    issues = []
    cleaned = {
        key: _text_field(data, mock_result, key, issues)
        for key in ("topic_md", "lit_md", "survey_md", "exp_md")
    }
    return cleaned, issues


def _clean_endpoint_response(endpoint: str, data: dict, mock_result, payload):
    cleaners = {
        config.API_ENDPOINTS["sim_flow"]: lambda: _clean_flow_response(data, mock_result),
        config.API_ENDPOINTS["diag_report"]: lambda: _clean_diag_response(data, mock_result),
        config.API_ENDPOINTS["workbench_design"]: lambda: _clean_workbench_response(
            data, mock_result, payload
        ),
        config.API_ENDPOINTS["research_plan"]: lambda: _clean_research_response(data, mock_result),
    }
    cleaner = cleaners.get(endpoint)
    if cleaner is None:
        return data, []
    return cleaner()


def api_gate(endpoint: str, payload=None, mock_result=None, method: str = "POST"):
    """统一接口网关（契约见《API接口文档.md》）。

    MOCK_MODE=True  → 直接返回预置 Mock 数据（mock_result），不发起网络请求；
    MOCK_MODE=False → 请求 config.API_BASE + endpoint：
                      成功（HTTP 2xx 且 JSON 对象）→ 按接口契约清洗；
                      缺失 / 非法字段          → 仅用 Mock 补齐该字段；
                      失败 / 超时 / 异常      → 整体回退 mock_result。

    可选 config.API_TOKEN 通过 X-Token 请求头发送，不写入状态详情或日志。
    """
    if config.MOCK_MODE:
        _set_backend_status("mock", "内置示例")
        return _mock_copy(mock_result)

    url = f"{config.API_BASE.rstrip('/')}/{endpoint.lstrip('/')}"
    request_kwargs = {"json": payload or {}, "timeout": config.API_TIMEOUT}
    if config.API_TOKEN:
        request_kwargs["headers"] = {"X-Token": config.API_TOKEN}
    try:
        resp = requests.request(method, url, **request_kwargs)
    except requests.exceptions.RequestException as e:
        _set_backend_status("down", type(e).__name__)
        return _mock_copy(mock_result)

    if not 200 <= resp.status_code < 300:
        _set_backend_status("bad_response", f"HTTP {resp.status_code}")
        return _mock_copy(mock_result)

    try:
        data = resp.json()
    except ValueError:
        _set_backend_status("bad_response", f"HTTP {resp.status_code} · 非 JSON")
        return _mock_copy(mock_result)

    if not isinstance(data, dict):
        _set_backend_status("bad_response", f"HTTP {resp.status_code} · 响应不是对象")
        return _mock_copy(mock_result)
    if data.get("error") or data.get("success") is False:
        _set_backend_status("bad_response", f"HTTP {resp.status_code} · 业务错误")
        return _mock_copy(mock_result)

    cleaned, issues = _clean_endpoint_response(endpoint, data, mock_result, payload or {})
    if issues:
        summary = ", ".join(dict.fromkeys(issues))
        if len(summary) > 100:
            summary = summary[:97] + "..."
        _set_backend_status("bad_response", f"HTTP {resp.status_code} · Mock 补齐 {summary}")
    else:
        _set_backend_status("ok", f"HTTP {resp.status_code}")
    return cleaned


def is_mock_off(result) -> bool:
    """判断 api_gate 返回值是否为降级占位。"""
    return isinstance(result, dict) and result.get("mock_off") is True


def mock_off_placeholder(result):
    """Mock 关闭时的友好降级提示 + 占位卡片。"""
    st.warning(result.get("message", "Mock 模式已关闭，接口待联调。"))
    info_card(
        "接口待联调",
        [f"接口：{result.get('endpoint', '-')}",
         f"载荷：{result.get('payload') or '-'}"],
        icon_name="triangle-alert",
        tone=config.COLORS["warning"],
    )
