#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 专职电路图 SVG 画师 (ascii_to_svg.py)
核心思想：
  将「出题推理」与「图形渲染」解耦——出题阶段仅输出轻量级 ASCII 电路拓扑草图，
  随后由本模块针对单道题（1 题 1 调用），将【题干描述 + ASCII 电路拓扑图】交给 DeepSeek，
  由 DeepSeek 自主生成任意拓扑的国标/教材风格 SVG 源码，并经通用几何碰撞检测器（防穿模、防文字重叠）与 CairoSVG 渲染成高清 PNG。
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, Tuple, List
import cairosvg
from critic import call_deepseek

SVG_SYSTEM_PROMPT = """你是高等教育出版社《电路》（邱关源 主编）的专职 SVG 电路图绘制专家。
你的唯一任务是：根据用户提供的【单道电路题干描述】与【ASCII 电路拓扑草图】，编写一段完整、可直接由 CairoSVG 渲染为教科书插图的 `<svg>...</svg>` 源码。

### 一、画布与全局样式铁律（必须严格遵守）
1. 画布尺寸统一为：`viewBox="0 0 820 380" width="820" height="380"`，顶部预留 `y=32` 居中放置图题（`x="410"`）。
2. 必须在 `<svg>` 开头包含以下标准精致小箭头 `<defs>`（直接照抄，严禁把 markerWidth 改成大于 6）：
```xml
  <defs>
    <marker id="arrow-ctrl" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#dc2626"/>
    </marker>
    <marker id="arrow-curr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0f172a"/>
    </marker>
    <marker id="arrow-sw" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2563eb"/>
    </marker>
  </defs>
```
3. 背景：`<rect width="100%" height="100%" fill="#ffffff"/>`。
4. 字体：统一使用 `font-family: 'WenQuanYi Micro Hei', 'Noto Sans CJK SC', sans-serif;`。
5. **严禁使用 `<tspan>` 标签**（CairoSVG 渲染 `<tspan>` 配合 `text-anchor` 时会发生严重字符重叠）！
   - 数字下标请直接使用 Unicode 下标字符：`₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉`（如 `R₁ = 6 Ω`、`4I₁`、`Us₁ = 32 V`）；
   - 字母下标请直接写普通英文字符（如 `Us = 30 V`、`RL`、`ix`、`2ix`、`uC(t)`、`iC(t)`、`Rs = 2 Ω`、`Is₂ = 8 A`、`IL`），绝不使用 `ₛ`、`ₓ` 等生僻 Unicode 字母下标（会变豆腐块）。
6. 边距与横向列距安全区：
   - 所有最左侧文字的左边缘必须满足 `x >= 25`（最左侧垂直支路的 `x` 坐标建议设在 `x = 120 ~ 140` 之间，左侧电压源文字用 `text-anchor="end"` 放在 `x - 30` 处）；
   - 当电路包含多级元件（如：左侧源 + Rs + 二端口网络 + 右侧并联电流源 Is₂ + 并联负载电阻 RL）时，务必均匀分配横向 x 坐标，**严禁把两个并联垂直支路（如 Is₂ 和 RL）画在同一个 x 坐标上**！推荐横向坐标分配示例：左源 `x=115` → `Rs` 中心 `x=175` → 端口1 `x=235` → 二端口虚线框 `x="245" width="300"` → `R₁` 中心 `x=295` → 节点M `x=365` → `R₃` 中心 `x=425` → 受控源中心 `x=495` → 端口2 `x=555`（`I₂` 箭头从 `x=595` 向左指到 `x=568`）→ 并联电流源 `Is₂` 垂直支路 `x=635`（文字标在左侧 `x=608, text-anchor="end"`）→ 并联负载电阻 `RL` 垂直支路 `x=715`（文字标在右侧 `x=732, text-anchor="start"`，不要画多余的 UL 文字以免压线）。

### 二、标准电路图元与防穿模（防短路/防碰撞）坐标准则
建议主回路采用清晰的网格坐标：上水平母线 `y = 115`，下水平公共母线 `y = 300`，垂直支路元件中心 `y = 207`。
**【极其重要：1. 导线绝对不能穿过任何元件内部！2. 垂直支路的 x 坐标必须选在两个水平元件之间的纯导线节点上，绝对不能插在水平电阻矩形框的 x 范围内！3. 严禁添加题干未要求的多余垂直短路线！】**

1. **水平电阻（中心 `(cx, cy)`，宽 `48`，高 `18`）**：
   - 矩形框：`<rect x="{cx-24}" y="{cy-9}" width="48" height="18" fill="#ffffff" stroke="#0f172a" stroke-width="2.2"/>`
   - 左右连接导线必须在 `cx-24` 和 `cx+24` 处断开！并且区间 `[cx-28, cx+28]` 内严禁有任何垂直支路或节点圆点接入！
   - 文字标注放在上方 `y = cy - 16`，`text-anchor="middle"`。

2. **垂直电阻（中心 `(cx, cy)`，宽 `18`，高 `48`）**：
   - 矩形框：`<rect x="{cx-9}" y="{cy-24}" width="18" height="48" fill="#ffffff" stroke="#0f172a" stroke-width="2.2"/>`
   - 上下连接导线必须在 `cy-24` 和 `cy+24` 处断开！
   - 文字标注放在右侧 `x = cx + 16, y = cy + 5`，`text-anchor="start"`。

3. **垂直独立电压源（中心 `(cx, cy)`，半径 `r = 22`）**：
   - 圆圈：`<circle cx="{cx}" cy="{cy}" r="22" fill="#ffffff" stroke="#0f172a" stroke-width="2.2"/>`
   - 上下连接导线必须在 `cy-22` 和 `cy+22` 处断开！
   - 极性符号：`+` 在 `(cx, cy-6)`，`−` 在 `(cx, cy+14)`，`text-anchor="middle"`；名称标在左侧 `(cx-32, cy+5)`，`text-anchor="end"`。

4. **垂直独立电流源（中心 `(cx, cy)`，半径 `r = 20`）**：
   - 圆圈：`<circle cx="{cx}" cy="{cy}" r="20" fill="#ffffff" stroke="#0f172a" stroke-width="2.2"/>`
   - 内部画箭头线（如向上：`y1=cy+11` 到 `y2=cy-9`，`marker-end="url(#arrow-curr)"`）；
   - 如果右侧紧邻并联负载电阻 `RL`（间距 `< 90px`），请把电流源文字标在圆圈**左侧** `(cx-26, cy+5)` 且设 `text-anchor="end"`，避免与右侧 `RL` 矩形重叠！

5. **受控源（必须用醒目的红框红字标准菱形 `<polygon>`！）**：
   - **垂直受控电流源 CCCS（中心 `(cx, cy)`，半宽 `22`，半高 `26`）**：
     `<polygon points="{cx},{cy-26} {cx+22},{cy} {cx},{cy+26} {cx-22},{cy}" fill="#fef2f2" stroke="#b91c1c" stroke-width="2.2"/>`
     上下导线在 `cy-26` 和 `cy+26` 处断开；
     **注意箭头方向**：若题干说“方向由 b 指向 a（向上）”，内部箭头必须从下往上画：`y1="{cy+13}" y2="{cy-11}"`！右侧 `(cx+30, cy+5)` 标注红色控制量（如 `1·I₁`）。
   - **水平受控电压源 VCVS（中心 `(cx, cy)`，半宽 `26`，半高 `20`）**：
     `<polygon points="{cx-26},{cy} {cx},{cy-20} {cx+26},{cy} {cx},{cy+20}" fill="#fef2f2" stroke="#b91c1c" stroke-width="2.2"/>`
     左右导线在 `cx-26` 和 `cx+26` 处断开；内部左端 `(cx-10, cy+5)` 标 `−`、右端 `(cx+10, cy+5)` 标 `+`；上方 `(cx, cy-26)` 标红色控制量（如 `2ix` 或 `4I₁`）。
   - **控制量支路电流箭头**：在控制支路导线上画一段醒目的红色箭头（`stroke="#dc2626" marker-end="url(#arrow-ctrl)"`）并标注 `I₁` 或 `ix`。

6. **垂直电容（中心 `(cx, cy)`，极板宽 `28`，间隙 `8`）**：
   - 上极板 `y = cy - 4`，下极板 `y = cy + 4`，各画一条粗水平线（`x1=cx-14` 到 `x2=cx+14, stroke-width="3.2"`）；
   - 上导线连到 `cy - 4`，下导线从 `cy + 4` 连到底部母线（中间 8px 断开！）。

7. **换路开关 S（水平安装在 `(x1, y)` 与 `(x2, y)` 之间，间距约 `42px`）**：
   - 两个空心触点小圆圈 `r="3.5"`，斜杆从 `(x1+3, y-1)` 斜向上画到 `(x2-3, y-22)`，配蓝色弧形动作箭头与上方蓝色文字 `S (t = 0 断开)`。

8. **二端口虚线框、节点与端口**：
   - 若有二端口虚线背景框，顶部 `y` 设为 `54`，框内标题文字放在 `y = 74`（距离 `y = 115` 的上水平母线留出 `41px` 垂直间距，绝不与上母线电阻上方的文字 `y = 99` 重叠！）；
   - T 型连接点画实心黑圆点 `r="3.8"`，端口 `a, b` 或 `1, 1', 2, 2'` 画空心白底圆圈 `r="5"`。

请只输出纯 `<svg>...</svg>` 代码（可包裹在 ```xml ... ``` 代码块中），不要任何多余解释。
"""


