"""
TDCA-FC-20260802-004 修正声明: 无（首版）
制度锚定: ID24（效用精灵九大数学能力-贝叶斯）
Granted-By: ID24

NSFL-Declaration:
  - 贝叶斯推理不替代真实观测，后验更新需真实数据
  - 置信区间必须明确标注
SPDX-License-Identifier: TDCA-Internal
"""

import math
from typing import List, Optional, Tuple


class BayesianEngine:
    """
    贝叶斯引擎（九大能力-贝叶斯推理）

    支持:
      - 正态分布后验更新（共轭先验）
      - 置信区间计算
      - 代理模型（高斯过程简化版）
    """

    def __init__(self):
        pass

    def normal_posterior(
        self,
        prior_mean: float,
        prior_variance: float,
        observations: List[float],
        observation_variance: float = 1.0
    ) -> dict:
        """
        正态-正态共轭后验更新。
        返回: {'mean': float, 'variance': float, 'posterior_samples': [...]}
        """
        n = len(observations)
        if n == 0:
            return {'mean': prior_mean, 'variance': prior_variance, 'posterior_samples': []}

        obs_mean = sum(observations) / n
        # 后验方差 = 1 / (1/prior_var + n/obs_var)
        post_var = 1.0 / (1.0 / prior_variance + n / observation_variance)
        # 后验均值 = post_var * (prior_mean/prior_var + n*obs_mean/obs_var)
        post_mean = post_var * (prior_mean / prior_variance + n * obs_mean / observation_variance)

        return {
            'mean': post_mean,
            'variance': post_var,
            'posterior_samples': self._sample(post_mean, post_var, 100),
            'n_observations': n,
        }

    def confidence_interval(self, mean: float, variance: float, level: float = 0.95) -> Tuple[float, float]:
        """正态分布置信区间（近似 1.96σ 对应 95%，scipy 不可用时用近似 z 值）"""
        z = 1.96
        try:
            from scipy.stats import norm
            z = norm.ppf((1 + level) / 2)
        except ImportError:
            z = 1.96 if level >= 0.95 else 1.645
        std = math.sqrt(variance)
        return (mean - z * std, mean + z * std)

    def expected_improvement(self, current_best: float, pred_mean: float, pred_var: float) -> float:
        """EI 采集函数（贝叶斯优化的勘探-开发平衡）"""
        std = math.sqrt(pred_var)
        if std == 0:
            return 0.0
        try:
            from scipy.stats import norm
            z = (current_best - pred_mean) / std
            ei = (current_best - pred_mean) * norm.cdf(z) + std * norm.pdf(z)
        except ImportError:
            # 简化 EI
            delta = current_best - pred_mean
            ei = max(0.0, delta) + 0.5 * std
        return float(ei)

    @staticmethod
    def _sample(mean: float, variance: float, n: int) -> List[float]:
        """从正态分布采样（Box-Muller）"""
        import random
        std = math.sqrt(variance)
        samples = []
        for _ in range(n):
            u1 = random.random()
            u2 = random.random()
            z = math.sqrt(-2 * math.log(max(u1, 1e-12))) * math.cos(2 * math.pi * u2)
            samples.append(mean + std * z)
        return samples
