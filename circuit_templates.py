#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邱关源《电路》参数化拓扑模板库 + SymPy 符号求解器 + 国标/教材风格 SVG/PNG 渲染器
"""

import os
from typing import Dict, Any, List
import sympy as sp
import cairosvg

FONT_FAMILY = "'WenQuanYi Micro Hei', 'Noto Sans CJK SC', sans-serif"


def sub(base: str, subscript: str, tail: str = "") -> str:
    """将数字下标转为文泉驿原生支持的 Unicode 数字下标（₁₂₃），英文下标直接拼接，避免 cairosvg 中 tspan 与 text-anchor 冲突重叠"""
    digit_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    sub_clean = subscript.translate(digit_map)
    return f"{base}{sub_clean}{tail}"


def svg_header(width: int = 780, height: int = 380) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <marker id="arrow-ctrl" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#dc2626"/>
    </marker>
    <marker id="arrow-curr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0f172a"/>
    </marker>
    <marker id="arrow-sw" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2563eb"/>
    </marker>
  </defs>
  <style>
    .bg {{ fill: #ffffff; }}
    .panel {{ fill: #f8fafc; stroke: #94a3b8; stroke-width: 1.6; stroke-dasharray: 6 4; rx: 8; }}
    .wire {{ stroke: #0f172a; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
    .comp {{ stroke: #0f172a; stroke-width: 2.2; fill: #ffffff; stroke-linejoin: round; }}
    .comp-dep {{ stroke: #b91c1c; stroke-width: 2.2; fill: #fef2f2; stroke-linejoin: round; }}
    .node {{ fill: #0f172a; }}
    .port {{ fill: #ffffff; stroke: #0f172a; stroke-width: 2.2; }}
    .label {{ font-family: {FONT_FAMILY}; font-size: 15px; fill: #0f172a; font-weight: 600; }}
    .sublabel {{ font-family: {FONT_FAMILY}; font-size: 13px; fill: #334155; font-weight: 500; }}
    .ctrl-label {{ font-family: {FONT_FAMILY}; font-size: 15px; fill: #dc2626; font-weight: 700; }}
    .sw-label {{ font-family: {FONT_FAMILY}; font-size: 13px; fill: #2563eb; font-weight: 600; }}
    .title {{ font-family: {FONT_FAMILY}; font-size: 16px; fill: #0f172a; font-weight: 700; }}
  </style>
  <rect width="100%" height="100%" class="bg"/>
"""


def draw_resistor_h(cx: int, cy: int, label_top: str = "", label_bottom: str = "", w: int = 48, h: int = 18) -> str:
    x0 = cx - w // 2
    y0 = cy - h // 2
    out = f'  <rect x="{x0}" y="{y0}" width="{w}" height="{h}" class="comp"/>\n'
    if label_top:
        out += f'  <text x="{cx}" y="{y0 - 9}" text-anchor="middle" class="label">{label_top}</text>\n'
    if label_bottom:
        out += f'  <text x="{cx}" y="{y0 + h + 18}" text-anchor="middle" class="sublabel">{label_bottom}</text>\n'
    return out


def draw_resistor_v(cx: int, cy: int, label_right: str = "", label_left: str = "", w: int = 18, h: int = 48) -> str:
    x0 = cx - w // 2
    y0 = cy - h // 2
    out = f'  <rect x="{x0}" y="{y0}" width="{w}" height="{h}" class="comp"/>\n'
    if label_right:
        out += f'  <text x="{x0 + w + 8}" y="{cy + 5}" text-anchor="start" class="label">{label_right}</text>\n'
    if label_left:
        out += f'  <text x="{x0 - 8}" y="{cy + 5}" text-anchor="end" class="label">{label_left}</text>\n'
    return out


def draw_vsource_v(cx: int, cy: int, label_left: str = "", r: int = 22, plus_top: bool = True) -> str:
    out = f'  <circle cx="{cx}" cy="{cy}" r="{r}" class="comp"/>\n'
    py_plus = cy - 6 if plus_top else cy + 14
    py_minus = cy + 14 if plus_top else cy - 6
    out += f'  <text x="{cx}" y="{py_plus}" text-anchor="middle" class="label">+</text>\n'
    out += f'  <text x="{cx}" y="{py_minus}" text-anchor="middle" class="label">−</text>\n'
    if label_left:
        out += f'  <text x="{cx - r - 10}" y="{cy + 5}" text-anchor="end" class="label">{label_left}</text>\n'
    return out


def draw_isource_v(cx: int, cy: int, label_left: str = "", label_right: str = "", r: int = 22, arrow_up: bool = True) -> str:
    out = f'  <circle cx="{cx}" cy="{cy}" r="{r}" class="comp"/>\n'
    if arrow_up:
        out += f'  <line x1="{cx}" y1="{cy + 12}" x2="{cx}" y2="{cy - 10}" stroke="#0f172a" stroke-width="2.2" marker-end="url(#arrow-curr)"/>\n'
    else:
        out += f'  <line x1="{cx}" y1="{cy - 12}" x2="{cx}" y2="{cy + 10}" stroke="#0f172a" stroke-width="2.2" marker-end="url(#arrow-curr)"/>\n'
    if label_left:
        out += f'  <text x="{cx - r - 8}" y="{cy + 5}" text-anchor="end" class="label">{label_left}</text>\n'
    if label_right:
        out += f'  <text x="{cx + r + 8}" y="{cy + 5}" text-anchor="start" class="label">{label_right}</text>\n'
    return out


def draw_cccs_v(cx: int, cy: int, label_right: str = "", half_w: int = 22, half_h: int = 26, arrow_up: bool = True) -> str:
    pts = f"{cx},{cy - half_h} {cx + half_w},{cy} {cx},{cy + half_h} {cx - half_w},{cy}"
    out = f'  <polygon points="{pts}" class="comp-dep"/>\n'
    if arrow_up:
        out += f'  <line x1="{cx}" y1="{cy + 13}" x2="{cx}" y2="{cy - 11}" stroke="#dc2626" stroke-width="2.2" marker-end="url(#arrow-ctrl)"/>\n'
    else:
        out += f'  <line x1="{cx}" y1="{cy - 13}" x2="{cx}" y2="{cy + 11}" stroke="#dc2626" stroke-width="2.2" marker-end="url(#arrow-ctrl)"/>\n'
    if label_right:
        out += f'  <text x="{cx + half_w + 10}" y="{cy + 5}" text-anchor="start" class="ctrl-label">{label_right}</text>\n'
    return out