def extract_svg_code(text: str) -> str:
    m = re.search(r"(<svg[\s\S]*?</svg>)", text, re.IGNORECASE)
    if not m:
        raise ValueError("未能在 DeepSeek 输出中找到 <svg>...</svg> 标签！")
    svg_str = m.group(1).strip()
    if not svg_str.startswith("<?xml"):
        svg_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_str
    return svg_str


def _estimate_text_bbox(tx: float, ty: float, text_str: str, anchor: str, font_size: float = 14.0) -> Tuple[float, float, float, float]:
    width = 0.0
    for ch in text_str:
        width += font_size * (0.95 if 0x4E00 <= ord(ch) <= 0x9FFF else 0.50)
    height = font_size * 1.10
    if anchor == "middle":
        x1, x2 = tx - width / 2.0, tx + width / 2.0
    elif anchor == "end":
        x1, x2 = tx - width, tx
    else:
        x1, x2 = tx, tx + width
    y1, y2 = ty - height * 0.80, ty + height * 0.15
    return (x1, y1, x2, y2)


def _boxes_overlap(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float], pad: float = 0.0) -> bool:
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def validate_svg_geometry_and_xml(svg_code: str, topology_description: str = "") -> List[str]:
    """
    通用 SVG 语法与几何排版碰撞检测器：
    1. XML 语法完整性；
    2. 禁用 <tspan> 与生僻豆腐块下标字符检查；
    3. 导线/节点穿模进入元件（<rect>/<circle>/<polygon>）内部的短路/错位检测；
    4. 文字与文字重叠、文字与元件框重叠、文字越界检测；
    5. 受控电流源箭头方向与题干一致性核对。
    """
    issues: List[str] = []

    if "<tspan" in svg_code:
        issues.append("检测到使用了 <tspan> 标签，会导致 CairoSVG 文字重叠，请删除所有 <tspan> 并改用纯文本 + Unicode 数字下标（₁₂₃）。")

    bad_chars = [c for c in ["ₛ", "ₓ", "ₐ", "ₘ", "ₗ"] if c in svg_code]
    if bad_chars:
        issues.append(f"检测到字体不支持的 Unicode 字母下标 {bad_chars}（会渲染成方框乱码），请改为普通英文字母（如 Us, ix, RL）。")

    try:
        root = ET.fromstring(svg_code.encode("utf-8"))
    except Exception as e:
        issues.append(f"SVG XML 语法解析失败: {e}")
        return issues

    comp_boxes: List[Tuple[float, float, float, float, str]] = []
    lines: List[Tuple[float, float, float, float]] = []
    nodes: List[Tuple[float, float]] = []
    texts: List[Tuple[float, float, float, float, str]] = []
    polygons: List[Tuple[float, float, float, float]] = []

    for elem in root.iter():
        tag = elem.tag.split("}")[-1]
        if tag == "rect":
            w = str(elem.attrib.get("width", "0"))
            if "%" in w:
                continue
            w_val = float(re.sub(r"[^0-9.]", "", w) or 0)
            h_val = float(re.sub(r"[^0-9.]", "", str(elem.attrib.get("height", "0"))) or 0)
            if w_val > 120 or h_val > 120:
                continue
            x_val = float(elem.attrib.get("x", 0))
            y_val = float(elem.attrib.get("y", 0))
            comp_boxes.append((x_val, y_val, x_val + w_val, y_val + h_val, f"电阻rect(x={x_val:.0f},y={y_val:.0f},w={w_val:.0f},h={h_val:.0f})"))
        elif tag == "circle":
            r_val = float(elem.attrib.get("r", 0))
            cx = float(elem.attrib.get("cx", 0))
            cy = float(elem.attrib.get("cy", 0))
            if r_val >= 14:
                comp_boxes.append((cx - r_val, cy - r_val, cx + r_val, cy + r_val, f"电源circle(cx={cx:.0f},cy={cy:.0f},r={r_val:.0f})"))
            elif r_val <= 6:
                nodes.append((cx, cy))
        elif tag == "polygon":
            pts_str = elem.attrib.get("points", "").strip()
            coords = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", pts_str)]
            if len(coords) >= 6:
                xs = coords[0::2]
                ys = coords[1::2]
                px1, py1, px2, py2 = min(xs), min(ys), max(xs), max(ys)
                if (px2 - px1) > 15 and (py2 - py1) > 15:
                    comp_boxes.append((px1, py1, px2, py2, f"受控源菱形(cx={(px1+px2)/2:.0f},cy={(py1+py2)/2:.0f})"))
                    polygons.append((px1, py1, px2, py2))
        elif tag == "line":
            x1 = float(elem.attrib.get("x1", 0))
            y1 = float(elem.attrib.get("y1", 0))
            x2 = float(elem.attrib.get("x2", 0))
            y2 = float(elem.attrib.get("y2", 0))
            lines.append((x1, y1, x2, y2))
        elif tag == "text":
            txt = (elem.text or "").strip()
            if not txt:
                continue
            tx = float(elem.attrib.get("x", 380))
            ty = float(elem.attrib.get("y", 190))
            anchor = elem.attrib.get("text-anchor", "start")
            bbox = _estimate_text_bbox(tx, ty, txt, anchor, 14.5)
            texts.append((bbox[0], bbox[1], bbox[2], bbox[3], txt))
            if bbox[0] < 10 or bbox[2] > 812 or bbox[1] < 8 or bbox[3] > 374:
                issues.append(f"文本 '{txt}' 包围盒 ({bbox[0]:.0f},{bbox[1]:.0f})~({bbox[2]:.0f},{bbox[3]:.0f}) 过于贴近或超出画布边缘，请向内移动。")

    # 1. 检查节点小圆点是否错误落在了电阻或电源内部
    for nx, ny in nodes:
        for bx1, by1, bx2, by2, bname in comp_boxes:
            if bx1 + 2 < nx < bx2 - 2 and by1 + 2 < ny < by2 - 2:
                issues.append(f"节点圆点 ({nx:.0f},{ny:.0f}) 错误画在了元件 {bname} 内部！节点必须位于元件外部的导线上。")

    # 2. 检查是否有导线穿入或贯穿元件包围盒（排除电源/菱形内部长度 <= 28 的极性/方向短箭头）
    for x1, y1, x2, y2 in lines:
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if length <= 28:
            continue
        lx_min, lx_max = min(x1, x2), max(x1, x2)
        ly_min, ly_max = min(y1, y2), max(y1, y2)
        for bx1, by1, bx2, by2, bname in comp_boxes:
            # 水平导线穿过元件内部
            if abs(y1 - y2) < 1e-2 and (by1 + 2 < y1 < by2 - 2):
                if lx_min < bx2 - 2 and lx_max > bx1 + 2:
                    issues.append(f"水平导线 ({x1:.0f},{y1:.0f})->({x2:.0f},{y2:.0f}) 穿入了元件 {bname} 内部，必须在元件边缘断开！")
            # 垂直导线穿过元件内部（含垂直支路错误接在水平电阻中间！）
            if abs(x1 - x2) < 1e-2 and (bx1 + 2 < x1 < bx2 - 2):
                if ly_min < by2 - 2 and ly_max > by1 + 2:
                    issues.append(f"垂直导线 ({x1:.0f},{y1:.0f})->({x2:.0f},{y2:.0f}) 穿入了元件 {bname} 内部（严禁将垂直支路接在水平电阻中间），请修正坐标！")

    # 3. 检查文本与文本之间的重叠
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            t1 = texts[i]
            t2 = texts[j]
            if _boxes_overlap(t1[:4], t2[:4], pad=-2.0):
                issues.append(f"文本 '{t1[4]}' 与文本 '{t2[4]}' 发生重叠，请调整它们的 x 或 y 坐标拉开间距！")

    # 4. 检查文本与元件框的重叠（排除元件内部的 '+' / '−' 极性字符）
    for tx1, ty1, tx2, ty2, tstr in texts:
        if tstr in ("+", "−", "-", "↑", "↓"):
            continue
        for bx1, by1, bx2, by2, bname in comp_boxes:
            if _boxes_overlap((tx1, ty1, tx2, ty2), (bx1, by1, bx2, by2), pad=-2.0):
                issues.append(f"文本 '{tstr}' 与元件 {bname} 发生重叠（遮挡元件边框），请将该文本移到元件外侧安全位置！")
        # 检查文本是否压在水平或垂直长导线上
        for x1, y1, x2, y2 in lines:
            length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            if length <= 28:
                continue
            lx_min, lx_max = min(x1, x2), max(x1, x2)
            ly_min, ly_max = min(y1, y2), max(y1, y2)
            if abs(x1 - x2) < 1e-2 and (tx1 + 2 < x1 < tx2 - 2) and (ly_min < ty2 - 2 and ly_max > ty1 + 2):
                issues.append(f"文本 '{tstr}' 压在了垂直导线 x={x1:.0f} 上，请移开或删除多余标注！")
            if abs(y1 - y2) < 1e-2 and (ty1 + 2 < y1 < ty2 - 2) and (lx_min < tx2 - 2 and lx_max > tx1 + 2):
                issues.append(f"文本 '{tstr}' 压在了水平导线 y={y1:.0f} 上，请移开！")

    # 5. 若题干明确要求受控电流源方向“向上”，检查菱形内部竖直箭头是否向上（y2 < y1）
    if "向上" in topology_description and polygons:
        for px1, py1, px2, py2 in polygons:
            for x1, y1, x2, y2 in lines:
                if px1 <= x1 <= px2 and px1 <= x2 <= px2 and py1 <= y1 <= py2 and py1 <= y2 <= py2:
                    if abs(x1 - x2) < 2 and y2 > y1:
                        issues.append("题干要求受控电流源方向向上（指向节点 a），但菱形内部箭头画成了向下（y2 > y1），请改为 y1 在下、y2 在上（向上指）！")

    # 6. 若为二端口网络（题干含“I_2 从端钮 2 流入”），检查二端口虚线框是否把外部 Rs 包了进去，以及 I₂ 箭头是否向左
    if "二端口" in topology_description:
        for elem in root.iter():
            if elem.tag.split("}")[-1] == "rect" and elem.attrib.get("stroke-dasharray"):
                rx = float(elem.attrib.get("x", 0))
                rw = float(elem.attrib.get("width", 0))
                if rx < 230 or (rx + rw) < 535:
                    issues.append(f"二端口虚线框 (x={rx:.0f}, width={rw:.0f}) 边界不准确：左边界应设在端口 1 附近（如 x=245），右边界应设在端口 2 附近（如 x+width=545），严禁把外部电阻 Rs 包进二端口框内！")
        for elem in root.iter():
            if elem.tag.split("}")[-1] == "line" and elem.attrib.get("marker-end"):
                x1 = float(elem.attrib.get("x1", 0))
                y1 = float(elem.attrib.get("y1", 0))
                x2 = float(elem.attrib.get("x2", 0))
                y2 = float(elem.attrib.get("y2", 0))
                if abs(y1 - y2) < 2 and 545 <= min(x1, x2) <= 625 and x2 > x1:
                    issues.append(f"端口 2 处的电流 I₂ 箭头 ({x1:.0f},{y1:.0f})->({x2:.0f},{y2:.0f}) 画成了向右流出！标准二端口参考方向 I₂ 必须向左流入端钮 2（即 x1 > x2，从右指向左）！")

    return issues


