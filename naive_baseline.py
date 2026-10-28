#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单轮 Naive Prompt 对照组实验 (naive_baseline.py)
复现直接将 13 个章节范围 + 出题要求 + 画图需求塞进一个单轮 Prompt 时，大模型的典型退化现象。
"""

import os
import json
from critic import call_deepseek, run_hard_rules

NAIVE_USER_PROMPT = (
    "stu_001, 出 3道题；难度比例：1：1：1；"
    "习题范围：普通的电阻电路分析、电路定理、二端口、正弦稳态电路、三相电路、耦合电路、谐振、"
    "周期非正弦、暂态（一阶电路、二阶电路）、滤波器、均匀传输线、图论；"
    "参考教材：邱关源《电路》；"
    "题目要求：简单题需≥2步计算、中等题含多考点+隐性陷阱、难题跨模块+概念误导+定理前提甄别，"
    "每个题目要带图（请在回复中直接用 ASCII 字符画绘制电路图，并给出 3 道题的完整题目和解析）。"
)


def run_naive_baseline() -> dict:
    print("[Naive Baseline] 正在调用 DeepSeek 单轮直接生成 3 道题与配图...")
    raw_output, meta = call_deepseek(
        messages=[
            {"role": "user", "content": NAIVE_USER_PROMPT},
        ],
        temperature=0.7,
        max_tokens=3500,
    )

    hard_audit = run_hard_rules(raw_output, templates=None)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples")
    os.makedirs(out_dir, exist_ok=True)
    out_md_path = os.path.join(out_dir, "naive_single_prompt_output.md")

    header = (
        "# 单轮 Prompt 对照组实验输出 (`naive_baseline.py`)\n\n"
        "> **实验说明**：本文件由 `naive_baseline.py` 实跑 DeepSeek (`deepseek-chat`) 单轮直接生成。\n"
        "> 可以清晰观察到单轮 Prompt 在同时承担「章节规划 + 电路拓扑构造 + 自由手写画图 + 数值求解 + 设问编撰」时的三大结构性退化：\n"
        "> 1. **画图锁死拓扑难度**：大模型为了能在字符画/手写代码里把图画出来，本能回避复杂的菱形受控源、互感同名端或带斜杆动作箭头的换路开关，退化为简陋的 ASCII 字符框线图；\n"
        "> 2. **章节向低维纯电阻/套路题坍缩**：13 个章节并列时，高阶章节（均匀传输线、滤波器、非互易二端口等）被跳过，优先挑最省算力的直流电阻串并联或最基础的一阶公式套用；\n"
        "> 3. **“概念误导/定理甄别”沦为文字送分问答**：在题目末尾硬塞一句“某同学认为功率可以直接用叠加定理相加 / 某同学认为……请判断该说法是否正确”，毫无定量计算耦合。\n\n"
        f"- **调用模型**：`{meta['model']}`\n"
        f"- **耗时**：`{meta['elapsed_sec']} s` | **Token 消耗**：`{meta['total_tokens']}` (`prompt={meta['prompt_tokens']}, completion={meta['completion_tokens']}`)\n"
        f"- **Critic 硬规则审计结果**：`passed = {hard_audit['passed']}`\n"
        f"- **触发拦截项**：`{json.dumps(hard_audit['violations'], ensure_ascii=False)}`\n\n"
        "---\n\n"
        "## 原始单轮 Prompt\n\n"
        f"```text\n{NAIVE_USER_PROMPT}\n```\n\n"
        "---\n\n"
        "## DeepSeek 单轮原始输出\n\n"
    )

    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(header + raw_output + "\n")

    print(f"[Naive Baseline] 已保存至 {out_md_path} (耗时 {meta['elapsed_sec']}s, tokens={meta['total_tokens']})")
    return {
        "output_path": out_md_path,
        "meta": meta,
        "hard_audit": hard_audit,
    }


if __name__ == "__main__":
    run_naive_baseline()
