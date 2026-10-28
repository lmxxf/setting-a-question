#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邱关源《电路》参数化拓扑与 ASCII 草图库 + SymPy 符号求解器 (circuit_templates.py)
注意：本模块只负责提供【拓扑参数 + SymPy 严格符号求解 + ASCII 电路拓扑草图】，
所有的 SVG/PNG 图形均由 `ascii_to_svg.py` 调用 DeepSeek 专职画师根据 ASCII 草图自主生成！
"""

from typing import Dict, Any, List
import sympy as sp


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

    ascii_diagram = r"""
           R1 = 6 Ω         节点 A        R3 = 4 Ω                   a
    +------[ 6 Ω ]------------●-----------[ 4 Ω ]-----------●--------o - - - - +
    |                         |                             |                  |
    |                         | I1 (↓)                      |                  |
   (+)                        v                            / \                 |
  ( Us ) 36 V              [ R2 ] 12 Ω                    < ↑ > 1·I1 (CCCS)  [ RL ] (可变负载)
   (−)                        |                            \ /                 |
    |                         |                             |                  |
    +-------------------------●-----------------------------●--------o - - - - +
                              |                                      b
                             === (GND)
    """

    return {
        "id": "q1_thevenin_dependent",
        "figure_title": "题 1 图：含受控电流源（CCCS）的线性有源一端口网络",
        "difficulty": "简单",
        "module": "第4章 电路定理（含受控源网络的戴维南定理与最大功率传输）",
        "ascii_diagram": ascii_diagram.strip(),
        "topology_description": (
            "左侧独立电压源 U_s = 36 V（上正下负，下端接参考地 b）串联电阻 R_1 = 6 Ω 接至节点 A；"
            "节点 A 与参考地 b 之间接电阻 R_2 = 12 Ω，流过 R_2 从 A 向下的电流定义为控制量 I_1；"
            "节点 A 向右串联电阻 R_3 = 4 Ω 到达输出端口上端钮 a；"
            "在输出端钮 a 与参考地端钮 b 之间，并联一个方向由 b 指向 a（向上注入节点 a）的受控电流源（CCCS，菱形符号），其电流大小为 1·I_1；"
            "端口 a-b 外接可变负载电阻 R_L（虚线连接）。"
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
    uC_wrong_num = int(uC_wrong_num if isinstance(uC_0_wrong, int) else uC_0_wrong.subs(subs_map))
    Req_num = int(Req_expr.subs(subs_map))
    Req_wrong_num = int(Req_wrong.subs(subs_map))
    tau_num = int(tau_expr.subs(subs_map))
    iC_0p_num = int(-sp.Rational(uC_0_num, Req_num))
    ix_0p_num = -iC_0p_num

    ascii_diagram = r"""
           R1 = 4 Ω     S (t=0 断开)   节点 A      R3 = 4 Ω        2ix (VCVS)     节点 B
    +------[ 4 Ω ]------o  /  o---------●---------[ 4 Ω ]--------< −   + >---------●-------+
    |                                   |                                                  |
    |                                   | ix (↓)                                           | iC(t) (↓)
   (+)                                  v                                               +  v
  ( Us ) 30 V                         [ R2 ] 6 Ω                                   uC(t) ===== C = 0.25 F
   (−)                                  |                                               -  |
    |                                   |                                                  |
    +-----------------------------------●--------------------------------------------------+
                                        |
                                       === (GND)
    """

    return {
        "id": "q2_first_order_transient",
        "figure_title": "题 2 图：含受控电压源（VCVS）的一阶 RC 换路暂态电路",
        "difficulty": "中等",
        "module": "第7章 一阶电路的时域分析（换路定则 + 含受控源戴维南等效时间常数 + 三要素法）",
        "ascii_diagram": ascii_diagram.strip(),
        "topology_description": (
            "左侧独立直流电压源 U_s = 30 V（上正下负，下端接参考地）串联电阻 R_1 = 4 Ω 与开关 S（t < 0 时闭合，t = 0 时断开）接至节点 A；"
            "节点 A 到参考地接电阻 R_2 = 6 Ω，流过 R_2 向下的电流定义为控制量 i_x；"
            "节点 A 向右依次串联电阻 R_3 = 4 Ω 与受控电压源 VCVS（菱形符号，极性为左 − 右 +，电压大小为 2i_x，控制系数 r = 2 Ω）到达节点 B；"
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
    }


# ==============================================================================
# 模板 3（难题 Hard）：含受控源非互易二端口网络与双电源综合分析（第 16 章 二端口 + 第 4 章 定理甄别）
# ==============================================================================
def build_template_two_port_cascade() -> Dict[str, Any]:
    I1, I2 = sp.symbols("I1 I2", real=True)
    R1_val, R2_val, R3_val, alpha_val = 2, 4, 2, 4
    Us1_val, Rs_val, Is2_val, RL_val = 32, 2, 8, 6

    Z11 = R1_val + R2_val
    Z12 = R2_val
    Z21 = R2_val + alpha_val
    Z22 = R2_val + R3_val

    eq1 = sp.Eq(Us1_val - Rs_val * I1, Z11 * I1 + Z12 * I2)
    eq2 = sp.Eq(RL_val * (Is2_val - I2), Z21 * I1 + Z22 * I2)
    sol_both = sp.solve([eq1, eq2], (I1, I2))
    I1_both = int(sol_both[I1])
    I2_both = int(sol_both[I2])
    IL_both = int(Is2_val - I2_both)
    UL_both = int(RL_val * IL_both)
    PL_both = int(RL_val * (IL_both**2))

    eq2_wrong_recip = sp.Eq(RL_val * (Is2_val - I2), Z12 * I1 + Z22 * I2)
    sol_wrong_recip = sp.solve([eq1, eq2_wrong_recip], (I1, I2))
    UL_wrong_recip = sp.simplify(RL_val * (Is2_val - sol_wrong_recip[I2]))

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

    ascii_diagram = r"""
                        + - - - - [ 含受控源线性二端口网络 N ] - - - - +
         Rs = 2 Ω   I1  |    R1 = 2 Ω       节点 M   R3 = 2 Ω   4I1    |   I2
    +----[ 2 Ω ]--->--o 1 ---[ 2 Ω ]---------●------[ 2 Ω ]---< − + >--o 2 --<--+----------+
    |                   |                    |                         |        |          |
   (+)                  |                    |                         |       (↑)         | IL (↓)
  (Us1) 32 V            |                 [ R2 ] 4 Ω                   |      (Is2) 8 A  [ RL ] 6 Ω
   (−)                  |                    |                         |       ( )         |
    |                   |                    |                         |        |          |
    +-----------------o 1'-------------------●-------------------------o 2'-----+----------+
                        + - - - - - - - - - - - - - - - - - - - - - - -+
    """

    return {
        "id": "q3_two_port_cascade",
        "figure_title": "题 3 图：含受控源非互易二端口网络 N 与双端有源外电路",
        "difficulty": "困难",
        "module": "第16章 二端口网络 + 第4章 电路定理前提甄别（非互易二端口Z参数 + 互易定理失效甄别 + 双源叠加与功率不可叠加定量分析）",
        "ascii_diagram": ascii_diagram.strip(),
        "topology_description": (
            "虚线框内为含受控源的线性二端口网络 N（左端口 1-1'，右端口 2-2'，1'-2' 为底部直通公共参考端，标准参考方向：I_1 从端钮 1 流入，I_2 从端钮 2 流入）："
            "二端口内部由 T 型网络构成：端钮 1 串联 R_1 = 2 Ω 到内部节点 M；节点 M 到公共底线接 R_2 = 4 Ω；节点 M 向右串联 R_3 = 2 Ω 与受控电压源 VCVS（菱形符号，极性左 − 右 +，电压为 4I_1）到达端钮 2。"
            "外部电路：端口 1-1' 外接独立电压源 U_s1 = 32 V（上正下负）串联内阻 R_s = 2 Ω；端口 2-2' 外接独立电流源 I_s2 = 8 A（方向由 2' 向上指向 2）与负载电阻 R_L = 6 Ω 并联（设流过 R_L 向下的负载电流为 I_L，负载电压 U_L = U_2 上正下负）。"
        ),
        "sympy_equations": [
            "第(1)问 求 Z 参数与互易定理甄别：对内部 T 型网络列 KVL（受控源 4I_1 左 − 右 +，使端钮 2 电位比节点 M 进一步升高 4I_1），U_1 = R_1*I_1 + R_2*(I_1 + I_2) = 6*I_1 + 4*I_2；U_2 = R_2*(I_1 + I_2) + 4*I_1 + R_3*I_2 = 8*I_1 + 6*I_2。故 Z = [[6, 4], [8, 6]] Ω（Z_11 = 6 Ω, Z_12 = 4 Ω, Z_21 = 8 Ω, Z_22 = 6 Ω）。因 Z_12 = 4 Ω != Z_21 = 8 Ω，该二端口不满足互易定理！（若误按互易定理令 Z_21 = Z_12 = 4 Ω，联立外电路会算出错误负载电压 U_L_wrong = 144/5 = 28.8 V）。",
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
    }


def get_exam_templates_for_stu001() -> List[Dict[str, Any]]:
    return [
        build_template_thevenin_dependent(),
        build_template_first_order_transient(),
        build_template_two_port_cascade(),
    ]