def generate_svg_from_ascii(
    question_title: str,
    topology_description: str,
    ascii_diagram: str,
    out_svg_path: str,
    out_png_path: str,
    max_retries: int = 4,
) -> Dict[str, Any]:
    """
    单题专职调用 DeepSeek：将【题干拓扑描述 + ASCII 电路图】转换为 SVG 并渲染为 PNG
    """
    feedback = ""
    logs: List[Dict[str, Any]] = []
    final_svg = ""

    for attempt in range(1, max_retries + 1):
        user_prompt = (
            f"请将以下单道电路题的【题干拓扑描述】与【ASCII 电路拓扑图】绘制为教科书级 SVG 电路图：\n\n"
            f"【图题】\n{question_title}\n\n"
            f"【题干拓扑与元件参数】\n{topology_description}\n\n"
            f"【ASCII 电路拓扑草图】\n```text\n{ascii_diagram.strip()}\n```\n"
        )
        if feedback and final_svg:
            user_prompt += (
                f"\n【你上一轮生成的 SVG 源码】\n```xml\n{final_svg}\n```\n"
                f"\n【自动几何碰撞检测发现的问题（请保持上一轮 SVG 其余正确结构不变，仅精准修改以下几处坐标/方向问题）】\n{feedback}\n"
            )
        elif feedback:
            user_prompt += f"\n【上一版 SVG 自动几何碰撞检测发现的问题（请立即修正坐标）】\n{feedback}\n"

        raw_resp, meta = call_deepseek(
            messages=[
                {"role": "system", "content": SVG_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=8192,
        )

        try:
            svg_code = extract_svg_code(raw_resp)
            issues = validate_svg_geometry_and_xml(svg_code, topology_description=topology_description)
            os.makedirs(os.path.dirname(os.path.abspath(out_svg_path)), exist_ok=True)
            with open(out_svg_path, "w", encoding="utf-8") as f:
                f.write(svg_code + "\n")
            cairosvg.svg2png(bytestring=svg_code.encode("utf-8"), write_to=out_png_path, dpi=180)
        except Exception as e:
            issues = [f"SVG 提取或 CairoSVG 渲染异常: {e}"]
            svg_code = ""

        logs.append(
            {
                "attempt": attempt,
                "meta": meta,
                "issues": issues,
                "passed": len(issues) == 0,
            }
        )
        final_svg = svg_code

        if len(issues) == 0:
            break
        feedback = "\n".join(f"- {it}" for it in issues)
        print(f"    [SVG 画师几何自检拦截 第{attempt}轮]\n{feedback}")

    return {
        "svg_path": out_svg_path,
        "png_path": out_png_path,
        "attempts": logs,
        "svg_length": len(final_svg),
    }