def draw_vcvs_h(cx: int, cy: int, label_top: str = "", half_w: int = 26, half_h: int = 20, plus_right: bool = True) -> str:
    pts = f"{cx - half_w},{cy} {cx},{cy - half_h} {cx + half_w},{cy} {cx},{cy + half_h}"
    out = f'  <polygon points="{pts}" class="comp-dep"/>\n'
    px_plus = cx + 10 if plus_right else cx - 10
    px_minus = cx - 10 if plus_right else cx + 10
    out += f'  <text x="{px_plus}" y="{cy + 5}" text-anchor="middle" class="ctrl-label">+</text>\n'
    out += f'  <text x="{px_minus}" y="{cy + 5}" text-anchor="middle" class="ctrl-label">−</text>\n'
    if label_top:
        out += f'  <text x="{cx}" y="{cy - half_h - 9}" text-anchor="middle" class="ctrl-label">{label_top}</text>\n'
    return out


def draw_capacitor_v(cx: int, cy: int, label_right: str = "", plate_w: int = 28, gap: int = 8) -> str:
    y1 = cy - gap // 2
    y2 = cy + gap // 2
    out = f'  <line x1="{cx - plate_w // 2}" y1="{y1}" x2="{cx + plate_w // 2}" y2="{y1}" stroke="#0f172a" stroke-width="3.2"/>\n'
    out += f'  <line x1="{cx - plate_w // 2}" y1="{y2}" x2="{cx + plate_w // 2}" y2="{y2}" stroke="#0f172a" stroke-width="3.2"/>\n'
    if label_right:
        out += f'  <text x="{cx + plate_w // 2 + 10}" y="{cy + 5}" text-anchor="start" class="label">{label_right}</text>\n'
    return out


def draw_ground(cx: int, cy: int) -> str:
    return (
        f'  <line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy + 12}" class="wire"/>\n'
        f'  <line x1="{cx - 16}" y1="{cy + 12}" x2="{cx + 16}" y2="{cy + 12}" class="wire"/>\n'
        f'  <line x1="{cx - 10}" y1="{cy + 18}" x2="{cx + 10}" y2="{cy + 18}" class="wire"/>\n'
        f'  <line x1="{cx - 4}" y1="{cy + 24}" x2="{cx + 4}" y2="{cy + 24}" class="wire"/>\n'
    )


