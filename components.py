# -*- coding: utf-8 -*-
"""components.py — 公共可复用组件沉淀（深色玻璃工作区体系）

职责（供 pages.py / app.py 复用，本模块不承载页面业务逻辑）：
1. inject_css()              全局内联样式：深灰基底、冷蓝微光、玻璃内容块、噪点肌理
2. icon()                    Iconify(lucide) 内联 SVG 渲染（禁 Emoji 功能图标）
3. init_session_state()      集中初始化全部会话状态，统一守卫
4. page_header / section_title / stat_card / info_card / tag / signal_bar  统一样式组件
5. flow_dashboard()          心流自适应仪表盘（渐变进度条 + conic-gradient 环形仪表 + 状态条）
6. render_kg()               streamlit-agraph 图谱渲染封装（按类型着色 + 兜底表格）
7. node_detail_panel()       下拉选择器等价实现“节点点击查看详情”
8. api_gate()                统一接口网关（真实请求 + 字段清洗 + Mock 回退）

设计规范：禁紫/靛蓝、禁纯平背景（噪点+径向微光）、侧边栏使用深色工作台，
禁 Emoji 功能图标、全站缓动统一 cubic-bezier(0.1,0.9,0.2,1)。
"""

import copy
import html
import json
import math
import uuid
from datetime import datetime, timezone

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
  box-sizing:border-box; padding:0 9px 0 13px; margin:0 !important;
  border:0; border-radius:6px;
  background:transparent;
  box-shadow:none;
  transition: all .22s var(--ease-out-quint); cursor:pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  transform:none; background:rgba(255,255,255,.28); box-shadow:none;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child,
