#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邱关源《电路》四步闭环智能出题与配图 Agent (agent.py)
架构流水线：
  Step 1 [Planner]         : 章节正交抽样与拓扑难度梯度规划（破除“首章纯电阻坍缩”）
  Step 2 [SymPy & SVG]     : 参数化拓扑绑定、SymPy 符号精确求解凑整、国标 SVG/PNG 渲染（解除“画图锁死难度”）
  Step 3 [Question Writer] : 基于 SymPy Ground-Truth 驱动 DeepSeek 撰写真题题干、定量陷阱设问与分步解析
  Step 4 [Critic Loop]     : 硬规则 + LLM 教研主任红队联合审题，不达标自动打回重写
"""

import os
import json
import time
from typing import Dict, Any, List
from circuit_templates import get_exam_templates_for_stu001, export_template_graphics
from critic import call_deepseek, audit_exam

RAW_REQUIREMENT = (
    "stu_001, 出 3道题；难度比例：1：1：1；"
    "习题范围：普通的电阻电路分析、电路定理、二端口、正弦稳态电路、三相电路、耦合电路、谐振、"
    "周期非正弦、暂态（一阶电路、二阶电路）、滤波器、均匀传输线、图论；"
    "参考教材：邱关源《电路》；"
    "题目要求：简单题需≥2步计算、中等题含多考点+隐性陷阱、难题跨模块+概念误导+定理前提甄别，"
    "每个题目要带图；例如出电路定理支路上完全可以加受控源，而不是简单图。"
)


def build_writer_messages(templates: List[Dict[str, Any]], feedback: str = "") -> List[Dict[str, str]]:
    spec_list = []
    for idx, tpl in enumerate(templates, start=1):
        spec_list.append(
            {
                "question_no": idx,
                "image_markdown": f"![题{idx}图](q{idx}.png)",
                "svg_file": f"q{idx}.svg",
                "difficulty": tpl["difficulty"],
                "module": tpl["module"],
                "topology_description": tpl.get("topology_description", ""),
                "parameters": tpl["parameters"],
                "sympy_equations": tpl.get("sympy_equations", []),
                "sympy_ground_truth": tpl["ground_truth"],
            }
        )

    system_prompt = (
        "你是高等教育出版社《电路》（邱关源 主编）教材编写组的核心命题专家。\n"
        "请根据给定的 3 个已完成 SymPy 严格数学验算与标准 SVG 电路图渲染的拓扑蓝图，为学生 `stu_001` 编写一份高质量、严谨、排版精美的 Markdown 试卷（含题干、配图引用、设问、命题设计意图/陷阱剖析、以及标准分步解析）。\n\n"
        "【铁律要求】\n"
        "1. 题干中必须将 `topology_description` 中的电路连接关系和元件参数完整、清晰地写入题干正文，使读者结合配图 `![题X图](qX.png)` 没有任何歧义；\n"
        "2. 严禁在解析中打草稿、试错或出现“按GT锁定”等字眼！请直接按照 `sympy_equations` 中经过严格符号验算的 KCL/KVL 方程写出流畅、自洽、一步到位的教材级标准解析，全文保持精炼紧凑（总长度控制在 2200~3000 字以内，确保第 3 题完整收尾绝不截断）；\n"
        "3. 每道题必须在题干下方紧跟对应的图片引用：`![题1图](q1.png)`、`![题2图](q2.png)`、`![题3图](q3.png)`；\n"
        "4. 严禁出现“某同学认为……对不对/是否正确”这种低幼、应付式的独立送分文字判断题！所有概念误导与定理前提甄别必须化入硬核的定量计算设问（按 `sympy_equations` 中的三问结构编写）；\n"
        "5. 公式统一使用标准 LaTeX 数学公式（`$...$` 与 `$$...$$`），排版清晰优雅。"
    )

    user_content = (
        f"【原始出题需求】\n{RAW_REQUIREMENT}\n\n"
        f"【Planner 锁定的三道题参数与 SymPy 权威 Ground-Truth】\n"
        f"{json.dumps(spec_list, ensure_ascii=False, indent=2)}\n"
    )
    if feedback:
        user_content += f"\n【上一轮教研主任红队打回修改意见（请务必修正）】\n{feedback}\n"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def run_agent_pipeline(max_retries: int = 2) -> Dict[str, Any]:
    t_start = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, "examples")
    os.makedirs(out_dir, exist_ok=True)

    print("======================================================================")
    print("Step 1 & 2: 启动 Planner 章节解耦 + SymPy 符号求解 + 国标 SVG/PNG 渲染")
    print("======================================================================")
    templates = get_exam_templates_for_stu001()
    exported_imgs = export_template_graphics(templates, out_dir)
    for idx, (tpl, img) in enumerate(zip(templates, exported_imgs), start=1):
        print(f"  [题{idx} | {tpl['difficulty']}] {tpl['module']}")
        print(f"     -> SVG: {img['svg']} | PNG: {img['png']}")

    iterations_log: List[Dict[str, Any]] = []
    feedback = ""
    final_exam_md = ""
    final_audit: Dict[str, Any] = {}

    for attempt in range(1, max_retries + 1):
        print(f"\n======================================================================")
        print(f"Step 3: 调用 DeepSeek Question Writer 撰写试卷 (第 {attempt} 轮)")
        print("======================================================================")
        messages = build_writer_messages(templates, feedback=feedback)
        exam_md, writer_meta = call_deepseek(messages, temperature=0.25, max_tokens=4096)
        print(f"  [Writer 完成] 耗时 {writer_meta['elapsed_sec']}s, Tokens: {writer_meta['total_tokens']}")

        print(f"\n======================================================================")
        print(f"Step 4: 调用 Critic 教研主任红队审题器审查 (第 {attempt} 轮)")
        print("======================================================================")
        audit_res = audit_exam(exam_md, templates=templates, use_llm=True)
        hard_passed = audit_res["hard_rules"]["passed"]
        llm_rev = audit_res["llm_review"] or {}
        llm_score = llm_rev.get("overall_score", 0)
        print(f"  [Critic 结论] Final Passed: {audit_res['final_passed']} | 硬规则: {hard_passed} | LLM 教研评分: {llm_score}/100")

        iterations_log.append(
            {
                "attempt": attempt,
                "writer_meta": writer_meta,
                "audit": audit_res,
            }
        )
        final_exam_md = exam_md
        final_audit = audit_res

        if audit_res["final_passed"]:
            print("  ✅ 试卷通过全部硬规则与教研主任红队审查！")
            break
        else:
            violations_str = "; ".join(audit_res["hard_rules"]["violations"])
            rev_instr = llm_rev.get("revision_instructions", "")
            feedback = f"硬规则违规：{violations_str}\n教研主任修改意见：{rev_instr}"
            print(f"  ⚠️ 触发红队拦截，准备打回重写：{feedback}")

    exam_path = os.path.join(out_dir, "stu_001_exam.md")
    with open(exam_path, "w", encoding="utf-8") as f:
        f.write(final_exam_md.strip() + "\n")

    log_data = {
        "student_id": "stu_001",
        "raw_requirement": RAW_REQUIREMENT,
        "total_elapsed_sec": round(time.time() - t_start, 2),
        "templates_and_sympy_ground_truth": [
            {
                "id": t["id"],
                "difficulty": t["difficulty"],
                "module": t["module"],
                "parameters": t["parameters"],
                "ground_truth": t["ground_truth"],
                "svg_file": f"examples/q{i}.svg",
                "png_file": f"examples/q{i}.png",
            }
            for i, t in enumerate(templates, start=1)
        ],
        "iterations": iterations_log,
        "final_passed": final_audit.get("final_passed", False),
    }
    log_path = os.path.join(out_dir, "run_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"\n[Done] 最终试卷已导出至: {exam_path}")
    print(f"[Done] 完整运行日志已导出至: {log_path}")
    return log_data


if __name__ == "__main__":
    run_agent_pipeline()