# ==============================================================================
# 模板 1（简单题 Easy）：含受控源（CCCS）的戴维南等效与最大功率传输（第 4 章 电路定理）
# ==============================================================================
def build_template_thevenin_dependent() -> Dict[str, Any]:
    Us_val, R1_val, R2_val, R3_val, beta_val = 36, 6, 12, 4, 1

    Us, R1, R2, R3, beta = sp.symbols("Us R1 R2 R3 beta", real=True, positive=True)
    UA_oc, I1_oc = sp.symbols("UA_oc I1_oc", real=True)

    # 1) 开路电压 Uoc
    eq_oc_1 = sp.Eq(UA_oc, R2 * I1_oc)
    eq_oc_2 = sp.Eq((UA_oc - Us) / R1 + I1_oc - beta * I1_oc, 0)
    sol_oc = sp.solve([eq_oc_1, eq_oc_2], (UA_oc, I1_oc))
    Uoc_expr = sol_oc[UA_oc] + R3 * (beta * sol_oc[I1_oc])

    # 2) 短路电流 Isc
    UA_sc, I1_sc, Isc = sp.symbols("UA_sc I1_sc Isc", real=True)
    eq_sc_1 = sp.Eq(UA_sc, R2 * I1_sc)
    eq_sc_2 = sp.Eq((UA_sc - Us) / R1 + I1_sc + UA_sc / R3, 0)
    eq_sc_3 = sp.Eq(Isc, UA_sc / R3 + beta * I1_sc)
    sol_sc = sp.solve([eq_sc_1, eq_sc_2, eq_sc_3], (UA_sc, I1_sc, Isc))

    subs_map = {Us: Us_val, R1: R1_val, R2: R2_val, R3: R3_val, beta: beta_val}
    I1_oc_num = int(sol_oc[I1_oc].subs(subs_map))
    Uoc_num = int(Uoc_expr.subs(subs_map))
    I1_sc_num = int(sol_sc[I1_sc].subs(subs_map))
    Isc_num = int(sol_sc[Isc].subs(subs_map))
    Req_num = int(sp.Rational(Uoc_num, Isc_num))
    Req_wrong = int(sp.Rational(R1_val * R2_val, R1_val + R2_val) + R3_val)
    Pmax_num = int(sp.Rational(Uoc_num**2, 4 * Req_num))

    svg = svg_header(760, 360)
    svg += '  <text x="380" y="34" text-anchor="middle" class="title">题 1 图：含受控电流源（CCCS）的线性有源一端口网络</text>\n'

    y_top, y_bot, y_mid = 95, 285, 190
    x_left, x_A, x_dep, x_port, x_RL = 140, 310, 485, 585, 665

    svg += f'  <line x1="{x_left}" y1="{y_top}" x2="201" y2="{y_top}" class="wire"/>\n'
    svg += draw_resistor_h(225, y_top, label_top=sub("R", "1", " = 6 Ω"))
    svg += f'  <line x1="249" y1="{y_top}" x2="{x_A}" y2="{y_top}" class="wire"/>\n'

    svg += f'  <line x1="{x_A}" y1="{y_top}" x2="371" y2="{y_top}" class="wire"/>\n'
    svg += draw_resistor_h(395, y_top, label_top=sub("R", "3", " = 4 Ω"))
    svg += f'  <line x1="419" y1="{y_top}" x2="{x_port - 5}" y2="{y_top}" class="wire"/>\n'

    svg += f'  <line x1="{x_left}" y1="{y_top}" x2="{x_left}" y2="{y_mid - 22}" class="wire"/>\n'
    svg += draw_vsource_v(x_left, y_mid, label_left=sub("U", "s", " = 36 V"), r=22, plus_top=True)
    svg += f'  <line x1="{x_left}" y1="{y_mid + 22}" x2="{x_left}" y2="{y_bot}" class="wire"/>\n'

    svg += f'  <line x1="{x_A}" y1="{y_top}" x2="{x_A}" y2="{y_mid - 24}" class="wire"/>\n'
    svg += f'  <line x1="{x_A}" y1="{y_top + 22}" x2="{x_A}" y2="{y_top + 56}" stroke="#dc2626" stroke-width="2.2" marker-end="url(#arrow-ctrl)"/>\n'
    svg += f'  <text x="{x_A + 12}" y="{y_top + 46}" class="ctrl-label">{sub("I", "1")}</text>\n'
    svg += draw_resistor_v(x_A, y_mid, label_right=sub("R", "2", " = 12 Ω"))
    svg += f'  <line x1="{x_A}" y1="{y_mid + 24}" x2="{x_A}" y2="{y_bot}" class="wire"/>\n'

    svg += f'  <line x1="{x_dep}" y1="{y_top}" x2="{x_dep}" y2="{y_mid - 26}" class="wire"/>\n'
    svg += draw_cccs_v(x_dep, y_mid, label_right=sub("1·I", "1"), arrow_up=True)
    svg += f'  <line x1="{x_dep}" y1="{y_mid + 26}" x2="{x_dep}" y2="{y_bot}" class="wire"/>\n'

    svg += f'  <line x1="{x_left}" y1="{y_bot}" x2="{x_port - 5}" y2="{y_bot}" class="wire"/>\n'
    svg += draw_ground(x_A, y_bot)

    for nx, ny in [(x_A, y_top), (x_A, y_bot), (x_dep, y_top), (x_dep, y_bot)]:
        svg += f'  <circle cx="{nx}" cy="{ny}" r="3.8" class="node"/>\n'
    svg += f'  <text x="{x_A}" y="{y_top - 12}" text-anchor="middle" class="sublabel">节点 A</text>\n'

    svg += f'  <line x1="{x_port + 5}" y1="{y_top}" x2="{x_RL}" y2="{y_top}" stroke="#475569" stroke-width="1.8" stroke-dasharray="5 4"/>\n'
    svg += f'  <line x1="{x_port + 5}" y1="{y_bot}" x2="{x_RL}" y2="{y_bot}" stroke="#475569" stroke-width="1.8" stroke-dasharray="5 4"/>\n'
    svg += f'  <line x1="{x_RL}" y1="{y_top}" x2="{x_RL}" y2="{y_mid - 24}" class="wire"/>\n'
    svg += draw_resistor_v(x_RL, y_mid, label_right=sub("R", "L"))
    svg += f'  <line x1="{x_RL}" y1="{y_mid + 24}" x2="{x_RL}" y2="{y_bot}" class="wire"/>\n'
    svg += f'  <line x1="{x_RL - 18}" y1="{y_mid + 18}" x2="{x_RL + 18}" y2="{y_mid - 18}" stroke="#2563eb" stroke-width="1.8" marker-end="url(#arrow-sw)"/>\n'

    svg += f'  <circle cx="{x_port}" cy="{y_top}" r="5" class="port"/>\n'
    svg += f'  <text x="{x_port}" y="{y_top - 12}" text-anchor="middle" class="label">a</text>\n'
    svg += f'  <circle cx="{x_port}" cy="{y_bot}" r="5" class="port"/>\n'
    svg += f'  <text x="{x_port}" y="{y_bot + 24}" text-anchor="middle" class="label">b</text>\n'

    svg += "</svg>\n"

    return {
        "id": "q1_thevenin_dependent",
        "difficulty": "简单",
        "module": "第4章 电路定理（含受控源网络的戴维南定理与最大功率传输）",
        "topology_description": (
            "左侧独立电压源 U_s = 36 V（上正下负，下端接参考地 b）串联电阻 R_1 = 6 Ω 接至节点 A；"
            "节点 A 与参考地 b 之间接电阻 R_2 = 12 Ω，流过 R_2 从 A 向下的电流定义为控制量 I_1；"
            "节点 A 向右串联电阻 R_3 = 4 Ω 到达输出端口上端钮 a；"
            "在输出端钮 a 与参考地端钮 b 之间，并联一个方向由 b 指向 a（向上注入节点 a）的受控电流源（CCCS），其电流大小为 1·I_1；"
            "端口 a-b 外接可变负载电阻 R_L。"
        ),
        "sympy_equations": [
            "开路状态（a-b 断开）：受控电流源 1·I_1 的电流全部从节点 a 经 R_3 向左流回节点 A。对节点 A 列 KCL：(U_A - 36)/6 + I_1 - 1·I_1 = 0 => U_A = 36 V，故 I_1 = U_A / 12 = 3 A；端口开路电压 U_oc = U_a = U_A + R_3 * (1·I_1) = 36 + 4 * 3 = 48 V。",
            "短路状态（a-b 短路，U_a = 0）：受控电流源 1·I_1 直接流入短路支路。对节点 A 列 KCL：(U_A - 36)/6 + U_A/12 + U_A/4 = 0 => U_A = 12 V，此时 I_1 = 12/12 = 1 A，经 R_3 流向 a 的电流为 12/4 = 3 A，故端口短路电流 I_sc = 3 + 1·I_1 = 3 + 1 = 4 A。",
            "戴维南等效内阻：R_eq = U_oc / I_sc = 48 / 4 = 12 Ω。（典型误区：若学生误将受控电流源当作独立源置零开路，从 a-b 看进去会算出错误内阻 R_eq_wrong = (R_1 // R_2) + R_3 = (6 // 12) + 4 = 4 + 4 = 8 Ω）。",
            "最大功率传输：当 R_L = R_eq = 12 Ω 时，P_max = U_oc^2 / (4 * R_eq) = 48^2 / (4 * 12) = 48 W。",
        ],
        "parameters": {
            "U_s": "36 V",
            "R_1": "6 Ω",
            "R_2": "12 Ω",
            "R_3": "4 Ω",
            "CCCS": "1·I_1 (受控电流源，接于节点 a 与地 b 之间，方向向上指向 a，I_1 为流经 R_2 向下的支路电流)",
        },
        "ground_truth": {
            "I1_open_circuit": f"{I1_oc_num} A",
            "U_oc": f"{Uoc_num} V",
            "I1_short_circuit": f"{I1_sc_num} A",
            "I_sc": f"{Isc_num} A",
            "R_eq": f"{Req_num} Ω",
            "R_eq_wrong_if_zeroed": f"{Req_wrong} Ω（典型误区：误将受控源当作独立源直接置零开路所得错误值）",
            "R_L_opt": f"{Req_num} Ω",
            "P_max": f"{Pmax_num} W",
        },
        "svg": svg,
    }


