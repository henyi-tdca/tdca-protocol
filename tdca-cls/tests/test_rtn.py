"""RTN 净额测试（R-CLS-2：P3*=T_net 闭式验证）"""
import numpy as np
import pytest
from scipy.optimize import linprog

from tdca_cls.rtn import RTNNetting


def p3_lp(D):
    """现金约束模型 P3 的 LP 最优值（独立验证）"""
    n = D.shape[0]
    N = D.sum(axis=0) - D.sum(axis=1)
    nv = n * n + 2 * n
    c = np.zeros(nv)
    c[n * n:n * n + n] = 1
    A_eq = np.zeros((n, nv))
    for i in range(n):
        for j in range(n):
            A_eq[i, n * i + j] -= 1
            A_eq[i, n * j + i] += 1
        A_eq[i, n * n + i] = 1
        A_eq[i, n * n + n + i] = -1
    b_eq = -N
    A_ub = np.zeros((n, nv))   # 现金约束: sum_j x_ij - y_i <= 0
    for i in range(n):
        for j in range(n):
            A_ub[i, n * i + j] = 1
        A_ub[i, n * n + i] = -1
    b_ub = np.zeros(n)
    bounds = [(0, None)] * nv
    for i in range(n):
        for j in range(n):
            bounds[n * i + j] = (0, D[i, j])
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    assert res.success
    return res.fun


def test_rtn_tnet_equals_p3_random():
    """100 随机矩阵: T_net == P3*（LP 独立验证）"""
    rng = np.random.default_rng(42)
    netting = RTNNetting()
    for _ in range(100):
        n = int(rng.integers(2, 9))
        D = rng.integers(0, 20, size=(n, n)).astype(float)
        np.fill_diagonal(D, 0)
        nodes = [f"N{i}" for i in range(n)]
        debt = {}
        for i in range(n):
            for j in range(n):
                if D[i, j] > 0:
                    debt[(nodes[i], nodes[j])] = float(D[i, j])
        r = netting.net(nodes, debt)
        assert abs(r.t_net - p3_lp(D)) < 1e-6, f"T_net={r.t_net} vs P3*={p3_lp(D)}"


def test_rtn_ring_case():
    """环案例: A欠B10/B欠C10/C欠A5 → T_net=5"""
    netting = RTNNetting()
    debt = {("A", "B"): 10.0, ("B", "C"): 10.0, ("C", "A"): 5.0}
    r = netting.net(["A", "B", "C"], debt)
    assert r.t_net == pytest.approx(5.0)
    assert r.t_full == pytest.approx(25.0)
    assert r.utilization == pytest.approx(1 - 5 / 25)
    # 净额定向支付总额 = T_net
    total = sum(a for _, _, a in r.payment_orders)
    assert total == pytest.approx(5.0)


def test_rtn_conservation():
    """守恒: ΣN_i = 0 → 净应付总额 = 净应收总额"""
    netting = RTNNetting()
    debt = {("A", "B"): 30.0, ("B", "C"): 20.0, ("C", "A"): 5.0, ("A", "C"): 5.0}
    r = netting.net(["A", "B", "C"], debt)
    assert abs(sum(r.net_positions.values())) < 1e-9
    payers = sum(a for _, _, a in r.payment_orders)
    assert payers == pytest.approx(r.t_net)
