#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教研主任红队自动审题器 (Critic) + DeepSeek API 客户端
包含：硬规则检查（模块覆盖、高阶元件、反低幼判断题、图文与SymPy数值一致性） + LLM 教研室主任深度审查
"""

import os
import re
import json
import time
from typing import Dict, Any, List, Tuple
import requests


def load_env(env_path: str = None) -> Dict[str, str]:
    if env_path is None:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
                os.environ[k.strip()] = env_vars[k.strip()]
    return env_vars


def call_deepseek(
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 8192,
    response_json: bool = False,
) -> Tuple[str, Dict[str, Any]]:
    load_env()
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    if not api_key:
        raise RuntimeError("未检测到 DEEPSEEK_API_KEY，请检查 .env 文件！")

    url = f"{base_url}/chat/completions" if not base_url.endswith("/v1") else f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}

    t0 = time.time()
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    elapsed = round(time.time() - t0, 2)
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    meta = {
        "model": model,
        "elapsed_sec": elapsed,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }
    return content, meta


def run_hard_rules(exam_md: str, templates: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    执行四项硬性教研规则审查：
    1. 章节模块覆盖度（杜绝全篇坍缩为第1章纯直流无源电阻）
    2. 高阶电路图元检查（受控源、动态换路元件L/C/S、二端口/互感）
    3. 反偷懒式送分问答检查（拦截“某同学认为……对不对/是否正确”低幼文字判断题）
    4. 图文参数与 SymPy Ground-Truth 100% 数值一致性核对
    """
    violations: List[str] = []
    checks: Dict[str, bool] = {}

    # 规则 1：模块覆盖度
    has_theorem = any(w in exam_md for w in ["戴维南", "Thevenin", "等效内阻", "最大功率"])
    has_transient = any(w in exam_md for w in ["换路", "时间常数", "暂态", "0_+", "0_-", "0+", "0-", "三要素"])
    has_twoport_or_ac = any(w in exam_md for w in ["二端口", "Z参数", "阻抗参数", "互易", "耦合", "谐振"])
    checks["module_diversity"] = has_theorem and has_transient and has_twoport_or_ac
    if not checks["module_diversity"]:
        violations.append(
            f"【规则1-章节坍缩拦截】未覆盖完整的跨模块组合（定理={has_theorem}, 暂态={has_transient}, 二端口/交流={has_twoport_or_ac}）。"
        )

    # 规则 2：高阶元件存在性
    has_dependent_src = any(w in exam_md for w in ["受控", "CCCS", "VCVS", "4I_1", "4I₁", "2i_x", "2iₓ", "1·I_1", "1·I₁"])
    has_dynamic_elem = any(w in exam_md for w in ["开关", "0.25 F", "0.25F", "电容", "电感"])
    checks["advanced_components"] = has_dependent_src and has_dynamic_elem
    if not checks["advanced_components"]:
        violations.append(
            f"【规则2-高阶元件缺失】缺少受控源或动态储能/换路元件（受控源={has_dependent_src}, 动态元件={has_dynamic_elem}）。"
        )

    # 规则 3：拦截“某同学认为……对不对”式低幼文字判断题
    lazy_patterns = [
        r"某同学认为.{0,60}(对不对|是否正确|对吗|是否成立\？)",
        r"小[明王李张]认为.{0,60}(对不对|是否正确|对吗)",
        r"请判断.{0,30}同学.{0,20}是否正确",
    ]
    lazy_hits = []
    for pat in lazy_patterns:
        m = re.search(pat, exam_md)
        if m:
            lazy_hits.append(m.group(0))
    checks["no_lazy_true_false_question"] = len(lazy_hits) == 0
    if lazy_hits:
        violations.append(
            f"【规则3-低幼送分问答题拦截】检测到应付式文字判断题：{lazy_hits}。必须将定理前提甄别化入定量数值计算！"
        )

    # 规则 4：图文与 SymPy Ground-Truth 关键数值核对
    if templates is not None:
        required_anchors = [
            ("题1", ["36", "48", "12"]),
            ("题2", ["30", "0.25", "24", "12", "3"]),
            ("题3", ["32", "8", "36", "216", "120"]),
        ]
        missing_nums = []
        for q_tag, nums in required_anchors:
            for num in nums:
                if num not in exam_md:
                    missing_nums.append(f"{q_tag}缺失关键数值:{num}")
        checks["sympy_ground_truth_aligned"] = len(missing_nums) == 0
        if missing_nums:
            violations.append(f"【规则4-SymPy数值不一致】{', '.join(missing_nums)}")
    else:
        checks["sympy_ground_truth_aligned"] = False

    return {
        "passed": len(violations) == 0,
        "checks": checks,
        "violations": violations,
    }