# ==============================================================================
# 模板 2（中等题 Medium）：含开关换路与受控电压源（VCVS）的一阶 RC 暂态电路（第 7 章）
# ==============================================================================
def build_template_first_order_transient() -> Dict[str, Any]:
    Us_val, R1_val, R2_val, R3_val, r_val, C_val = 30, 4, 6, 4, 2, sp.Rational(1, 4)

    Us, R1, R2, R3, r, C = sp.symbols("Us R1 R2 R3 r C", real=True, positive=True)

    ix_0_minus = Us / (R1 + R2)
    uA_0_minus = R2 * ix_0_minus
    uC_0_minus = uA_0_minus + r * ix_0_minus
    uC_0_wrong = uA_0_minus

    Req_expr = R2 + R3 + r
    Req_wrong = R2 + R3
    tau_expr = Req_expr * C

    subs_map = {Us: Us_val, R1: R1_val, R2: R2_val, R3: R3_val, r: r_val, C: C_val}
    ix_0m_num = int(ix_0_minus.subs(subs_map))
    uA_0m_num = int(uA_0_minus.subs(subs_map))
    uC_0_num = int(uC_0_minus.subs(subs_map))
    uC_wrong_num = int(uC_0_wrong.subs(subs_map))
    Req_num = int(Req_expr.subs(subs_map))
    Req_wrong_num = int(Req_wrong.subs(subs_map))
    tau_num = int(tau_expr.subs(subs_map))
    iC_0p_num = int(-sp.Rational(uC_0_num, Req_num))
    ix_0p_num = -iC_0p_num

    svg = svg_header(760, 370)
    svg += '  <text x="380" y="34" text-anchor="middle" class="title">题 2 图：含受控电压源（VCVS）的一阶 RC 换路暂态电路</text>\n'

    y_top, y_bot, y_mid = 105, 295, 200
    x_left, x_A, x_B = 135, 345, 625

    svg += f'  <line x1="{x_left}" y1="{y_top}" x2="{x_left}" y2="{y_mid - 22}" class="wire"/>\n'
    svg += draw_vsource_v(x_left, y_mid, label_left=sub("U", "s", " = 30 V"), r=22, plus_top=True)
    svg += f'  <line x1="{x_left}" y1="{y_mid + 22}" x2="{x_left}" y2="{y_bot}" class="wire"/>\n'

    svg += f'  <line x1="{x_left}" y1="{y_top}" x2="176" y2="{y_top}" class="wire"/>\n'
    svg += draw_resistor_h(200, y_top, label_top=sub("R", "1", " = 4 Ω"))
    svg += f'  <line x1="224" y1="{y_top}" x2="265" y2="{y_top}" class="wire"/>\n'
    svg += f'  <circle cx="265" cy="{y_top}" r="3.5" class="port"/>\n'
    svg += f'  <circle cx="307" cy="{y_top}" r="3.5" class="port"/>\n'
    svg += f'  <line x1="268" y1="{y_top - 1}" x2="304" y2="{y_top - 22}" stroke="#0f172a" stroke-width="2.4" stroke-linecap="round"/>\n'
    svg += f'  <path d="M 290 {y_top + 4} Q 297 {y_top - 14} 285 {y_top - 28}" fill="none" stroke="#2563eb" stroke-width="1.8" marker-end="url(#arrow-sw)"/>\n'
    svg += f'  <text x="287" y="{y_top - 35}" text-anchor="middle" class="sw-label">S (t = 0 断开)</text>\n'
    svg += f'  <line x1="310" y1="{y_top}" x2="{x_A}" y2="{y_top}" class="wire"/>\n'

    svg += f'  <line x1="{x_A}" y1="{y_top}" x2="{x_A}" y2="{y_mid - 24}" class="wire"/>\n'
    svg += f'  <line x1="{x_A}" y1="{y_top + 22}" x2="{x_A}" y2="{y_top + 56}" stroke="#dc2626" stroke-width="2.2" marker-end="url(#arrow-ctrl)"/>\n'
    svg += f'  <text x="{x_A + 12}" y="{y_top + 46}" class="ctrl-label">{sub("i", "x")}</text>\n'
    svg += draw_resistor_v(x_A, y_mid, label_right=sub("R", "2", " = 6 Ω"))
    svg += f'  <line x1="{x_A}" y1="{y_mid + 24}" x2="{x_A}" y2="{y_bot}" class="wire"/>\n'

    svg += f'  <line x1="{x_A}" y1="{y_top}" x2="401" y2="{y_top}" class="wire"/>\n'
    svg += draw_resistor_h(425, y_top, label_top=sub("R", "3", " = 4 Ω"))
    svg += f'  <line x1="449" y1="{y_top}" x2="504" y2="{y_top}" class="wire"/>\n'
    svg += draw_vcvs_h(530, y_top, label_top=sub("2i", "x"), half_w=26, half_h=20, plus_right=True)
    svg += f'  <line x1="556" y1="{y_top}" x2="{x_B}" y2="{y_top}" class="wire"/>\n'

    svg += f'  <line x1="{x_B}" y1="{y_top}" x2="{x_B}" y2="{y_mid - 4}" class="wire"/>\n'
    svg += f'  <line x1="{x_B}" y1="{y_top + 24}" x2="{x_B}" y2="{y_top + 58}" stroke="#0f172a" stroke-width="2.0" marker-end="url(#arrow-curr)"/>\n'
    svg += f'  <text x="{x_B - 12}" y="{y_top + 48}" text-anchor="end" class="sublabel">{sub("i", "C", "(t)")}</text>\n'
    svg += draw_capacitor_v(x_B, y_mid, label_right="C = 0.25 F")
    svg += f'  <text x="{x_B - 22}" y="{y_mid - 12}" text-anchor="end" class="label">+</text>\n'
    svg += f'  <text x="{x_B - 22}" y="{y_mid + 4}" text-anchor="end" class="sublabel">{sub("u", "C", "(t)")}</text>\n'
    svg += f'  <text x="{x_B - 22}" y="{y_mid + 22}" text-anchor="end" class="label">−</text>\n'
    svg += f'  <line x1="{x_B}" y1="{y_mid + 4}" x2="{x_B}" y2="{y_bot}" class="wire"/>\n'

    svg += f'  <line x1="{x_left}" y1="{y_bot}" x2="{x_B}" y2="{y_bot}" class="wire"/>\n'
    svg += draw_ground(x_A, y_bot)

    for nx, ny in [(x_A, y_top), (x_A, y_bot)]:
        svg += f'  <circle cx="{nx}" cy="{ny}" r="3.8" class="node"/>\n'
    svg += f'  <text x="{x_A}" y="{y_top - 12}" text-anchor="middle" class="sublabel">节点 A</text>\n'
    svg += f'  <text x="{x_B}" y="{y_top - 12}" text-anchor="middle" class="sublabel">节点 B</text>\n'

    svg += "</svg>\n"

    return {
        "id": "q2_first_order_transient",
        "difficulty": "中等",
        "module": "第7章 一阶电路的时域分析（换路定则 + 含受控源戴维南等效时间常数 + 三要素法）",
        "topology_description": (
            "左侧独立直流电压源 U_s = 30 V（上正下负，下端接参考地）串联电阻 R_1 = 4 Ω 与开关 S（t < 0 时闭合，t = 0 时断开）接至节点 A；"
            "节点 A 到参考地接电阻 R_2 = 6 Ω，流过 R_2 向下的电流定义为控制量 i_x；"
            "节点 A 向右依次串联电阻 R_3 = 4 Ω 与受控电压源 VCVS（极性为左 − 右 +，电压大小为 2i_x，控制系数 r = 2 Ω）到达节点 B；"
            "节点 B 到参考地接电容 C = 0.25 F（电容电压 u_C(t) 上正下负，电容电流 i_C(t) 参考方向向下）。"
        ),
        "sympy_equations": [
            "换路前稳态（t = 0_-）：开关 S 闭合，电容 C 相当于开路，故流经 R_3 与电容的电流 i_C(0_-) = 0。左侧回路电流 i_x(0_-) = U_s / (R_1 + R_2) = 30 / (4 + 6) = 3 A，节点 A 电压 u_A(0_-) = R_2 * i_x(0_-) = 6 * 3 = 18 V。",
            "隐性陷阱 1（求初始值 u_C(0_+)）：虽然电容支路电流为 0 使 R_3 无压降，但串联在该支路上的受控电压源 2i_x（左−右+）两端仍有电压 2 * i_x(0_-) = 2 * 3 = 6 V！由 KVL 得 u_C(0_-) = u_A(0_-) + 2i_x(0_-) = 18 + 6 = 24 V，由换路定则得 u_C(0_+) = u_C(0_-) = 24 V（漏算开路支路受控源电压会误得 18 V）。",
            "隐性陷阱 2（求换路后时间常数 τ）：t >= 0 时开关 S 断开，左支路脱离，电路为零输入响应（u_C(∞) = 0）。在电容端口外加电压 u、设从节点 B 向左流入 R_3 的电流为 i，则该电流全部经节点 A 流过 R_2 下地，即 i_x = i。由 KVL：u = R_3*i + 2*i_x + R_2*i_x = (4 + 2 + 6)*i = 12*i，故戴维南等效电阻 R_eq = 12 Ω（误将受控源短路会算成 10 Ω），时间常数 τ = R_eq * C = 12 * 0.25 = 3 s。",
            "全响应与跃变电流（t >= 0）：由三要素法得 u_C(t) = 24 * e^(-t/3) V；电容电流 i_C(t) = C * du_C/dt = 0.25 * (-8 * e^(-t/3)) = -2 * e^(-t/3) A，故 i_C(0_+) = -2 A；流过 R_2 的电流 i_x(t) = -i_C(t) = 2 * e^(-t/3) A，即 i_x(0_+) = 2 A（对比 i_x(0_-) = 3 A，电阻电流发生跃变）。",
        ],
        "parameters": {
            "U_s": "30 V",
            "R_1": "4 Ω",
            "R_2": "6 Ω",
            "R_3": "4 Ω",
            "VCVS": "2i_x（受控电压源，极性左 − 右 +，控制系数 r = 2 Ω，i_x 为流经 R_2 向下的电流）",
            "C": "0.25 F",
            "switch_S": "t < 0 时闭合已久达直流稳态，t = 0 时断开",
        },
        "ground_truth": {
            "ix_0_minus": f"{ix_0m_num} A",
            "uA_0_minus": f"{uA_0m_num} V",
            "uC_0_plus": f"{uC_0_num} V",
            "uC_0_wrong_if_ignore_vcvs": f"{uC_wrong_num} V（隐性陷阱1：误以为电容开路支路电流为0则支路两端无压降，漏算串联受控电压源 2i_x(0-) = 6V）",
            "R_eq_t_ge_0": f"{Req_num} Ω",
            "R_eq_wrong_if_zeroed": f"{Req_wrong_num} Ω（隐性陷阱2：求时间常数时误把受控源置零短路，算出 Req = R2 + R3 = 10 Ω）",
            "tau": f"{tau_num} s",
            "uC_t": "24*exp(-t/3) V (t >= 0)",
            "iC_0_plus": f"{iC_0p_num} A",
            "ix_0_plus": f"{ix_0p_num} A（对比 ix(0-) = 3 A，电阻电流在换路瞬间发生跃变）",
            "iC_t": "-2*exp(-t/3) A (t >= 0)",
        },
        "svg": svg,
    }