[data-testid="stSidebar"] [role="radiogroup"] label input[type="radio"] { display:none !important; }
[data-testid="stSidebar"] [role="radiogroup"] label > div > div > div:first-child { display:none !important; }
[data-testid="stSidebar"] [role="radiogroup"] label > div > div { gap:0 !important; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:nth-child(2) {
  flex:1; min-width:0; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
  font-size:.86rem; font-weight:600; color:#4A3D31; line-height:1.35;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {
  font-size:.86rem; font-weight:600; color:#4A3D31; margin:0;
  overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  transform:none; border:0;
  background:linear-gradient(90deg, rgba(166,124,82,.20), rgba(166,124,82,.07) 68%, transparent);
  box-shadow:none;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::before {
  content:""; position:absolute; left:0; top:9px; bottom:9px; width:3px;
  border-radius:999px; background:#8C6E4A;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) div,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color:#2F261F !important; font-weight:700; }

/* ★演示主线 标记：右上角蓝色标签 */
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="04"]) > div:nth-child(2),
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="3"]) > div:nth-child(2) { padding-right:72px; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="04"])::after,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="3"])::after {
  content:"★ 演示主线";
  position:absolute; top:50%; right:10px; transform:translateY(-50%);
  background:transparent; color:#8C6E4A;
  font-size:.6rem; font-weight:800; letter-spacing:.02em;
  padding:0; border-radius:0; white-space:nowrap;
  box-shadow:none;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="04"]):has(input:checked)::after,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="3"]):has(input:checked)::after {
  background:transparent; color:#6E5033; box-shadow:none;
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
  border:1px solid rgba(255, 255, 255, 0.10); border-radius:var(--surface-radius); padding:.9rem 1rem; position:relative;
  box-sizing:border-box; min-height:8.2rem; height:100%;
  box-shadow:var(--surface-shadow);
  transition: all .22s var(--ease-out-quint); animation: dshFadeIn .5s var(--ease-out-quint) backwards;
}
.dsh-stat:hover { transform:translateY(-2px); box-shadow:0 6px 20px #00000024; }
.dsh-stat-value {
  font-size:clamp(1.15rem, 1.8vw, 1.6rem); font-weight:800; color:var(--text1);
  line-height:1.15; font-variant-numeric:tabular-nums; white-space:nowrap;
}
.dsh-stat-meta { display:flex; align-items:flex-start; gap:.38rem; margin-top:.48rem; }
.dsh-stat-icon {
  position:static; flex:0 0 1.4rem; width:1.4rem; height:1.4rem;
  display:grid; place-items:center; color:var(--warm); border-radius:6px;
  background:rgba(166,124,82,.12); border:1px solid rgba(201,177,143,.2);
}
.dsh-stat-icon svg { width:14px; height:14px; }
.dsh-stat-label { min-width:0; font-size:.78rem; color:var(--text2); line-height:1.45; }
.dsh-stat-delta { font-size:.7rem; color:#54B95A; margin-top:.28rem; font-weight:600; }
[data-testid="stHorizontalBlock"]:has(.dsh-stat) > [data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(.dsh-stat) > [data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"]:has(.dsh-stat) [data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.dsh-stat) [data-testid="stElementContainer"]:has(.dsh-stat),
[data-testid="stHorizontalBlock"]:has(.dsh-stat) [data-testid="stMarkdownContainer"]:has(.dsh-stat) {
  height:100%;
}

.dsh-info {
  background-color: var(--block); background-image:var(--noise);
  border:1px solid rgba(255, 255, 255, 0.10); border-radius:var(--surface-radius); padding:1.05rem 1.15rem;
  box-shadow:var(--surface-shadow); animation: dshFadeIn .5s var(--ease-out-quint) backwards;
}
.dsh-info-title { font-weight:800; color:var(--title); margin-bottom:.5rem; display:flex; gap:.5rem; align-items:center; }
.dsh-info-line { font-size:.85rem; color:var(--text2); line-height:1.7; margin-bottom:.2rem; }
.dsh-info-line b { color:var(--text1); }

/* ---------- 教师—智能体连续对话 ---------- */
.dsh-chat-list { display:flex; flex-direction:column; gap:.65rem; margin:.15rem 0 .8rem; }
.dsh-chat-row { display:flex; align-items:flex-start; gap:.55rem; }
.dsh-chat-row.is-teacher { justify-content:flex-end; }
.dsh-chat-avatar {
  flex:0 0 30px; width:30px; height:30px; display:grid; place-items:center;
  border-radius:8px; color:#8C6E4A; background:#FDFBF6;
  border:1px solid rgba(140,110,74,.24);
}
.dsh-chat-row.is-teacher .dsh-chat-avatar { order:2; color:#FDFBF6; background:#8C6E4A; }
.dsh-chat-bubble {
  max-width:min(82%, 880px); padding:.7rem .85rem; border-radius:10px;
  color:#F0F0F2; background:rgba(34,38,48,.92); border:1px solid rgba(255,255,255,.11);
  box-shadow:0 4px 14px rgba(35,27,20,.10); font-size:.84rem; line-height:1.72;
  overflow-wrap:anywhere; white-space:normal;
}
.dsh-chat-row.is-teacher .dsh-chat-bubble {
  color:#3A3129; background:#FDFBF6; border-color:rgba(140,110,74,.25);
}
.dsh-chat-row.is-agent .dsh-chat-bubble { max-height:520px; overflow-y:auto; }
.dsh-chat-role { display:block; margin-bottom:.22rem; font-size:.68rem; font-weight:800; letter-spacing:.08em; color:#C9B18F; }
.dsh-chat-row.is-teacher .dsh-chat-role { color:#8C6E4A; text-align:right; }
.dsh-chat-heading { margin:.55rem 0 .25rem; color:#fff; font-size:.92rem; font-weight:800; }
.dsh-chat-paragraph { margin:.16rem 0; }
.dsh-chat-point { display:grid; grid-template-columns:auto 1fr; gap:.38rem; margin:.18rem 0; }
.dsh-chat-point > span { color:#C9B18F; font-weight:800; }
.dsh-chat-rule { border:0; border-top:1px solid rgba(255,255,255,.12); margin:.55rem 0; }
.dsh-chat-space { height:.28rem; }

/* ---------- 首页 · 四大核心能力（等高响应式卡片） ---------- */
[data-testid="stHorizontalBlock"]:has(.dsh-agent-card) {
  align-items:stretch; gap:1rem;
}
[data-testid="stHorizontalBlock"]:has(.dsh-agent-card) > [data-testid="stColumn"] {
  display:flex; min-width:0;
}
[data-testid="stHorizontalBlock"]:has(.dsh-agent-card) > [data-testid="stColumn"] > div {
  width:100%; height:100%;
}
[data-testid="stHorizontalBlock"]:has(.dsh-agent-card) [data-testid="stVerticalBlock"] {
  height:100%; display:flex; flex-direction:column;
}
[data-testid="stHorizontalBlock"]:has(.dsh-agent-card) [data-testid="stElementContainer"]:has(.dsh-agent-card) {
  flex:1; display:flex;
}
[data-testid="stHorizontalBlock"]:has(.dsh-agent-card) [data-testid="stMarkdownContainer"]:has(.dsh-agent-card) {
  width:100%; height:100%;
}
.dsh-agent-card {
  --agent-accent:#A67C52;
  position:relative; overflow:hidden; box-sizing:border-box; height:680px; min-height:680px;
  display:flex; flex-direction:column; gap:0;
  padding:1.15rem 1.05rem 1rem;
  background:linear-gradient(160deg, rgba(50,54,64,.96), rgba(34,38,48,.90));
  border:1px solid rgba(255,255,255,.11); border-top:3px solid var(--agent-accent);
  border-radius:14px; box-shadow:var(--surface-shadow);
  transition:transform .22s var(--ease-out-quint), box-shadow .22s var(--ease-out-quint), border-color .22s var(--ease-out-quint);
  animation:dshFadeIn .5s var(--ease-out-quint) backwards;
}
.dsh-agent-card::after {
  content:""; position:absolute; width:150px; height:150px; right:-82px; top:-88px;
  border-radius:50%; background:color-mix(in srgb, var(--agent-accent) 14%, transparent);
  border:1px solid color-mix(in srgb, var(--agent-accent) 26%, transparent); pointer-events:none;
}
.dsh-agent-card:hover {
  transform:translateY(-3px); border-color:color-mix(in srgb, var(--agent-accent) 48%, rgba(255,255,255,.10));
  box-shadow:0 12px 30px rgba(35,27,20,.18);
}
.dsh-agent-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:.85rem; }
.dsh-agent-icon {
  width:38px; height:38px; display:flex; align-items:center; justify-content:center;
  color:var(--agent-accent); background:color-mix(in srgb, var(--agent-accent) 13%, transparent);
  border:1px solid color-mix(in srgb, var(--agent-accent) 32%, transparent); border-radius:9px;
}
.dsh-agent-index { color:var(--agent-accent); font-size:.68rem; font-weight:800; letter-spacing:.12em; }
.dsh-agent-title {
  min-height:3.3rem; color:#fff; font-size:1rem; font-weight:800; line-height:1.55;
  letter-spacing:-.01em; padding-bottom:.85rem; margin-bottom:.8rem;
  border-bottom:1px solid rgba(255,255,255,.10);
}
.dsh-agent-kicker {
  color:var(--agent-accent); font-size:.68rem; font-weight:800; letter-spacing:.12em;
  margin-bottom:.35rem;
}
.dsh-agent-list { display:flex; flex-direction:column; gap:.15rem; }
.dsh-agent-feature {
  position:relative; padding:.52rem 0 .52rem .85rem;
  color:#F0F0F2; font-size:.77rem; line-height:1.65;
  border-bottom:1px solid rgba(255,255,255,.075);
}
.dsh-agent-feature::before {
  content:""; position:absolute; left:0; top:1rem; width:5px; height:5px;
  border-radius:50%; background:var(--agent-accent); box-shadow:0 0 0 3px color-mix(in srgb, var(--agent-accent) 12%, transparent);
}
.dsh-agent-value {
  margin-top:auto; padding:.78rem .82rem; border-radius:9px;
  background:color-mix(in srgb, var(--agent-accent) 10%, rgba(255,255,255,.035));
  border:1px solid color-mix(in srgb, var(--agent-accent) 26%, rgba(255,255,255,.06));
}
.dsh-agent-value-label { color:var(--agent-accent); font-size:.67rem; font-weight:800; letter-spacing:.1em; margin-bottom:.3rem; }
.dsh-agent-value-text { color:#F0F0F2; font-size:.74rem; line-height:1.6; }
[data-testid="stHorizontalBlock"]:has(.dsh-agent-card) .stButton { margin-top:.25rem; }
[data-testid="stHorizontalBlock"]:has(.dsh-agent-card) .stButton > button {
  border-color:color-mix(in srgb, #A67C52 68%, transparent) !important;
}

@media (max-width: 1200px) {
  [data-testid="stHorizontalBlock"]:has(.dsh-agent-card) {
    display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:1rem;
  }
  [data-testid="stHorizontalBlock"]:has(.dsh-agent-card) > [data-testid="stColumn"] {
    width:100% !important; flex:none !important;
  }
}
@media (max-width: 700px) {
  [data-testid="stHorizontalBlock"]:has(.dsh-agent-card) { grid-template-columns:1fr; }
  .dsh-agent-card { height:auto; min-height:0; }
}

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

/* ---------- 工作台 · 三步横向等宽按钮 ---------- */
.st-key-ws_action_row [data-testid="stHorizontalBlock"] {
  gap:.42rem; align-items:stretch;
}
.st-key-ws_action_row [data-testid="stColumn"] { min-width:0; }
.st-key-ws_action_row [data-testid="stButton"] { width:100%; height:100%; }
.st-key-ws_action_row [data-testid="stButton"] > button {
  width:100%; height:10.5rem; min-height:10.5rem;
  padding:.7rem .2rem !important; display:flex; align-items:center; justify-content:center;
}
.st-key-ws_action_row [data-testid="stButton"] > button p {
  width:1.8em; margin:0; white-space:normal !important;
  line-height:1.55 !important; overflow-wrap:normal; word-break:normal;
  text-align:center; font-size:clamp(.72rem, .86vw, .86rem); letter-spacing:.045em;
}
.st-key-ws_action_row [data-testid="stColumn"]:first-child button p,
.st-key-ws_action_row [data-testid="stColumn"]:last-child button p {
  letter-spacing:.12em;
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
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="04"]) > div:nth-child(2),
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="3"]) > div:nth-child(2) { padding-right:24px; }
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="04"])::after,
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input[value="3"])::after {
    content:"★"; right:6px;
  }
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
  position:relative; overflow:hidden; box-sizing:border-box; text-align:center;
  background-color:rgba(248,244,236,.76);
  background-image:linear-gradient(145deg, rgba(255,255,255,.64), rgba(232,223,207,.42)), var(--noise);
  border:1px solid rgba(140,110,74,.18); border-radius:14px;
  padding:1.15rem .8rem 1.05rem; margin:.1rem 0 .35rem;
  box-shadow:0 8px 24px rgba(74,61,49,.09), inset 0 1px 0 rgba(255,255,255,.72);
}
.dsh-brand::before {
  content:""; position:absolute; left:34%; right:34%; top:0; height:3px;
  border-radius:0 0 4px 4px; background:linear-gradient(90deg, #C9B18F, #8C6E4A, #C9B18F);
}
.dsh-brand::after {
  content:""; position:absolute; width:110px; height:110px; right:-72px; bottom:-76px;
  border-radius:50%; border:1px solid rgba(140,110,74,.12);
  box-shadow:0 0 0 20px rgba(166,124,82,.025); pointer-events:none;
}
.dsh-brand-eyebrow {
  position:relative; z-index:1; color:#8C6E4A; font-size:.56rem; font-weight:800;
  letter-spacing:.14em; line-height:1.3; margin-bottom:.45rem;
}
.dsh-brand-title {
  position:relative; z-index:1; color:#30261E; font-size:1.04rem; font-weight:800;
  letter-spacing:.025em; line-height:1.35;
}
.dsh-brand-rule {
  position:relative; z-index:1; width:32px; height:1px; margin:.58rem auto .52rem;
  background:linear-gradient(90deg, transparent, rgba(140,110,74,.75), transparent);
}
.dsh-brand-sub {
  position:relative; z-index:1; display:flex; flex-direction:column; align-items:center; gap:.12rem;
  color:#58483A; font-size:.78rem; font-weight:700; line-height:1.5; letter-spacing:.015em;
}
.dsh-badge {
  display:inline-flex; align-items:center; gap:.4rem; padding:.28rem .75rem;
  border-radius:8px; font-size:.74rem; font-weight:700;
}
.dsh-foot { font-size:.7rem; color:#4A3D31; padding-top:.4rem; line-height:1.6; }
/* 本轮仅作用于准备、诊断、对话、科研区域，不覆盖侧栏或工作台。 */
.st-key-sim_prepare, .st-key-diag_layout, .st-key-diag_chat_panel,
.st-key-research_prepare, .st-key-research_reading { margin-bottom:24px; }
.st-key-sim_prepare [data-testid="stVerticalBlockBorderWrapper"],
.st-key-diag_chat_panel, .st-key-research_prepare { border-radius:12px; }
.st-key-sim_prepare button p, .st-key-diag_layout button p,
.st-key-diag_chat_panel button p, .st-key-research_prepare button p {
  word-break:normal; overflow-wrap:normal; writing-mode:horizontal-tb;
  line-height:1.5; font-size:15px;
}
.st-key-diag_report_reading .dsh-info,
.st-key-research_reading {
  color:#f0f0f2; background-color:rgba(34,38,48,.85); background-image:var(--noise);
  border-radius:12px; padding:24px; line-height:1.7; overflow-wrap:anywhere;
}
.st-key-research_reading [data-testid="stMarkdownContainer"] {
  max-width:78ch; margin-inline:auto; color:#f0f0f2; font-size:16px;
}
.st-key-research_reading [data-testid="stMarkdownContainer"] p,
.st-key-research_reading [data-testid="stMarkdownContainer"] li { color:#f0f0f2; line-height:1.7; }
.st-key-research_reading h1, .st-key-diag_report_reading h1 { color:#fff; font-size:26px; line-height:1.45; }
.st-key-research_reading h2, .st-key-diag_report_reading h2 { color:#fff; font-size:22px; line-height:1.5; }
.st-key-research_reading h3, .st-key-diag_report_reading h3 { color:#fff; font-size:18px; }
.st-key-diag_chat_panel .dsh-chat-list { gap:24px; }
.st-key-diag_chat_panel .dsh-chat-bubble { padding:16px 24px; font-size:16px; line-height:1.7; min-width:0; }
.st-key-diag_chat_panel .dsh-chat-row.is-agent .dsh-chat-bubble { max-height:none; overflow:visible; }
.st-key-diag_chat_panel .dsh-chat-heading { font-size:18px; }
.st-key-research_prepare [data-testid="stBaseButton-secondary"]:not(:disabled),
.st-key-sim_prepare [data-testid="stBaseButton-secondary"]:not(:disabled),
.st-key-diag_layout [data-testid="stBaseButton-secondary"]:not(:disabled),
.st-key-diag_chat_panel [data-testid="stBaseButton-secondary"]:not(:disabled) {
  color:#624B31 !important; border-color:#A68C69 !important; background:#FDFBF6 !important;
}
.st-key-sim_prepare .dsh-flow-status { color:#285B38 !important; }
.st-key-sim_feedback_layout .dsh-fbar-head { color:#3A3129; }
.st-key-sim_feedback_layout .dsh-flow-status { color:#624B31 !important; }
.st-key-persistence_panel [data-testid="stCaptionContainer"] p,
.st-key-persistence_panel .dsh-flow-status { color:#F0F0F2 !important; }
.st-key-persistence_panel summary,
.st-key-persistence_panel summary:hover,
.st-key-persistence_panel summary:focus { background:#343842 !important; color:#fff !important; }
.st-key-persistence_panel summary p { color:#fff !important; }
.st-key-persistence_panel [data-testid="stFileUploader"] button:not(:disabled),
.st-key-diag_layout [data-testid="stFileUploader"] button:not(:disabled),
.st-key-sim_prepare [data-testid="stFileUploader"] button:not(:disabled) { color:#624B31 !important; }
.dsh-research-hints { display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 16px; }
.dsh-research-hints span { background:#FDFBF6; border:1px solid #D9D0C0; color:#3A3129; padding:8px 12px; border-radius:8px; }
.st-key-diag_layout, .st-key-sim_feedback_layout { container-type:inline-size; }
@container (max-width: 760px) {
  .st-key-diag_layout > [data-testid="stHorizontalBlock"],
  .st-key-sim_feedback_layout > [data-testid="stHorizontalBlock"] { flex-direction:column; }
  .st-key-diag_layout > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  .st-key-sim_feedback_layout > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { width:100%; flex:1 1 100%; }
}
@media (max-width:900px) {
  .st-key-diag_layout [data-testid="stHorizontalBlock"],
  .st-key-diag_chat_panel [data-testid="stHorizontalBlock"],
  .st-key-research_prepare [data-testid="stHorizontalBlock"],
  .st-key-sim_feedback_layout [data-testid="stHorizontalBlock"] { flex-direction:column; }
  .st-key-diag_layout [data-testid="stColumn"], .st-key-diag_chat_panel [data-testid="stColumn"],
  .st-key-research_prepare [data-testid="stColumn"], .st-key-sim_feedback_layout [data-testid="stColumn"] { width:100%; flex:1 1 100%; min-width:0; }
  .st-key-research_reading, .st-key-diag_chat_panel .dsh-chat-bubble { padding:16px; }
}
</style>
"""


def inject_css():
    """注入全局美化样式。"""
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(WORKSPACE_CSS, unsafe_allow_html=True)
    st.markdown(DARK_WORKSPACE_CSS, unsafe_allow_html=True)


WORKSPACE_CSS = """<style>
.stApp [data-testid="stToolbar"] { display:none !important; }
[data-testid="stSidebar"] { width:280px !important; min-width:280px !important; }
[data-testid="stSidebar"] > div:first-child { width:280px !important; }
.st-key-workspace { container-type:inline-size; min-width:0; }
.st-key-workspace .dsh-page-title { color:#2F261F; font-size:28px; line-height:1.3; font-weight:700; margin:0; }
.st-key-workspace .dsh-page-description { color:#66594B; font-size:16px; line-height:1.7; margin:8px 0 24px; }
.st-key-page_layout > [data-testid="stHorizontalBlock"] { gap:28px; align-items:flex-start; flex-wrap:nowrap; }
.st-key-page_layout > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child { flex:0 0 168px; width:168px; min-width:0; }
.st-key-page_layout > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { flex:1 1 0; min-width:0; width:0; }
.st-key-page_layout [data-testid="stColumn"]:has(.st-key-function_nav) { flex:0 0 168px !important; width:168px !important; min-width:168px !important; }
.st-key-page_layout [data-testid="stColumn"]:has(.st-key-page_content) { flex:1 1 0 !important; width:0 !important; min-width:0 !important; }
.st-key-function_nav button { background:transparent !important; border:0 !important; border-left:2px solid transparent !important; border-radius:0 !important; box-shadow:none !important; min-height:42px; justify-content:flex-start; padding:8px 12px; color:#4A3D31 !important; }
.st-key-function_nav [data-testid*="stBaseButton"] { background:transparent !important; border:0 !important; border-left:2px solid transparent !important; border-radius:0 !important; box-shadow:none !important; }
.st-key-function_nav button p { color:inherit !important; white-space:normal !important; word-break:normal !important; overflow:visible; font-size:16px; text-align:left; }
.st-key-function_nav button[kind="primary"],
.st-key-function_nav [data-testid="stBaseButton-primary"] { border-left:2px solid #8C6E4A !important; background:rgba(140,110,74,.09) !important; color:#3A3129 !important; font-weight:700; }
.st-key-function_nav [data-testid="stVerticalBlock"] { gap:4px; }
.st-key-function_nav hr { border-color:#8C6E4A33; margin:12px 0; }
.st-key-page_content { background:rgba(34,38,48,.96); color:#F0F0F2; border-radius:8px; padding:28px; min-width:0; }
.st-key-page_content [data-testid="stVerticalBlock"], .st-key-page_content [data-testid="stColumn"] { min-width:0; }
.st-key-page_content p, .st-key-page_content li, .st-key-page_content label, .st-key-page_content [data-testid="stWidgetLabel"] p { font-size:16px; line-height:1.7; color:#F4F1EC; }
.st-key-page_content h1, .st-key-page_content h2, .st-key-page_content h3, .st-key-page_content .dsh-section { color:#FFF; }
.st-key-page_content .dsh-section { font-size:20px; border:0; padding:0; margin:16px 0; background:transparent; box-shadow:none; }
.st-key-page_content .dsh-section::before { display:none; }
.st-key-page_content .dsh-info, .st-key-page_content .dsh-stat, .st-key-page_content .dsh-bubble,
.st-key-page_content [data-testid="stVerticalBlockBorderWrapper"] { box-shadow:none; border:0; border-radius:0; background:transparent; }
.st-key-page_content .dsh-info { padding:14px 0; border-bottom:1px solid #FFFFFF20; }
.st-key-page_content .dsh-info-line, .st-key-page_content .dsh-info-title, .st-key-page_content .dsh-bubble-body { font-size:16px; line-height:1.7; }
.st-key-page_content .dsh-info-light { background:#FDFBF6; padding:16px; color:#3A3129; }
.st-key-page_content .dsh-info-light *, .st-key-page_content input, .st-key-page_content textarea,
.st-key-page_content [data-baseweb="select"] * { color:#3A3129; }
.st-key-page_content [data-testid="stBaseButton-primary"] { background:#8C6E4A !important; color:#FFF !important; border:0 !important; }
.st-key-page_content [data-testid="stBaseButton-primary"]:hover { background:#A67C52 !important; }
.st-key-page_content [data-testid="stBaseButton-primary"] p,
.st-key-page_content button[kind="primary"] p { color:#FFF !important; font-weight:700; }
.st-key-page_content [data-testid="stBaseButton-secondary"] { background:transparent !important; color:#F3EBDD !important; border:1px solid rgba(222,196,159,.72) !important; }
.st-key-page_content [data-testid="stBaseButton-secondary"]:hover { background:rgba(222,196,159,.10) !important; border-color:#DEC49F !important; }
.st-key-page_content [data-testid="stBaseButton-secondary"] p,
.st-key-page_content button[kind="secondary"] p { color:#F3EBDD !important; }
.st-key-page_content button:disabled { background:rgba(255,255,255,.045) !important; border:1px solid rgba(255,255,255,.12) !important; opacity:1 !important; }
.st-key-page_content button:disabled p { color:#AEB2BA !important; }
.st-key-page_content [data-testid="stFileUploader"] button p,
.st-key-page_content [data-testid="stFileUploaderDropzone"] button p { color:#3A3129 !important; }
.st-key-page_content button p { white-space:normal !important; word-break:normal !important; }
.st-key-page_content button { height:auto; min-height:42px; }
.st-key-page_content a { color:#DEC49F; }
.st-key-page_content [data-testid="stAlert"] p { color:inherit; }
.st-key-page_content .dsh-bubble { padding:16px 0; border-bottom:1px solid #FFFFFF20; }
.st-key-page_content .dsh-bubble-head { flex-wrap:wrap; }
.st-key-page_content .dsh-bubble-role { color:#F0F0F2; background:transparent !important; }
.st-key-page_content .dsh-info-title [style*="border-left"] { border-left:0 !important; padding-left:0 !important; }
.st-key-page_content [data-testid="stMarkdownContainer"] { overflow-wrap:anywhere; }
.st-key-page_content [data-testid="stMarkdownContainer"] table { display:block; max-width:100%; overflow-x:auto; }
.st-key-page_content iframe { max-width:100%; }
.st-key-page_content [class*="st-key-reading_"] { max-width:880px; margin-inline:auto; }
.st-key-page_content .dsh-empty { max-width:620px; padding:4px 0 18px; }
.st-key-page_content .dsh-empty-title { color:#FFF; font-size:20px; line-height:1.45; font-weight:700; margin-bottom:6px; }
.st-key-page_content .dsh-empty-note { color:#C9CDD5; font-size:15px; line-height:1.7; margin-bottom:14px; }
.st-key-page_content .dsh-save-status { color:#BFC3CB; font-size:13px; line-height:1.55; border-top:1px solid rgba(255,255,255,.10); margin-top:24px; padding-top:12px; }
.st-key-workspace .dsh-stat:hover, .st-key-workspace .dsh-info:hover, .st-key-workspace button:hover { transform:none; box-shadow:none; }
.st-key-workspace *, .st-key-workspace *::before, .st-key-workspace *::after { animation:none; }
.st-key-page_content [class*="st-key-view_body_"] { animation:workspaceFade 160ms cubic-bezier(.1,.9,.2,1); }
@keyframes workspaceFade { from {opacity:0;} to {opacity:1;} }
@media (max-width:640px) {
  .st-key-page_layout > [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:20px; }
  .st-key-page_layout > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
  .st-key-page_layout > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { flex:1 1 100%; width:100%; }
  .st-key-page_layout [data-testid="stColumn"]:has(.st-key-function_nav),
  .st-key-page_layout [data-testid="stColumn"]:has(.st-key-page_content) { flex:1 1 100% !important; width:100% !important; min-width:0 !important; }
  .st-key-function_nav > [data-testid="stVerticalBlock"] { flex-direction:row; flex-wrap:wrap; gap:4px 8px; }
  .st-key-function_nav > [data-testid="stVerticalBlock"] > div { width:auto; flex:0 1 auto; max-width:100%; }
  .st-key-function_nav [data-testid="stDivider"] { display:none; }
  .st-key-page_content { padding:20px; }
  .st-key-page_content [data-testid="stHorizontalBlock"] { flex-wrap:wrap; }
  .st-key-page_content [data-testid="stColumn"] { flex:1 1 100%; width:100%; min-width:0; }
}
@media (prefers-reduced-motion:reduce) {
  .st-key-workspace *, .st-key-workspace *::before, .st-key-workspace *::after { animation:none !important; transition:none !important; }
}
</style>"""


# DeepSeek 式双区工作台 + 冷蓝学术玻璃主题。作为最终覆盖层，
# 保留原有业务组件与页面结构，避免视觉改版破坏已有状态和交互。
DARK_WORKSPACE_CSS = """<style>
:root {
  --primary:#4D9FD1;
  --primary-hover:#65AED8;
  --primary-soft:#8CC4E3;
  --primary-deep:#397FA9;
  --accent:#C28B62;
  --good:#6FAF8D;
  --warn:#D2A65A;
  --danger:#CF7A7A;
  --bg:#0B1016;
  --sidebar:#0D141C;
  --workspace:rgba(18,25,34,.86);
  --glass:rgba(25,35,46,.66);
  --glass-strong:rgba(29,41,54,.84);
  --border:rgba(174,202,224,.13);
  --border-strong:rgba(174,202,224,.22);
  --text1:#EDF3F7;
  --text2:#C5D0D8;
  --text3:#9DACB9;
  --title:#F4F8FA;
  --ease-out-quint:cubic-bezier(.1,.9,.2,1);
  --noise:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='150' height='150'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.78' numOctaves='2' stitchTiles='stitchTiles'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.035'/%3E%3C/svg%3E");
}
html, body, .stApp { color-scheme:dark; background:#0B1016 !important; }
.stApp {
  background-image:
    radial-gradient(circle at 82% -12%, rgba(77,159,209,.10), transparent 34%),
    radial-gradient(circle at 12% 105%, rgba(194,139,98,.055), transparent 30%),
    var(--noise) !important;
  color:var(--text1);
}
[data-testid="stHeader"] { background:transparent !important; }
[data-testid="stToolbar"] { display:none !important; }
[data-testid="stMain"] { background:transparent !important; }
[data-testid="stMainBlockContainer"] {
  max-width:none !important;
  padding:16px 18px 24px !important;
}

/* 左侧七模块工作栏 */
[data-testid="stSidebar"] {
  width:260px !important; min-width:260px !important;
  background-color:rgba(13,20,28,.96) !important;
  background-image:linear-gradient(180deg,rgba(77,159,209,.045),transparent 24%),var(--noise) !important;
  border-right:1px solid rgba(174,202,224,.10) !important;
  box-shadow:18px 0 42px rgba(0,0,0,.16);
}
[data-testid="stSidebar"] > div:first-child { width:260px !important; padding:14px 12px 16px; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:7px; }
[data-testid="stSidebar"] hr { border-color:var(--border) !important; }
.dsh-brand {
  margin:0 0 14px !important; padding:16px 14px 18px !important;
  border-radius:18px !important; overflow:hidden;
  background:linear-gradient(145deg,rgba(77,159,209,.105),rgba(255,255,255,.025) 58%,rgba(194,139,98,.035)) !important;
  border:1px solid var(--border) !important;
  box-shadow:inset 0 1px rgba(255,255,255,.045),0 16px 32px rgba(0,0,0,.16) !important;
}
.dsh-brand::before { background:var(--noise) !important; opacity:.58 !important; }
.dsh-brand::after { background:linear-gradient(90deg,var(--primary),rgba(77,159,209,.08)) !important; }
.dsh-brand-eyebrow { color:#7FB7D7 !important; font-size:10px !important; letter-spacing:.16em !important; }
.dsh-brand-title { color:var(--title) !important; font-size:20px !important; letter-spacing:-.02em; }
.dsh-brand-rule { background:linear-gradient(90deg,var(--primary),transparent) !important; opacity:.7; }
.dsh-brand-sub { color:var(--text3) !important; font-size:12px !important; }
.dsh-nav-label { margin:1px 10px 4px; color:#718391; font-size:10px; font-weight:800; letter-spacing:.16em; }
.st-key-module_navigation button,
.st-key-sidebar_footer button {
  position:relative; min-height:42px !important; padding:8px 10px !important;
  justify-content:flex-start !important; gap:9px !important;
  color:var(--text3) !important; background:transparent !important;
  border:1px solid transparent !important; border-radius:11px !important;
  box-shadow:none !important; transition:background-color 180ms var(--ease-out-quint),color 180ms var(--ease-out-quint),border-color 180ms var(--ease-out-quint) !important;
}
.st-key-module_navigation button p,.st-key-sidebar_footer button p {
  color:inherit !important; font-size:13px !important; font-weight:590 !important;
  white-space:nowrap !important; overflow:hidden; text-overflow:ellipsis;
}
.st-key-module_navigation button svg,.st-key-sidebar_footer button svg { color:currentColor !important; width:18px; height:18px; flex:0 0 auto; }
.st-key-module_navigation button:hover,.st-key-sidebar_footer button:hover {
  color:var(--text1) !important; background:rgba(255,255,255,.045) !important; border-color:rgba(174,202,224,.08) !important;
}
.st-key-module_navigation [data-testid="stBaseButton-primary"],
.st-key-sidebar_footer [data-testid="stBaseButton-primary"] {
  color:#EAF5FB !important;
  background:linear-gradient(90deg,rgba(77,159,209,.17),rgba(77,159,209,.055)) !important;
  border-color:rgba(77,159,209,.20) !important;
}
.st-key-module_navigation [data-testid="stBaseButton-primary"]::before,
.st-key-sidebar_footer [data-testid="stBaseButton-primary"]::before {
  content:""; position:absolute; left:0; top:10px; bottom:10px; width:3px; border-radius:999px; background:var(--primary);
  box-shadow:0 0 14px rgba(77,159,209,.30);
}
.st-key-main_nav_04 button::after {
  content:"主线"; margin-left:auto; padding:2px 6px; border-radius:999px;
  color:#D8B89E; background:rgba(194,139,98,.10); border:1px solid rgba(194,139,98,.16); font-size:9px; font-weight:800;
}
.st-key-sidebar_footer { margin-top:auto !important; padding-top:12px; border-top:1px solid var(--border); }
.dsh-badge {
  display:flex !important; margin-top:7px !important; padding:7px 9px !important;
  color:var(--text3) !important; background:rgba(255,255,255,.025) !important;
  border:1px solid var(--border) !important; border-radius:10px !important; font-size:10px !important;
}
.dsh-foot { color:#687A88 !important; font-size:9px !important; line-height:1.55 !important; overflow-wrap:anywhere; }

/* 右侧大圆角工作区 */
.st-key-workspace { min-width:0; }
.st-key-workspace_panel {
  min-height:calc(100vh - 42px); padding:0 30px 24px !important; overflow:hidden;
  color:var(--text1); background:var(--workspace) !important;
  background-image:linear-gradient(145deg,rgba(77,159,209,.032),transparent 36%),var(--noise) !important;
  border:1px solid var(--border) !important; border-radius:24px !important;
  box-shadow:inset 0 1px rgba(255,255,255,.035),0 24px 70px rgba(0,0,0,.25) !important;
  backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
}
.st-key-workspace_header {
  position:sticky; top:0; z-index:20; margin:0 -30px 22px; padding:26px 30px 14px;
  background:linear-gradient(180deg,rgba(18,25,34,.98) 0%,rgba(18,25,34,.93) 76%,rgba(18,25,34,.72) 100%);
  border-bottom:1px solid rgba(174,202,224,.08); backdrop-filter:blur(22px); -webkit-backdrop-filter:blur(22px);
}
.st-key-workspace .dsh-page-title {
  margin:0 !important; color:var(--title) !important; font-size:clamp(25px,2.1vw,34px) !important;
  line-height:1.18 !important; font-weight:720 !important; letter-spacing:-.035em;
}
.st-key-workspace .dsh-page-description {
  max-width:760px; margin:7px 0 17px !important; color:var(--text3) !important;
  font-size:14px !important; line-height:1.65 !important;
}
.st-key-function_nav { overflow-x:auto; overflow-y:hidden; scrollbar-width:none; }
.st-key-function_nav::-webkit-scrollbar { display:none; }
.st-key-function_nav > [data-testid="stHorizontalBlock"] { display:flex !important; width:max-content !important; gap:7px !important; flex-wrap:nowrap !important; }
.st-key-function_nav [data-testid="stColumn"] { flex:0 0 auto !important; width:auto !important; min-width:0 !important; }
.st-key-function_nav button {
  min-height:34px !important; width:auto !important; padding:6px 13px !important; white-space:nowrap;
  color:var(--text3) !important; background:rgba(255,255,255,.018) !important;
  border:1px solid transparent !important; border-radius:999px !important; box-shadow:none !important;
  transition:background-color 180ms var(--ease-out-quint),color 180ms var(--ease-out-quint),border-color 180ms var(--ease-out-quint) !important;
}
.st-key-function_nav button p { color:inherit !important; font-size:12px !important; font-weight:650 !important; white-space:nowrap !important; }
.st-key-function_nav button:hover { color:var(--text1) !important; background:rgba(255,255,255,.05) !important; }
.st-key-function_nav [data-testid="stBaseButton-primary"] {
  color:#E9F5FB !important; background:rgba(77,159,209,.15) !important; border-color:rgba(77,159,209,.22) !important;
  box-shadow:inset 0 1px rgba(255,255,255,.035) !important;
}
.st-key-page_content { padding:0 0 8px !important; background:transparent !important; color:var(--text1) !important; border:0 !important; border-radius:0 !important; }
.st-key-page_content [class*="st-key-view_body_"] { animation:workspaceReveal 200ms var(--ease-out-quint); }
@keyframes workspaceReveal { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:none} }

/* 通用玻璃容器、信息与数据层级 */
.st-key-page_content [data-testid="stVerticalBlockBorderWrapper"],
.st-key-page_content .dsh-info,.st-key-page_content .dsh-stat,.st-key-page_content .dsh-bubble,
.st-key-page_content .dsh-agent-card,.st-key-page_content .dsh-gauge {
  color:var(--text1) !important; background:var(--glass) !important;
  background-image:linear-gradient(145deg,rgba(255,255,255,.025),transparent 48%) !important;
  border:1px solid var(--border) !important; border-radius:17px !important;
  box-shadow:inset 0 1px rgba(255,255,255,.035),0 12px 30px rgba(0,0,0,.12) !important;
  backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
}
.st-key-page_content [data-testid="stVerticalBlockBorderWrapper"] { padding:2px !important; }
.st-key-page_content .dsh-info,.st-key-page_content .dsh-stat,.st-key-page_content .dsh-bubble { padding:16px 18px !important; }
.st-key-page_content .dsh-info[style*="background-color"],.st-key-page_content .dsh-info-light {
  background:rgba(25,35,46,.74) !important; border-color:var(--border) !important; color:var(--text1) !important;
}
.st-key-page_content .dsh-info[style*="background-color"] *, .st-key-page_content .dsh-info-light * { color:var(--text2) !important; }
.st-key-page_content [style*="background:#FDFBF6"],.st-key-page_content [style*="background: #FDFBF6"] {
  color:var(--text2) !important; background:rgba(25,35,46,.74) !important; border-color:var(--border) !important;
}
.st-key-page_content .dsh-research-hints span {
  color:var(--text2) !important; background:rgba(25,35,46,.68) !important;
  border:1px solid var(--border) !important; border-radius:999px !important;
}
.st-key-page_content .dsh-info-title { color:var(--title) !important; font-size:14px !important; border:0 !important; }
.st-key-page_content .dsh-info-title span[style*="border-left"] { border-left:2px solid var(--primary) !important; padding-left:9px !important; }
.st-key-page_content .dsh-info-line,.st-key-page_content .dsh-bubble-body { color:var(--text2) !important; font-size:14px !important; line-height:1.72 !important; }
.st-key-page_content .dsh-stat-value { color:var(--title) !important; font-size:clamp(24px,2.2vw,34px) !important; letter-spacing:-.035em; }
.st-key-page_content .dsh-stat-label,.st-key-page_content .dsh-stat-meta { color:var(--text3) !important; }
.st-key-page_content .dsh-stat-icon { color:var(--primary) !important; background:rgba(77,159,209,.10) !important; }
.st-key-page_content .dsh-stat-delta { color:#86BEA1 !important; }
.st-key-page_content .dsh-section {
  margin:26px 0 13px !important; padding:0 !important; color:var(--title) !important;
  font-size:17px !important; font-weight:700 !important; letter-spacing:-.015em; background:transparent !important; border:0 !important;
}
.st-key-page_content .dsh-section::before { content:"" !important; display:inline-block !important; width:18px; height:2px; margin-right:9px; vertical-align:middle; border-radius:999px; background:linear-gradient(90deg,var(--primary),rgba(77,159,209,.16)); }
.st-key-page_content .dsh-section-note { margin-left:auto; color:var(--text3) !important; font-size:11px !important; font-weight:500 !important; }
.st-key-page_content .dsh-tag,.st-key-page_content [class*="dsh-tag"] {
  color:#B9D9EA !important; background:rgba(77,159,209,.09) !important;
  border:1px solid rgba(77,159,209,.16) !important; border-radius:999px !important;
}
.st-key-page_content .dsh-flow-status {
  color:var(--text2) !important; background:rgba(77,159,209,.075) !important;
  border:1px solid rgba(77,159,209,.14) !important; border-radius:12px !important;
}
.st-key-page_content .dsh-fbar-head { color:var(--text2) !important; }
.st-key-page_content .dsh-fbar-track { background:rgba(255,255,255,.07) !important; }
.st-key-page_content .dsh-fbar-fill { background:linear-gradient(90deg,var(--primary-deep),var(--primary)) !important; }
.st-key-page_content .dsh-bubble-role { color:#AFD5E9 !important; background:rgba(77,159,209,.10) !important; }
.st-key-page_content .dsh-chat-role { color:#A9CEE2 !important; }
.st-key-page_content .dsh-chat-bubble { color:var(--text2) !important; background:var(--glass) !important; border:1px solid var(--border) !important; border-radius:16px !important; }
.st-key-page_content .dsh-chat-row.is-teacher .dsh-chat-bubble { background:rgba(77,159,209,.105) !important; }
.st-key-page_content .dsh-chat-row.is-teacher .dsh-chat-avatar { color:#EAF5FB !important; background:#397FA9 !important; }
.st-key-page_content .dsh-step { border-radius:13px !important; background:rgba(255,255,255,.025) !important; border-color:var(--border) !important; }
.st-key-page_content .dsh-step-current { color:#DCEEF7 !important; background:rgba(77,159,209,.10) !important; border-color:rgba(77,159,209,.22) !important; }
.st-key-page_content .dsh-step-current .dsh-step-num { background:var(--primary-deep) !important; }
.st-key-page_content .dsh-step-done { color:#A9D2BB !important; background:rgba(111,175,141,.08) !important; border-color:rgba(111,175,141,.18) !important; }

/* Streamlit 原生控件 */
.st-key-page_content p,.st-key-page_content li,.st-key-page_content label,.st-key-page_content [data-testid="stWidgetLabel"] p { color:var(--text2) !important; }
.st-key-page_content h1,.st-key-page_content h2,.st-key-page_content h3,.st-key-page_content h4 { color:var(--title) !important; }
.st-key-page_content input,.st-key-page_content textarea,
.st-key-page_content [data-baseweb="select"] > div,.st-key-page_content [data-baseweb="base-input"] {
  color:var(--text1) !important; background:rgba(8,13,19,.46) !important; border-color:var(--border-strong) !important; border-radius:12px !important;
}
.st-key-page_content input::placeholder,.st-key-page_content textarea::placeholder { color:#70818E !important; }
.st-key-page_content [data-baseweb="select"] * { color:var(--text2) !important; }
.st-key-page_content [data-testid="stFileUploaderDropzone"] {
  background:rgba(8,13,19,.34) !important; border:1px dashed rgba(174,202,224,.20) !important; border-radius:16px !important;
}
.st-key-page_content button { min-height:40px; border-radius:11px !important; transition:background-color 180ms var(--ease-out-quint),border-color 180ms var(--ease-out-quint),color 180ms var(--ease-out-quint),transform 180ms var(--ease-out-quint) !important; }
.st-key-page_content [data-testid="stBaseButton-primary"] {
  color:#F4FAFD !important; background:linear-gradient(135deg,#397FA9,#4D9FD1) !important;
  border:1px solid rgba(140,196,227,.20) !important; box-shadow:0 8px 22px rgba(38,104,143,.18) !important;
}
.st-key-page_content [data-testid="stBaseButton-primary"]:hover { background:linear-gradient(135deg,#438CB6,#65AED8) !important; transform:translateY(-1px); }
.st-key-page_content [data-testid="stBaseButton-secondary"] {
  color:var(--text2) !important; background:rgba(255,255,255,.025) !important; border:1px solid var(--border-strong) !important;
}
.st-key-page_content [data-testid="stBaseButton-secondary"]:hover { color:var(--text1) !important; background:rgba(255,255,255,.055) !important; border-color:rgba(174,202,224,.28) !important; }
.st-key-page_content button p { color:inherit !important; }
.st-key-page_content [role="tablist"] { gap:7px; border-bottom:1px solid var(--border); }
.st-key-page_content [role="tab"] { color:var(--text3) !important; border-radius:10px 10px 0 0; }
.st-key-page_content [role="tab"][aria-selected="true"] { color:#C5E2F0 !important; background:rgba(77,159,209,.08) !important; }
.st-key-page_content [data-testid="stExpander"] { background:rgba(25,35,46,.48) !important; border:1px solid var(--border) !important; border-radius:14px !important; }
.st-key-page_content [data-testid="stAlert"] { border-radius:14px !important; border:1px solid var(--border) !important; background:rgba(25,35,46,.74) !important; }
.st-key-page_content table { color:var(--text2) !important; background:rgba(10,16,23,.28); border-radius:12px; }
.st-key-page_content th { color:var(--title) !important; background:rgba(77,159,209,.07) !important; }
.st-key-page_content td,.st-key-page_content th { border-color:var(--border) !important; }
.st-key-page_content a { color:#7FC0E2 !important; }
.st-key-page_content .dsh-empty { max-width:680px; padding:24px !important; background:rgba(25,35,46,.48); border:1px dashed var(--border-strong); border-radius:18px; }
.st-key-page_content .dsh-empty-title { color:var(--title) !important; }
.st-key-page_content .dsh-empty-note,.st-key-page_content .dsh-save-status { color:var(--text3) !important; }
.st-key-page_content .dsh-save-status { border-color:var(--border) !important; }
.st-key-research_reading,.st-key-diag_report_reading,.st-key-ws_editor_panel { max-width:980px; }

@media (max-width:900px) {
  [data-testid="stSidebar"] { width:236px !important; min-width:236px !important; }
  [data-testid="stSidebar"] > div:first-child { width:236px !important; }
  [data-testid="stMainBlockContainer"] { padding:10px !important; }
  .st-key-workspace_panel { padding:0 20px 20px !important; border-radius:20px !important; }
  .st-key-workspace_header { margin:0 -20px 18px; padding:22px 20px 12px; }
  .st-key-page_content [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; }
  .st-key-page_content [data-testid="stColumn"] { flex:1 1 min(100%,320px) !important; width:auto !important; min-width:0 !important; }
}
@media (max-width:640px) {
  [data-testid="stMainBlockContainer"] { padding:6px !important; }
  .st-key-workspace_panel { min-height:calc(100vh - 12px); padding:0 15px 16px !important; border-radius:17px !important; }
  .st-key-workspace_header { margin:0 -15px 16px; padding:18px 15px 10px; }
  .st-key-workspace .dsh-page-title { font-size:24px !important; }
  .st-key-workspace .dsh-page-description { font-size:12px !important; margin-bottom:13px !important; }
  .st-key-page_content [data-testid="stColumn"] { flex:1 1 100% !important; width:100% !important; }
  .st-key-page_content .dsh-info,.st-key-page_content .dsh-stat,.st-key-page_content .dsh-bubble { padding:14px !important; border-radius:15px !important; }
}
@media (prefers-reduced-motion:reduce) {
  .st-key-workspace *,[data-testid="stSidebar"] * { animation:none !important; transition:none !important; scroll-behavior:auto !important; }
}
</style>"""


def safe_text(value) -> str:
    """将用户输入或后端文本转为可安全插入 HTML 的纯文本。

    公共卡片仍支持页面传入可信的内置 HTML；只在数据来自用户或后端时
    由调用方显式使用本函数，避免破坏现有 ``<b>`` 等可信样式。
    """
    return html.escape("" if value is None else str(value), quote=True)


def draft_widget(kind, label, *, key, **kwargs):
    """业务键不绑定控件；离页后 Streamlit 仅清理 _ui_ 临时键。"""
    widget_key = "_ui_" + key
    if kind == "selectbox" and key in st.session_state and st.session_state[key] not in kwargs.get("options", []):
        st.session_state[key] = kwargs["options"][0]
        st.warning("已保存的选项不再可用，已恢复为当前默认选项；请核对后继续。")
    if key in st.session_state:
        st.session_state[widget_key] = st.session_state[key]
        kwargs.pop("value", None)
        kwargs.pop("index", None)

    def commit():
        st.session_state[key] = st.session_state[widget_key]
        if key in ("sim_transcript", "sim_teacher_input"):
            st.session_state["sim_transcribe_truncate"] = False
        if key == "ws_lesson_editor":
            st.session_state["ws_lesson"] = st.session_state[widget_key]

    value = getattr(st, kind)(label, key=widget_key, on_change=commit, **kwargs)
    st.session_state[key] = value
    return value


# =====================================================================
# 2. 会话状态集中初始化
# =====================================================================
def init_session_state():
    """集中初始化全部会话状态，统一守卫，避免跨页状态丢失。"""
    defaults = {
        "nav_radio": "01",                       # 当前导航页 id
        "shell_mode": "workspace",               # workspace=七模块；manage=全局内容管理
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
        "ws_agent_result": None,                 # 统一接口最近一次真实回答与来源
        # ---- 教学模拟实训 ----
        "sim_started": False,
        "sim_round": 0,                          # 互动轮次（驱动确定性数值变化）
        "flow": {"load": 46.0, "engage": 55.0, "confuse": 52.0, "flow": 58.0},
        "flow_status": "",                       # 自适应状态文案（后端 /status 可覆盖）
        "sim_feedback": None,                    # 后端返回的虚拟学生反馈（None=用内置话术池）
        "sim_signals": None,                     # 后端返回的多模态信号（None=本地计算）
        "sim_agent_result": None,                # 统一接口原始回答与可选来源
        "sim_teacher_input": "",                # 工作台传入的可编辑授课片段
        # ---- 智能诊断 ----
        "diag_ready": False,
        "diag_lesson_text": "",                 # 粘贴 / TXT / 跨页传入的课例正文
        "diag_result": None,                     # 本次生成的诊断结果缓存
        "diag_trace": None,                      # 与诊断结果同步的溯源子图
        "diag_input_snapshot": None,             # 生成报告时的输入快照
        "diag_chat_history": [],                 # 教师与诊断智能体的连续对话
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
    _init_persistent_state()


# 只保存业务输入与生成结果，不保存上传文件对象、后端状态或任何密钥。
PERSISTED_STATE_KEYS = (
    "nav_radio",
    "sim_theme", "sim_teacher_input", "sim_started", "sim_round", "flow",
    "flow_status", "sim_feedback", "sim_signals", "sim_agent_result",
    "diag_ready", "diag_lesson_text", "diag_result", "diag_trace",
    "diag_input_snapshot", "diag_input_source", "diag_generated_source",
    "diag_chat_history", "diag_chat_question", "sim_transcript",
    "ws_stage", "ws_lesson", "ws_lesson_editor", "ws_grade", "ws_topic",
    "ws_hours", "ws_itrs", "ws_stem", "ws_check_conclusion",
    "ws_design_context", "ws_agent_result",
    "research_ready", "research_pain", "research_result",
    "research_input_snapshot", "research_input_source", "research_generated_source",
    "research_imported_pain",
)


def _normalise_workspace_id(value) -> str | None:
    """仅接受规范 UUID，避免把任意路径片段拼入后端地址。"""
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def _workspace_id() -> str:
    current = _normalise_workspace_id(st.session_state.get("workspace_id"))
    if current:
        return current
    try:
        query_value = st.query_params.get("workspace")
    except (AttributeError, KeyError):
        query_value = None
    current = _normalise_workspace_id(query_value) or str(uuid.uuid4())
    st.session_state["workspace_id"] = current
    try:
        st.query_params["workspace"] = current
    except (AttributeError, KeyError):
        pass
    return current


def _persistence_url(workspace_id: str) -> str:
    return (
        f"{config.API_BASE.rstrip('/')}/"
        f"{config.PERSISTENCE_ENDPOINT.strip('/')}/{workspace_id}"
    )


def _persistence_headers():
    return {"X-Token": config.API_TOKEN} if config.API_TOKEN else None


def _persistent_payload() -> dict:
    state = {}
    for key in PERSISTED_STATE_KEYS:
        if key in st.session_state:
            state[key] = copy.deepcopy(st.session_state[key])
    return state


def _load_persistent_state(workspace_id: str):
    try:
        response = requests.get(
            _persistence_url(workspace_id),
            headers=_persistence_headers(),
            timeout=(3, 12),
        )
    except requests.exceptions.RequestException as exc:
        st.session_state["persistence_error"] = f"连接失败：{type(exc).__name__}"
        return None
    if not 200 <= response.status_code < 300:
        st.session_state["persistence_error"] = f"HTTP {response.status_code}"
        return None
    try:
        data = response.json()
    except ValueError:
        return None
    state = data.get("state") if isinstance(data, dict) else None
    try:
        return validate_state(state)
    except ValueError as exc:
        st.session_state["persistence_error"] = str(exc)
        return None


BACKUP_MAX_BYTES = 10 * 1024 * 1024
_DICT_KEYS = {"flow", "sim_agent_result", "diag_result", "diag_trace",
              "ws_design_context", "ws_agent_result", "research_result"}
_LIST_KEYS = {"sim_feedback", "sim_signals", "diag_chat_history", "ws_itrs", "ws_stem"}
_BOOL_KEYS = {"sim_started", "diag_ready", "research_ready"}
_INT_KEYS = {"sim_round", "ws_stage", "ws_hours"}


def validate_state(state):
    """外部档案只接受白名单、有限大小和业务类型；不执行任何导入内容。"""
    if not isinstance(state, dict):
        raise ValueError("档案必须包含 state 对象。")
    if len(json.dumps(state, ensure_ascii=False).encode("utf-8")) > BACKUP_MAX_BYTES:
        raise ValueError("档案超过 10 MB，请减少内容后重试。")
    cleaned = {}
    for key in PERSISTED_STATE_KEYS:
        if key not in state:
            continue
        value = state[key]
        expected = dict if key in _DICT_KEYS else list if key in _LIST_KEYS else bool if key in _BOOL_KEYS else int if key in _INT_KEYS else str
        nullable = key in (_DICT_KEYS - {"flow"}) or key in {"sim_feedback", "sim_signals", "ws_lesson", "diag_input_snapshot", "research_input_snapshot"}
        if value is None and nullable:
            cleaned[key] = [] if key == "diag_chat_history" else None
            continue
        if type(value) is not expected:
            raise ValueError(f"档案字段 {key} 类型不正确。")
        cleaned[key] = copy.deepcopy(value)
    for key, allowed in {"nav_radio": [x["id"] for x in config.NAV_ITEMS],
                         "ws_grade": ["小学", "初中", "高中"],
                         "kg_domain": ["all"] + config.KG_SUBDOMAIN_IDS}.items():
        if key in cleaned and cleaned[key] not in allowed:
            raise ValueError(f"档案字段 {key} 的选项无效。")
    for key, lower, upper in [("ws_stage", 0, 3), ("ws_hours", 1, 8), ("sim_round", 0, 1000000)]:
        if key in cleaned and not lower <= cleaned[key] <= upper:
            raise ValueError(f"档案字段 {key} 超出范围。")
    for key, limit in [("diag_lesson_text", 20000), ("research_pain", 2000), ("diag_chat_question", 2000)]:
        if len(cleaned.get(key, "")) > limit:
            raise ValueError(f"档案字段 {key} 超过 {limit:,} 字。")
    for message in cleaned.get("diag_chat_history", []):
        if not isinstance(message, dict) or message.get("role") not in {"teacher", "assistant"} or not isinstance(message.get("content"), str):
            raise ValueError("对话记录格式不正确。")
    flow = cleaned.get("flow")
    if flow is not None and any(type(flow.get(k)) not in (int, float) or not 0 <= flow[k] <= 100 for k in ("load", "engage", "confuse", "flow")):
        raise ValueError("心流指标格式不正确。")
    for key in ("sim_feedback", "sim_signals"):
        if any(not isinstance(x, dict) for x in cleaned.get(key) or []):
            raise ValueError(f"档案字段 {key} 格式不正确。")
    context = cleaned.get("ws_design_context")
    if context and (context.get("grade") not in {"小学", "初中", "高中"} or not isinstance(context.get("topic"), str) or type(context.get("hours")) is not int):
        raise ValueError("教案上下文格式不正确。")
    for key in ("ws_itrs", "ws_stem"):
        for row in cleaned.get(key) or []:
            if not isinstance(row, (list, tuple)) or len(row) != 3 or not isinstance(row[0], str) or type(row[1]) not in (int, float) or not 0 <= row[1] <= 100 or not isinstance(row[2], str):
                raise ValueError("素养评分格式不正确。")
            if len(row[2]) != 7 or not row[2].startswith("#") or any(c not in "0123456789abcdefABCDEF" for c in row[2][1:]):
                raise ValueError("素养配色不是有效的十六进制颜色。")
    trace = cleaned.get("diag_trace")
    if trace:
        if not isinstance(trace.get("nodes"), list) or not isinstance(trace.get("edges"), list):
            raise ValueError("溯源图谱格式不正确。")
        for node in trace["nodes"]:
            if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not isinstance(node.get("label"), str) or type(node.get("size", 18)) not in (int, float):
                raise ValueError("图谱节点格式不正确。")
        ids = {n["id"] for n in trace["nodes"]}
        for edge in trace["edges"]:
            if not isinstance(edge, (list, tuple)) or len(edge) < 2 or any(not isinstance(x, str) or x not in ids for x in edge[:2]):
                raise ValueError("图谱关系格式不正确。")
    result = cleaned.get("diag_result")
    if result and (not isinstance(result.get("problems"), list) or any(not isinstance(x, dict) for x in result["problems"]) or not isinstance(result.get("conclusion"), str)):
        raise ValueError("诊断报告格式不正确。")
    result = cleaned.get("research_result")
    if result and not (isinstance(result.get("answer"), str) or all(isinstance(result.get(k), str) for k in ("topic_md", "lit_md", "survey_md", "exp_md"))):
        raise ValueError("研究方案格式不正确。")
    if result and "answer" in result and not is_agent_response(result):
        raise ValueError("研究方案缺少真实回答来源标识或 agent_type。")
    return cleaned


def backup_bytes():
    return json.dumps({"format_version": 1, "exported_at": datetime.now(timezone.utc).isoformat(),
                       "state": _persistent_payload()}, ensure_ascii=False, indent=2).encode("utf-8")


def parse_backup(raw):
    if len(raw) > BACKUP_MAX_BYTES:
        raise ValueError("备份超过 10 MB。")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("备份不是有效的 UTF-8 JSON 文件。") from exc
    if not isinstance(data, dict) or type(data.get("format_version", 1)) is not int or data.get("format_version", 1) != 1:
        raise ValueError("不支持的备份版本。")
    state = data.get("state")
    if isinstance(state, dict) and set(state) - set(PERSISTED_STATE_KEYS):
        raise ValueError("备份含非业务字段，未导入。")
    return validate_state(state)


def _restore_persistent_state(state: dict):
    for key in PERSISTED_STATE_KEYS:
        if key not in state:
            continue
        value = copy.deepcopy(state[key])
        st.session_state[key] = value


def _save_persistent_state():
    if not st.session_state.get("persistence_available"):
        return False
    workspace_id = _workspace_id()
    payload = _persistent_payload()
    if len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")) > BACKUP_MAX_BYTES:
        st.session_state["persistence_status"] = "保存失败：档案超过 10 MB，请先下载备份并整理内容，不会静默截断。"
        return False
    fingerprint = hash(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
    if fingerprint == st.session_state.get("persistence_fingerprint"):
        return True
    if fingerprint == st.session_state.get("persistence_attempted"):
        return False
    st.session_state["persistence_attempted"] = fingerprint
    st.session_state["persistence_status"] = "待保存：正在同步已提交的内容。"
    try:
        response = requests.put(
            _persistence_url(workspace_id),
            json={"state": payload},
            headers=_persistence_headers(),
            timeout=(3, 12),
        )
    except requests.exceptions.RequestException:
        st.session_state["persistence_status"] = "保存暂时失败，本次会话内容仍然保留。"
        return False
    if not _confirmed_write(response):
        st.session_state["persistence_status"] = f"保存失败（HTTP {response.status_code} 或响应未确认）；请下载备份并重试。"
        return False
    st.session_state["persistence_fingerprint"] = fingerprint
    st.session_state["persistence_status"] = f"已保存 · {datetime.now().strftime('%H:%M:%S')}（最新内容）"
    return True


def _init_persistent_state():
    workspace_id = _workspace_id()
    if not st.session_state.get("persistence_checked"):
        st.session_state["persistence_checked"] = True
        if config.MOCK_MODE:
            st.session_state["persistence_available"] = False
            st.session_state["persistence_status"] = "Mock 模式：当前会话自动保留。"
            return
        restored = _load_persistent_state(workspace_id)
        if restored is None:
            st.session_state["persistence_available"] = False
            st.session_state["persistence_status"] = "长期保存接口待后端同步；当前会话内容仍会保留。"
            return
        _restore_persistent_state(restored)
        st.session_state["persistence_available"] = True
        st.session_state["persistence_status"] = (
            "已恢复上次保存的内容。" if restored else "长期档案已连接，将自动保存新内容。"
        )
        st.session_state["persistence_fingerprint"] = hash(
            json.dumps(_persistent_payload(), ensure_ascii=False, sort_keys=True, default=str)
        )
        return



def _confirmed_write(response):
    if not 200 <= response.status_code < 300:
        return False
    if response.status_code == 204:
        return True
    try:
        data = response.json()
        return isinstance(data, dict) and data.get("success") is True
    except ValueError:
        return False


def _reset_business():
    for key in PERSISTED_STATE_KEYS:
        st.session_state.pop(key, None)
    for key in list(st.session_state):
        if key.startswith(("_ui_", "diag_upload", "sim_audio", "sim_transcribe", "research_pending", "diag_chat_", "backup_", "request_error_", "fallback_", "preview_")):
            st.session_state.pop(key, None)
    st.session_state["persistence_fingerprint"] = None
    st.session_state.pop("persistence_attempted", None)
    st.session_state.pop("persistence_remote_pending", None)
    st.session_state.pop("persistence_confirm_clear", None)


def _clear_saved_content(local_only=False):
    if not local_only:
        if config.MOCK_MODE:
            st.session_state["persistence_status"] = "Mock 模式无法删除远端档案，可仅清空本次会话。"
            return
        try:
            response = requests.delete(_persistence_url(_workspace_id()), headers=_persistence_headers(), timeout=(3, 12))
            if not _confirmed_write(response):
                st.session_state["persistence_status"] = f"删除失败（HTTP {response.status_code} 或响应未确认），内容未清空。"
                return
        except requests.exceptions.RequestException:
            st.session_state["persistence_status"] = "删除失败：网络不可用，内容未清空。"
            return
    _reset_business()
    # 脱离旧档案，防止仅清空本地时把空状态写回旧远端，或删除后重新创建它。
    st.session_state["workspace_id"] = str(uuid.uuid4())
    st.query_params["workspace"] = st.session_state["workspace_id"]
    st.session_state["persistence_available"] = False
    st.session_state["persistence_checked"] = True
    st.session_state["persistence_status"] = "已清空本次会话，旧远端档案未修改。" if local_only else "已确认删除远端档案并清空本次会话。"


def _retry_persistence():
    st.session_state.pop("persistence_attempted", None)
    if config.MOCK_MODE:
        st.session_state["persistence_status"] = "Mock 模式仅保留当前会话，请下载备份。"
        return
    remote = _load_persistent_state(_workspace_id())
    if remote is None:
        st.session_state["persistence_status"] = "读取失败，未覆盖远端：" + st.session_state.get("persistence_error", "响应格式异常")
        st.session_state["persistence_available"] = False
        return
    if remote:
        st.session_state["persistence_remote_pending"] = remote
        st.session_state["persistence_available"] = False
        st.session_state["persistence_status"] = "已找到远端内容，请选择恢复或用本次内容覆盖。"
    else:
        st.session_state["persistence_available"] = True
        st.session_state["persistence_fingerprint"] = None
        _save_persistent_state()


def _resolve_remote(restore):
    remote = st.session_state.pop("persistence_remote_pending", {})
    if restore:
        _reset_business()
        _restore_persistent_state(remote)
    st.session_state["persistence_available"] = True
    st.session_state["persistence_fingerprint"] = None
    st.session_state.pop("persistence_attempted", None)
    _save_persistent_state()


def _import_backup():
    try:
        uploaded = st.session_state.get("backup_file")
        if uploaded is None:
            return
        state = parse_backup(uploaded["data"])
        _reset_business()
        _restore_persistent_state(state)
        st.session_state["persistence_status"] = "备份已导入当前档案；待同步远端。" if st.session_state.get("persistence_available") else "备份已恢复；仅当前会话保留，长期保存尚未连接。"
    except (ValueError, RecursionError) as exc:
        st.session_state["persistence_status"] = f"导入失败，原内容未改变：{exc}"


def persistence_controls():
    """全局档案状态和手动清除入口；保持侧边栏结构不变。"""
    workspace_id = _workspace_id()
    with st.container(key="persistence_panel"):
        section_title("内容管理", "管理所有页面的同一份档案")
        status = safe_text(st.session_state.get("persistence_status", "当前会话自动保留。"))
        st.markdown(
            f'<div class="dsh-flow-status">{icon("bookmark", 14)} {status}</div>',
            unsafe_allow_html=True,
        )
        if st.session_state.get("persistence_error"):
            st.caption("长期保存连接详情：" + st.session_state["persistence_error"])
        st.caption("只有确认远端保存成功后，才能用同一完整网址恢复。尚未提交的输入不保证已保存，请失焦或按 Ctrl+Enter 提交。")
        st.caption("完整 workspace 链接可能允许访问档案，请勿公开分享含真实课堂资料的链接。原始音频与文档不进入档案。")
        st.code(workspace_id, language=None)
        st.button("重试连接与保存", on_click=_retry_persistence, key="persistence_retry")
        if st.session_state.get("persistence_remote_pending") is not None:
            st.warning("远端已有档案。请先下载本次备份，再选择要保留的内容。")
            st.button("恢复远端内容（覆盖本次）", on_click=_resolve_remote, args=(True,))
            st.button("保留本次内容（覆盖远端）", on_click=_resolve_remote, args=(False,))
        st.download_button("下载完整 JSON 备份", backup_bytes(), file_name="stem-workspace.json", mime="application/json", key="backup_download")
        st.file_uploader("导入 JSON 备份（最多 10 MB）", type=["json"], max_upload_size=10, key="backup_upload", on_change=_backup_changed)
        if st.session_state.get("backup_file"):
            st.caption("待导入：" + st.session_state["backup_file"]["name"])
        import_confirmed = draft_widget("checkbox", "我确认用备份替换当前输入、结果和对话", key="backup_confirm")
        st.button("确认导入备份", disabled=not (import_confirmed and st.session_state.get("backup_file")), on_click=_import_backup)
        st.divider()
        confirmed = draft_widget("checkbox", "我确认清除内容，已自行下载需要的备份", key="persistence_confirm_clear")
        st.button(
            "清除全部已保存内容",
            type="secondary",
            width="stretch",
            on_click=_clear_saved_content,
            key="persistence_clear_all",
            disabled=not confirmed,
        )
        st.button("仅清空本次会话（保留旧远端档案）", on_click=_clear_saved_content, args=(True,), disabled=not confirmed, key="persistence_clear_local")


# =====================================================================
# 3. 统一样式组件
# =====================================================================
def page_header(icon_name, title, subtitle, tag=None):
    st.markdown(f'<h1 class="dsh-page-title">{safe_text(title)}</h1>'
                f'<p class="dsh-page-description">{safe_text(subtitle)}</p>', unsafe_allow_html=True)


def current_view(pid):
    key = "view_" + pid
    choices = [item[0] for item in config.PAGE_VIEWS[pid]]
    if st.session_state.get(key) not in choices:
        st.session_state[key] = choices[0]
    return st.session_state[key]


def set_view(pid, view):
    if view not in dict(config.PAGE_VIEWS[pid]):
        raise ValueError("未知功能目录")
    if current_view(pid) != view:
        st.session_state.pop("preview_" + pid, None)
    st.session_state["view_" + pid] = view


def page_frame(pid):
    item = next(item for item in config.NAV_ITEMS if item["id"] == pid)
    view = current_view(pid)
    with st.container(key="workspace_panel"):
        with st.container(key="workspace_header"):
            page_header(item["icon"], item["name"], config.PAGE_DESCRIPTIONS[pid])
            with st.container(key="function_nav"):
                nav_columns = st.columns(len(config.PAGE_VIEWS[pid]), gap="small")
                for column, (ident, label) in zip(nav_columns, config.PAGE_VIEWS[pid]):
                    with column:
                        st.button(
                            label,
                            key=f"view_button_{pid}_{ident}",
                            width="stretch",
                            type="primary" if view == ident else "secondary",
                            on_click=set_view,
                            args=(pid, ident),
                        )
        content = st.container(key="page_content")
    return view, content


def management_frame():
    """在与业务页一致的右侧工作区中渲染全局内容管理。"""
    with st.container(key="workspace_panel"):
        with st.container(key="workspace_header"):
            page_header("bookmark", "内容管理", "管理当前工作区的长期保存、备份与恢复。")
        content = st.container(key="page_content")
    return content


def empty_view(pid, text, target=None):
    st.markdown(
        f'<div class="dsh-empty"><div class="dsh-empty-title">{safe_text(text)}</div>'
        '<div class="dsh-empty-note">完成输入后，结果会保留在当前会话中。</div></div>',
        unsafe_allow_html=True,
    )
    st.button("前往输入", type="primary", key=f"empty_{pid}_{current_view(pid)}",
              on_click=set_view, args=(pid, target or config.PAGE_VIEWS[pid][0][0]))


def accept_result(pid, result, origin, target):
    """在调用点记录本次请求结果，避免全局后端状态被其他页面请求覆盖。"""
    if config.MOCK_MODE or is_agent_response(result):
        for prefix in ("request_error_", "fallback_", "preview_"):
            st.session_state.pop(prefix + pid, None)
        return True
    status = st.session_state.get("backend_status") or ("down", "无有效回答")
    st.session_state["request_error_" + pid] = f"请求失败：{status[1]}。输入及已有结果已保留，可重试。"
    st.session_state["fallback_" + pid] = {
        "result": copy.deepcopy(result), "origin": origin, "target": target,
    }
    return False


def _open_mock_preview(pid):
    fallback = st.session_state["fallback_" + pid]
    set_view(pid, fallback["target"])
    st.session_state["preview_" + pid] = True


def _close_mock_preview(pid):
    fallback = st.session_state["fallback_" + pid]
    st.session_state.pop("preview_" + pid, None)
    set_view(pid, fallback["origin"])


def request_notice(pid):
    error = st.session_state.get("request_error_" + pid)
    if error:
        st.error(error)
        if st.session_state.get("fallback_" + pid) and not st.session_state.get("preview_" + pid):
            st.button("查看 Mock 示例（只读）", key="mock_preview_" + pid,
                      on_click=_open_mock_preview, args=(pid,))


def render_mock_preview(pid):
    """只读渲染兜底；不调用业务渲染器，也不写入报告、教案或流程阶段。"""
    if not st.session_state.get("preview_" + pid):
        return False
    st.warning("Mock 示例 · 非真实请求结果 · 仅供查看，未写入当前工作流程。")
    result = st.session_state["fallback_" + pid]["result"] or {}
    if isinstance(result, dict):
        for key in ("lesson_md", "topic_md", "lit_md", "survey_md", "exp_md", "conclusion", "status"):
            if result.get(key):
                st.markdown(str(result[key]))
        for problem in result.get("problems", []):
            st.subheader(problem.get("title", "示例问题"))
            for label, key in (("证据", "evidence"), ("归因", "cause"), ("建议", "suggest")):
                st.write(f"{label}：{problem.get(key, '')}")
        for feedback in result.get("feedback", []):
            st.write(f"{feedback.get('name', '示例学生')}：{feedback.get('text', '')}")
        if result.get("flow"):
            flow_dashboard(result["flow"], "Mock 示例指标，非实际测量")
    st.button("返回继续操作", key="mock_return_" + pid, on_click=_close_mock_preview, args=(pid,))
    return True


def save_status():
    _save_persistent_state()
    message = st.session_state.get("persistence_status", "当前会话自动保留。")
    if message.startswith("长期保存接口待后端同步"):
        message = "当前内容保留在本次会话；长期保存待后端接通。"
    st.markdown(f'<div class="dsh-save-status">{safe_text(message)}</div>', unsafe_allow_html=True)


def finish_action(pid, target):
    set_view(pid, target)
    _save_persistent_state()
    st.rerun()


def _backup_changed():
    uploaded = st.session_state.get("backup_upload")
    st.session_state["backup_confirm"] = False
    st.session_state["backup_file"] = ({"name": uploaded.name, "data": uploaded.getvalue()}
                                        if uploaded is not None else None)


def section_title(text: str, note: str = ""):
    """左侧暖棕竖线 + 小标题的区块分隔样式。"""
    note_html = f'<span class="dsh-section-note">{note}</span>' if note else ""
    st.markdown(f'<div class="dsh-section"><span>{text}</span>{note_html}</div>', unsafe_allow_html=True)


def stat_card(value, label, delta=None, icon=None, icon_name=None):
    """统一样式统计卡片：数值独占首行，图标与标签组合居下，避免窄卡片内容重叠。"""
    name = icon_name or icon or "activity"
    d = f'<div class="dsh-stat-delta">{delta}</div>' if delta else ""
    st.markdown(
        f"""<div class="dsh-stat"><div class="dsh-stat-value">{value}</div>
        <div class="dsh-stat-meta"><div class="dsh-stat-icon">{_ICON_FN(name, 18)}</div>
        <div class="dsh-stat-label">{label}</div></div>{d}</div>""",
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
    elif status[0] == "bad_request":
        html = ('<span class="dsh-badge" style="background:#ffffffd9; color:#D13438; border:1px solid #00000014;">'
                '前端请求格式异常 · 已回退 Mock</span>')
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
    统一接口只返回文本 answer；心流数值由前端演示模型生成，真实回答用于课堂建议。
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
                color={"color": "#607786", "highlight": "#65AED8", "hover": "#4D9FD1"},
                font={"size": 10, "color": "#9DACB9", "face": "Microsoft YaHei", "strokeWidth": 2},
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
        highlightColor={"border": "#65AED8", "background": "rgba(77,159,209,0.22)"},
        hoverColor={"border": "#4D9FD1", "background": "rgba(77,159,209,0.16)"},
        nodes={"font": {"color": "#EDF3F7", "size": 13, "face": "Microsoft YaHei"}, "borderWidth": 1, "shadow": False},
        edges={"color": {"color": "#607786", "highlight": "#65AED8"}, "smooth": {"enabled": True, "type": "dynamic"}, "selectionWidth": 2},
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


def node_detail_panel(nodes, edges, key="kg_node_detail"):
    """通过下拉选择器实现“节点点击查看详情”的等价交互。"""
    if not nodes:
        return
    options = [f'{n["label"]} · {n.get("type", "")}' for n in nodes]
    choice = draft_widget("selectbox", "选择节点查看详情（等价于画布点击）", options=options, index=0, key=key)
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


def _clean_agent_sources(value):
    """兼容未来的 sources / graph_sources；仅接收数组，不猜测内部结构。"""
    return copy.deepcopy(value) if isinstance(value, list) else []


def _clean_agent_chat_response(data: dict, payload: dict):
    """清洗 POST /api/agent-chat 的稳定返回契约。"""
    answer = data.get("answer")
    actual_type = data.get("agent_type")
    expected_type = payload.get("agent_type")
    issues = []
    if not _valid_text(answer):
        issues.append("answer")
    if not _valid_text(actual_type):
        issues.append("agent_type")
    elif actual_type != expected_type:
        issues.append("agent_type mismatch")
    if issues:
        return None, issues
    return {
        "answer": answer.strip(),
        "agent_type": actual_type,
        "sources": _clean_agent_sources(data.get("sources")),
        "graph_sources": _clean_agent_sources(data.get("graph_sources")),
        "_real_response": True,
    }, []


def api_gate(endpoint: str, payload=None, mock_result=None, method: str = "POST"):
    """统一智能体接口网关（契约见《STEM教师教育智能体前端接口说明.docx》）。

    MOCK_MODE=True  → 直接返回预置 Mock 数据（mock_result），不发起网络请求；
    MOCK_MODE=False → POST config.API_BASE + /api/agent-chat：
                      请求仅发送 question + agent_type；
                      成功返回 answer + agent_type，并兼容可选来源字段；
                      失败 / 超时 / 契约异常时整体回退 mock_result。

    可选 config.API_TOKEN 通过 X-Token 请求头发送，不写入状态详情或日志。
    """
    if config.MOCK_MODE:
        _set_backend_status("mock", "内置示例")
        return _mock_copy(mock_result)

    payload = payload if isinstance(payload, dict) else {}
    question = payload.get("question")
    agent_type = payload.get("agent_type")
    allowed_types = set(config.AGENT_TYPES.values())
    if not _valid_text(question) or agent_type not in allowed_types:
        _set_backend_status("bad_request", "前端请求格式错误")
        return _mock_copy(mock_result)

    request_body = {
        "question": question.strip(),
        "agent_type": agent_type,
    }
    url = f"{config.API_BASE.rstrip('/')}/{endpoint.lstrip('/')}"
    request_kwargs = {"json": request_body, "timeout": config.API_TIMEOUT}
    if config.API_TOKEN:
        request_kwargs["headers"] = {"X-Token": config.API_TOKEN}
    try:
        with st.spinner("智能体正在检索知识并生成回答……"):
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

    cleaned, issues = _clean_agent_chat_response(data, request_body)
    if issues:
        summary = ", ".join(dict.fromkeys(issues))
        if len(summary) > 100:
            summary = summary[:97] + "..."
        _set_backend_status("bad_response", f"HTTP {resp.status_code} · 契约字段异常 {summary}")
        return _mock_copy(mock_result)
    _set_backend_status("ok", f"HTTP {resp.status_code}")
    return cleaned


def transcribe_audio(filename: str, audio_bytes: bytes, content_type: str = "audio/wav"):
    """调用独立音频转写接口，返回纯文本；失败时返回 ``None``。

    后端稳定契约：POST multipart/form-data /api/transcribe，文件字段 ``file``，
    响应为 ``{"text": "..."}``。该能力与四智能体 JSON 接口相互独立。
    """
    if not audio_bytes:
        st.session_state["sim_transcribe_notice"] = "失败：音频文件为空。"
        return None
    if config.MOCK_MODE:
        st.session_state["sim_transcribe_notice"] = "成功（Mock 示例）：以下不是实际音频识别结果。"
        return "同学们，今天我们从校园碳足迹出发，讨论如何用跨学科知识设计减排方案。"

    url = f"{config.API_BASE.rstrip('/')}/{config.TRANSCRIBE_ENDPOINT.lstrip('/')}"
    headers = {"X-Token": config.API_TOKEN} if config.API_TOKEN else None
    try:
        with st.spinner("正在识别音频并转换为文本……"):
            resp = requests.post(
                url,
                files={"file": (filename or "audio.wav", audio_bytes, content_type or "audio/wav")},
                headers=headers,
                timeout=config.API_TIMEOUT,
            )
    except requests.exceptions.Timeout:
        st.session_state["sim_transcribe_notice"] = "转写失败：请求超时，请重试或手动输入。"
        return None
    except requests.exceptions.RequestException:
        st.session_state["sim_transcribe_notice"] = "转写失败：网络连接不可用，请重试或手动输入。"
        return None
    if not 200 <= resp.status_code < 300:
        st.session_state["sim_transcribe_notice"] = f"转写失败：HTTP {resp.status_code}，原授课文字未改变。"
        return None
    try:
        data = resp.json()
    except ValueError:
        st.session_state["sim_transcribe_notice"] = "转写失败：接口未返回 JSON。"
        return None
    text = data.get("text") if isinstance(data, dict) else None
    st.session_state["sim_transcribe_notice"] = "成功：请检查转写结果，再选择替换或追加。" if isinstance(text, str) and text.strip() else "转写失败：接口未返回有效 text。"
    return text.strip() if isinstance(text, str) and text.strip() else None


def is_agent_response(result) -> bool:
    """判断是否为统一真实后端返回，便于页面适配文本型 answer。"""
    return (
        isinstance(result, dict)
        and result.get("_real_response") is True
        and _valid_text(result.get("answer"))
        and isinstance(result.get("agent_type"), str)
        and result.get("agent_type") in set(config.AGENT_TYPES.values())
    )


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