def run_llm_critic(exam_md: str, templates: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    调用 DeepSeek 扮演高校《电路》课程教研主任，对生成的试题与解析进行红队评审
    """
    gt_summary = [
        {
            "id": t["id"],
            "difficulty": t["difficulty"],
            "module": t["module"],
            "topology_description": t.get("topology_description", ""),
            "parameters": t["parameters"],
            "sympy_equations": t.get("sympy_equations", []),
            "ground_truth": t["ground_truth"],
        }
        for t in templates
    ]
    system_prompt = (
        "你是国家级精品课程《电路》（邱关源教材）的教研室主任、红队审题专家。\n"
        "请严格审查输入的 3 道电路试题（含题干、设问与标准解析），对照给定的 SymPy 符号计算 Ground-Truth，以 JSON 格式输出审查报告。\n"
        "审查标准：\n"
        "1. 章节广度与梯度：3 道题是否严格满足 1:1:1（简单/中等/困难），且分别覆盖不同章节，杜绝纯直流无源电阻退化；\n"
        "2. 陷阱设计高级感：中等题和难题的隐性陷阱、定理前提甄别（如受控源不可置零、开路支路中受控电压源仍有电压、非互易二端口 Z12!=Z21、双电源叠加时功率不可直接相加且求出交叉项差值）是否完全融入定量计算设问，杜绝“某同学认为……对不对”式低幼文字问答；\n"
        "3. 图文与数值精确度：题干参数、节点名称、最终计算结果是否与 SymPy Ground-Truth 完全一致。\n"
        "请返回如下 JSON 结构：\n"
        "{\n"
        '  "passed": true 或 false,\n'
        '  "overall_score": 0到100的整数,\n'
        '  "dimension_scores": {"module_diversity": 0-25, "trap_depth": 0-25, "math_accuracy": 0-25, "diagram_alignment": 0-25},\n'
        '  "question_reviews": [\n'
        '    {"question": 1, "verdict": "PASS/FAIL", "comment": "具体点评"},\n'
        '    {"question": 2, "verdict": "PASS/FAIL", "comment": "具体点评"},\n'
        '    {"question": 3, "verdict": "PASS/FAIL", "comment": "具体点评"}\n'
        "  ],\n"
        '  "revision_instructions": "若不通过请给出具体重写指令，若通过填空字符串"\n'
        "}"
    )
    user_prompt = (
        f"【SymPy 权威 Ground-Truth 与拓扑参数】\n{json.dumps(gt_summary, ensure_ascii=False, indent=2)}\n\n"
        f"【待审试卷全文】\n{exam_md}"
    )
    raw_json, meta = call_deepseek(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_json=True,
    )
    parsed = json.loads(raw_json)
    return parsed, meta


def audit_exam(exam_md: str, templates: List[Dict[str, Any]] = None, use_llm: bool = True) -> Dict[str, Any]:
    hard_res = run_hard_rules(exam_md, templates)
    result: Dict[str, Any] = {
        "hard_rules": hard_res,
        "llm_review": None,
        "llm_meta": None,
        "final_passed": hard_res["passed"],
    }
    if use_llm and templates is not None:
        llm_res, llm_meta = run_llm_critic(exam_md, templates)
        result["llm_review"] = llm_res
        result["llm_meta"] = llm_meta
        result["final_passed"] = hard_res["passed"] and bool(llm_res.get("passed", False))
    return result