# ==============================================================================
# 模板 3（难题 Hard）：含受控源非互易二端口网络与双电源综合分析（第 16 章 二端口 + 第 4 章 定理甄别）
# ==============================================================================
def build_template_two_port_cascade() -> Dict[str, Any]:
    """
    全整数参数设计：
    - 二端口网络 N：R1 = 2Ω, R2 = 4Ω, R3 = 2Ω, 受控电压源 VCVS = 4*I1（左 - 右 +）
      Z11 = 6Ω, Z12 = 4Ω, Z21 = 8Ω, Z22 = 6Ω（Z12 != Z21，非互易！）
    - 端口 1 外接：Us1 = 32V 串联内阻 Rs = 2Ω
    - 端口 2 外接：独立电流源 Is2 = 8A（向上）并联负载电阻 RL = 6Ω
    """
    I1, I2 = sp.symbols("I1 I2", real=True)
    R1_val, R2_val, R3_val, alpha_val = 2, 4, 2, 4
    Us1_val, Rs_val, Is2_val, RL_val = 32, 2, 8, 6

    Z11 = R1_val + R2_val
    Z12 = R2_val
    Z21 = R2_val + alpha_val
    Z22 = R2_val + R3_val

    # 1) 双电源共同作用求解
    eq1 = sp.Eq(Us1_val - Rs_val * I1, Z11 * I1 + Z12 * I2)
    eq2 = sp.Eq(RL_val * (Is2_val - I2), Z21 * I1 + Z22 * I2)
    sol_both = sp.solve([eq1, eq2], (I1, I2))
    I1_both = int(sol_both[I1])
    I2_both = int(sol_both[I2])
    IL_both = int(Is2_val - I2_both)
    UL_both = int(RL_val * IL_both)
    PL_both = int(RL_val * (IL_both**2))

    # 2) 若误用互易定理（误令 Z21 = Z12 = 4Ω）算出的错误结果：
    eq2_wrong_recip = sp.Eq(RL_val * (Is2_val - I2), Z12 * I1 + Z22 * I2)
    sol_wrong_recip = sp.solve([eq1, eq2_wrong_recip], (I1, I2))
    UL_wrong_recip = sp.simplify(RL_val * (Is2_val - sol_wrong_recip[I2]))

    # 3) 叠加定理分量验算（全整数！）
    # (a) 仅 Us1 = 32V 作用（Is2 = 0 开路）：
    sol_us1 = sp.solve(
        [
            sp.Eq(Us1_val - Rs_val * I1, Z11 * I1 + Z12 * I2),
            sp.Eq(RL_val * (0 - I2), Z21 * I1 + Z22 * I2),
        ],
        (I1, I2),
    )
    I1_us1 = int(sol_us1[I1])
    I2_us1 = int(sol_us1[I2])
    IL_us1 = int(-I2_us1)
    UL_us1 = int(RL_val * IL_us1)
    PL_us1 = int(RL_val * (IL_us1**2))

    # (b) 仅 Is2 = 8A 作用（Us1 = 0 短路）：
    sol_is2 = sp.solve(
        [
            sp.Eq(0 - Rs_val * I1, Z11 * I1 + Z12 * I2),
            sp.Eq(RL_val * (Is2_val - I2), Z21 * I1 + Z22 * I2),
        ],
        (I1, I2),
    )
    I1_is2 = int(sol_is2[I1])
    I2_is2 = int(sol_is2[I2])
    IL_is2 = int(Is2_val - I2_is2)
    UL_is2 = int(RL_val * IL_is2)
    PL_is2 = int(RL_val * (IL_is2**2))

    # 绘制高质量 SVG（780x380）
    svg = svg_header(780, 380)
    svg += '  <text x="390" y="32" text-anchor="middle" class="title">题 3 图：含受控源非互易二端口网络 N 与双端有源外电路</text>\n'

    y_top, y_bot, y_mid = 115, 305, 210
    x_src1, x_p1, x_M, x_p2, x_is2, x_RL = 125, 250, 375, 555, 620, 700

    # 二端口虚线背景框
    svg += f'  <rect x="{x_p1 + 10}" y="60" width="{x_p2 - x_p1 - 20}" height="272" class="panel"/>\n'
    svg += f'  <text x="{(x_p1 + x_p2) // 2}" y="80" text-anchor="middle" class="sublabel">含受控源线性二端口网络 N</text>\n'

    # 端口 1 左侧外电路：Us1 = 32V + Rs = 2Ω
    svg += f'  <line x1="{x_src1}" y1="{y_top}" x2="{x_src1}" y2="{y_mid - 22}" class="wire"/>\n'
    svg += draw_vsource_v(x_src1, y_mid, label_left=sub("U", "s1", " = 32 V"), r=22, plus_top=True)
    svg += f'  <line x1="{x_src1}" y1="{y_mid + 22}" x2="{x_src1}" y2="{y_bot}" class="wire"/>\n'

    svg += f'  <line x1="{x_src1}" y1="{y_top}" x2="158" y2="{y_top}" class="wire"/>\n'
    svg += draw_resistor_h(182, y_top, label_top=sub("R", "s", " = 2 Ω"))
    svg += f'  <line x1="206" y1="{y_top}" x2="{x_p1 - 5}" y2="{y_top}" class="wire"/>\n'
    svg += f'  <line x1="212" y1="{y_top}" x2="238" y2="{y_top}" stroke="#dc2626" stroke-width="2.2" marker-end="url(#arrow-ctrl)"/>\n'
    svg += f'  <text x="225" y="{y_top - 10}" text-anchor="middle" class="ctrl-label">{sub("I", "1")}</text>\n'

    # 二端口内部：端口1 -> R1(2Ω) -> 节点 M -> R2(4Ω) -> 底线
    svg += f'  <line x1="{x_p1 + 5}" y1="{y_top}" x2="286" y2="{y_top}" class="wire"/>\n'
    svg += draw_resistor_h(310, y_top, label_top=sub("R", "1", " = 2 Ω"))
    svg += f'  <line x1="334" y1="{y_top}" x2="{x_M}" y2="{y_top}" class="wire"/>\n'

    svg += f'  <line x1="{x_M}" y1="{y_top}" x2="{x_M}" y2="{y_mid - 24}" class="wire"/>\n'
    svg += draw_resistor_v(x_M, y_mid, label_right=sub("R", "2", " = 4 Ω"))
    svg += f'  <line x1="{x_M}" y1="{y_mid + 24}" x2="{x_M}" y2="{y_bot}" class="wire"/>\n'

    # 二端口内部右臂：节点 M -> R3(2Ω) -> VCVS(4*I1, 左-右+) -> 端口2
    svg += f'  <line x1="{x_M}" y1="{y_top}" x2="411" y2="{y_top}" class="wire"/>\n'
    svg += draw_resistor_h(435, y_top, label_top=sub("R", "3", " = 2 Ω"))
    svg += f'  <line x1="459" y1="{y_top}" x2="479" y2="{y_top}" class="wire"/>\n'
    svg += draw_vcvs_h(505, y_top, label_top=sub("4I", "1"), half_w=26, half_h=20, plus_right=True)
    svg += f'  <line x1="531" y1="{y_top}" x2="{x_p2 - 5}" y2="{y_top}" class="wire"/>\n'

    # 端口 2 右侧外电路：I2 箭头 + Is2 = 8A（向上） + RL = 6Ω
    svg += f'  <line x1="{x_p2 + 5}" y1="{y_top}" x2="{x_RL}" y2="{y_top}" class="wire"/>\n'
    svg += f'  <line x1="595" y1="{y_top}" x2="568" y2="{y_top}" stroke="#0f172a" stroke-width="2.2" marker-end="url(#arrow-curr)"/>\n'
    svg += f'  <text x="582" y="{y_top - 10}" text-anchor="middle" class="label">{sub("I", "2")}</text>\n'

    svg += f'  <line x1="{x_is2}" y1="{y_top}" x2="{x_is2}" y2="{y_mid - 22}" class="wire"/>\n'
    svg += draw_isource_v(x_is2, y_mid, label_left=sub("I", "s2", "=8A"), r=20, arrow_up=True)
    svg += f'  <line x1="{x_is2}" y1="{y_mid + 22}" x2="{x_is2}" y2="{y_bot}" class="wire"/>\n'

    svg += f'  <line x1="{x_RL}" y1="{y_top}" x2="{x_RL}" y2="{y_mid - 24}" class="wire"/>\n'
    svg += f'  <line x1="{x_RL}" y1="{y_top + 22}" x2="{x_RL}" y2="{y_top + 54}" stroke="#0f172a" stroke-width="2.0" marker-end="url(#arrow-curr)"/>\n'
    svg += f'  <text x="{x_RL - 10}" y="{y_top + 46}" text-anchor="end" class="sublabel">{sub("I", "L")}</text>\n'
    svg += draw_resistor_v(x_RL, y_mid, label_right=sub("R", "L", " = 6 Ω"))
    svg += f'  <line x1="{x_RL}" y1="{y_mid + 24}" x2="{x_RL}" y2="{y_bot}" class="wire"/>\n'

    # 底部全通导线
    svg += f'  <line x1="{x_src1}" y1="{y_bot}" x2="{x_p1 - 5}" y2="{y_bot}" class="wire"/>\n'
    svg += f'  <line x1="{x_p1 + 5}" y1="{y_bot}" x2="{x_p2 - 5}" y2="{y_bot}" class="wire"/>\n'
    svg += f'  <line x1="{x_p2 + 5}" y1="{y_bot}" x2="{x_RL}" y2="{y_bot}" class="wire"/>\n'

    for nx, ny in [(x_M, y_top), (x_M, y_bot), (x_is2, y_top), (x_is2, y_bot)]:
        svg += f'  <circle cx="{nx}" cy="{ny}" r="3.8" class="node"/>\n'
    svg += f'  <text x="{x_M}" y="{y_top - 10}" text-anchor="middle" class="sublabel">M</text>\n'

    for px, py, plabel, dy in [
        (x_p1, y_top, "1", -12),
        (x_p1, y_bot, "1′", 24),
        (x_p2, y_top, "2", -12),
        (x_p2, y_bot, "2′", 24),
    ]:
        svg += f'  <circle cx="{px}" cy="{py}" r="5" class="port"/>\n'
        svg += f'  <text x="{px}" y="{py + dy}" text-anchor="middle" class="label">{plabel}</text>\n'

    svg += "</svg>\n"

    return {
        "id": "q3_two_port_cascade",
        "difficulty": "困难",
        "module": "第16章 二端口网络 + 第4章 电路定理前提甄别（非互易二端口Z参数 + 互易定理失效甄别 + 双源叠加与功率不可叠加定量分析）",
        "topology_description": (
            "虚线框内为含受控源的线性二端口网络 N（左端口 1-1'，右端口 2-2'，1'-2' 为底部直通公共参考端，标准参考方向：I_1 从端钮 1 流入，I_2 从端钮 2 流入）："
            "二端口内部由 T 型网络构成：端钮 1 串联 R_1 = 2 Ω 到内部节点 M；节点 M 到公共底线接 R_2 = 4 Ω；节点 M 向右串联 R_3 = 2 Ω 与受控电压源 VCVS（极性左 − 右 +，电压为 4I_1）到达端钮 2。"
            "外部电路：端口 1-1' 外接独立电压源 U_s1 = 32 V（上正下负）串联内阻 R_s = 2 Ω；端口 2-2' 外接独立电流源 I_s2 = 8 A（方向由 2' 向上指向 2）与负载电阻 R_L = 6 Ω 并联（设流过 R_L 向下的负载电流为 I_L，负载电压 U_L = U_2 上正下负）。"
        ),
        "sympy_equations": [
            "第(1)问 求 Z 参数与互易定理甄别：对内部 T 型网络列 KVL，U_1 = R_1*I_1 + R_2*(I_1 + I_2) = 6*I_1 + 4*I_2；U_2 = R_2*(I_1 + I_2) + 4*I_1 + R_3*I_2 = 8*I_1 + 6*I_2。故 Z = [[6, 4], [8, 6]] Ω（Z_11 = 6 Ω, Z_12 = 4 Ω, Z_21 = 8 Ω, Z_22 = 6 Ω）。因 Z_12 = 4 Ω != Z_21 = 8 Ω，该二端口不满足互易定理！（若误按互易定理令 Z_21 = Z_12 = 4 Ω，联立外电路会算出错误负载电压 U_L_wrong = 144/5 = 28.8 V）。",
            "第(2)问 双电源共同作用求解：端口 1 外电路方程 U_1 = 32 - 2*I_1，代入 U_1 = 6*I_1 + 4*I_2 得 8*I_1 + 4*I_2 = 32 (式①)；端口 2 节点 KCL 为 I_s2 = I_2 + I_L => I_L = 8 - I_2，故 U_2 = U_L = 6*(8 - I_2) = 48 - 6*I_2，代入 U_2 = 8*I_1 + 6*I_2 得 8*I_1 + 12*I_2 = 48 (式②)。联立式①②解得：I_1 = 3 A, I_2 = 2 A，从而负载电流 I_L = 8 - 2 = 6 A，负载电压 U_L = 6 * 6 = 36 V，负载实际吸收功率 P_L = I_L^2 * R_L = 6^2 * 6 = 216 W。",
            "第(3)问 叠加定理分量与功率差值 ΔP 定量分析：(a) 仅 U_s1 = 32 V 作用（I_s2 = 0 开路，受控源保留）：联立 8*I_1' + 4*I_2' = 32 与 8*I_1' + 12*I_2' = 0，解得 I_1' = 6 A, I_2' = -4 A，故 I_L' = -I_2' = 4 A, U_L' = 24 V, 单独功率 P_L' = (4)^2 * 6 = 96 W；(b) 仅 I_s2 = 8 A 作用（U_s1 = 0 短路，受控源保留）：联立 8*I_1'' + 4*I_2'' = 0 与 8*I_1'' + 12*I_2'' = 48，解得 I_1'' = -3 A, I_2'' = 6 A，故 I_L'' = 8 - 6 = 2 A, U_L'' = 12 V, 单独功率 P_L'' = (2)^2 * 6 = 24 W；(c) 对比验证：电流满足线性叠加 I_L = I_L' + I_L'' = 4 + 2 = 6 A，但单独功率之和 P_L' + P_L'' = 96 + 24 = 120 W != P_L = 216 W，差值 ΔP = P_L - (P_L' + P_L'') = 216 - 120 = 96 W，恰好等于二次型展开中的交叉耦合功率项 2 * I_L' * I_L'' * R_L = 2 * 4 * 2 * 6 = 96 W。",
        ],
        "parameters": {
            "two_port_N": "T型拓扑含受控源：R_1 = 2 Ω, R_2 = 4 Ω, R_3 = 2 Ω，输出臂串联受控电压源 4I_1（左 − 右 +，I_1 为端口 1 流入电流）",
            "port_1_source": "U_s1 = 32 V 串联内阻 R_s = 2 Ω",
            "port_2_load": "独立电流源 I_s2 = 8 A（方向向上）与负载电阻 R_L = 6 Ω 并联",
        },
        "ground_truth": {
            "Z_matrix": f"[[{Z11}, {Z12}], [{Z21}, {Z22}]] Ω（即 Z11 = 6 Ω, Z12 = 4 Ω, Z21 = 8 Ω, Z22 = 6 Ω）",
            "reciprocity_check": f"Z12 = {Z12} Ω != Z21 = {Z21} Ω，因内部含受控源 4I_1，破坏了互易性；若误按互易二端口令 Z21 = Z12 = 4 Ω，会算出错误负载电压 U_L = {UL_wrong_recip} V",
            "I1_both": f"{I1_both} A",
            "I2_both": f"{I2_both} A",
            "I_L_both": f"{IL_both} A",
            "U_L_both": f"{UL_both} V",
            "P_L_both": f"{PL_both} W",
            "superposition_Us1_only": f"I_1' = {I1_us1} A, I_2' = {I2_us1} A, I_L' = {IL_us1} A, U_L' = {UL_us1} V, P_L' = {PL_us1} W",
            "superposition_Is2_only": f"I_1'' = {I1_is2} A, I_2'' = {I2_is2} A, I_L'' = {IL_is2} A, U_L'' = {UL_is2} V, P_L'' = {PL_is2} W",
            "power_trap_verification": f"电流叠加 I_L = I_L' + I_L'' = {IL_us1} + {IL_is2} = {IL_both} A 成立，但功率直接相加 P_L' + P_L'' = {PL_us1} + {PL_is2} = {PL_us1 + PL_is2} W != 实际功率 P_L = {PL_both} W（差值恰为交叉耦合功率项 2*I_L'*I_L''*R_L = {2 * IL_us1 * IL_is2 * RL_val} W）",
        },
        "svg": svg,
    }


# ==============================================================================
# 模板 4（扩展模板）：正弦稳态相量 + 互感耦合电感去耦与谐振匹配（第 9/10/11 章）
# ==============================================================================
def build_template_coupled_resonance() -> Dict[str, Any]:
    w_val, L1_val, L2_val, M_val, C_val, R1_val = 1000, sp.Rational(6, 1000), sp.Rational(12, 1000), sp.Rational(4, 1000), sp.Rational(100, 1000000), 10
    X_L1 = int(w_val * L1_val)
    X_L2 = int(w_val * L2_val)
    X_M = int(w_val * M_val)
    X_C = int(1 / (w_val * C_val))
    # T型同名端异名去耦：等效串联电抗 X_La = X_L1 + X_M = 10Ω，恰与串联电容 -jX_C = -j10Ω 发生串联谐振！
    svg = svg_header(760, 360)
    svg += '  <text x="380" y="34" text-anchor="middle" class="title">扩展模板图：正弦稳态耦合电感（带同名端 •）与谐振匹配网络</text>\n'
    y_top, y_bot, y_mid = 105, 285, 195
    svg += f'  <line x1="135" y1="{y_top}" x2="180" y2="{y_top}" class="wire"/>\n'
    svg += draw_resistor_h(204, y_top, label_top="R₁ = 10 Ω")
    svg += f'  <line x1="228" y1="{y_top}" x2="290" y2="{y_top}" class="wire"/>\n'
    # 串联电容 -j10Ω
    svg += f'  <line x1="290" y1="{y_top - 14}" x2="290" y2="{y_top + 14}" stroke="#0f172a" stroke-width="3.2"/>\n'
    svg += f'  <line x1="298" y1="{y_top - 14}" x2="298" y2="{y_top + 14}" stroke="#0f172a" stroke-width="3.2"/>\n'
    svg += f'  <text x="294" y="{y_top - 20}" text-anchor="middle" class="label">−j10 Ω</text>\n'
    svg += f'  <line x1="298" y1="{y_top}" x2="360" y2="{y_top}" class="wire"/>\n'
    # 耦合电感 L1 (连续半圆弧线圈 + 同名端黑点 •)
    svg += f'  <path d="M 360 {y_top} A 8 8 0 0 1 376 {y_top} A 8 8 0 0 1 392 {y_top} A 8 8 0 0 1 408 {y_top} A 8 8 0 0 1 424 {y_top}" class="wire"/>\n'
    svg += f'  <circle cx="366" cy="{y_top - 12}" r="3.5" class="node"/>\n'
    svg += f'  <text x="392" y="{y_top - 16}" text-anchor="middle" class="label">j6 Ω</text>\n'
    svg += f'  <line x1="424" y1="{y_top}" x2="560" y2="{y_top}" class="wire"/>\n'
    # 竖支路耦合电感 L2 (连续半圆弧线圈 + 同名端黑点 •)
    svg += f'  <line x1="470" y1="{y_top}" x2="470" y2="160" class="wire"/>\n'
    svg += f'  <path d="M 470 160 A 8 8 0 0 1 470 176 A 8 8 0 0 1 470 192 A 8 8 0 0 1 470 208 A 8 8 0 0 1 470 224" class="wire"/>\n'
    svg += f'  <circle cx="458" cy="218" r="3.5" class="node"/>\n'
    svg += f'  <text x="485" y="198" text-anchor="start" class="label">j12 Ω</text>\n'
    svg += f'  <line x1="470" y1="224" x2="470" y2="{y_bot}" class="wire"/>\n'
    # 互感 M 双向弧线
    svg += f'  <path d="M 405 {y_top + 12} Q 445 140 456 175" fill="none" stroke="#dc2626" stroke-width="1.8" stroke-dasharray="4 3"/>\n'
    svg += f'  <text x="415" y="152" class="ctrl-label">jX_M = j4 Ω</text>\n'
    svg += f'  <line x1="135" y1="{y_top}" x2="135" y2="{y_mid - 22}" class="wire"/>\n'
    svg += draw_vsource_v(135, y_mid, label_left="U̇s = 50∠0° V", r=22, plus_top=True)
    svg += f'  <line x1="135" y1="{y_mid + 22}" x2="135" y2="{y_bot}" class="wire"/>\n'
    svg += f'  <line x1="135" y1="{y_bot}" x2="560" y2="{y_bot}" class="wire"/>\n'
    svg += f'  <circle cx="565" cy="{y_top}" r="5" class="port"/>\n'
    svg += f'  <circle cx="565" cy="{y_bot}" r="5" class="port"/>\n'
    svg += "</svg>\n"
    return {
        "id": "q4_coupled_resonance",
        "difficulty": "困难",
        "module": "第9/10/11章 正弦稳态与耦合电感谐振电路",
        "parameters": {"omega": "1000 rad/s", "X_L1": f"{X_L1} Ω", "X_L2": f"{X_L2} Ω", "X_M": f"{X_M} Ω", "X_C": f"{X_C} Ω", "R1": f"{R1_val} Ω"},
        "ground_truth": {"Z_eq": "6 + j8 Ω", "Z_L_conj_match": "6 - j8 Ω", "R_L_pure_res_match": "10 Ω"},
        "svg": svg,
    }


def get_exam_templates_for_stu001() -> List[Dict[str, Any]]:
    return [
        build_template_thevenin_dependent(),
        build_template_first_order_transient(),
        build_template_two_port_cascade(),
    ]


def export_template_graphics(templates: List[Dict[str, Any]], out_dir: str) -> List[Dict[str, str]]:
    os.makedirs(out_dir, exist_ok=True)
    exported = []
    for idx, tpl in enumerate(templates, start=1):
        svg_path = os.path.join(out_dir, f"q{idx}.svg")
        png_path = os.path.join(out_dir, f"q{idx}.png")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(tpl["svg"])
        cairosvg.svg2png(bytestring=tpl["svg"].encode("utf-8"), write_to=png_path, dpi=180)
        exported.append({"svg": svg_path, "png": png_path})
    return exported


if __name__ == "__main__":
    tpls = get_exam_templates_for_stu001()
    paths = export_template_graphics(tpls, os.path.join(os.path.dirname(__file__), "examples"))
    for t, p in zip(tpls, paths):
        print(f"[{t['difficulty']}] {t['module']} -> {p['png']}")
        print("  Ground truth:", t["ground_truth"])
