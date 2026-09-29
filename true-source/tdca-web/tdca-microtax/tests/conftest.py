# -*- coding: utf-8 -*-
"""测试基座注入：复用 CALL-RULES TaxRates（顶层导入惯例，同 tdca-call-rules/tests）。"""
import sys
from pathlib import Path

# tdca-microtax 包根（本文件位于 tdca-microtax/tests/）
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 复用基座: tdca-call-rules/engine（TaxRates/CallType）
CALL_RULES_ENGINE = ROOT.parent / "tdca-call-rules" / "engine"
if CALL_RULES_ENGINE.exists():
    sys.path.insert(0, str(CALL_RULES_ENGINE))

# 复用基座: tdca-fos/tdca_adapters（MOUPipeline/SimulatedTaxAuthority——M-3 集成用）
FOS_ADAPTERS = ROOT.parent / "tdca-fos" / "tdca_adapters"
if FOS_ADAPTERS.exists():
    sys.path.insert(0, str(FOS_ADAPTERS))

# 复用基座: tdca-translator-market（MOUSplitContract/default_mou_value_fn——M-3 Shapley 数学）
TRANSLATOR_MARKET = ROOT.parent / "tdca-translator-market"
if TRANSLATOR_MARKET.exists():
    sys.path.insert(0, str(TRANSLATOR_MARKET))

# 复用基座: tdca-nsfl-compiler（tax_regulations——TAXLAW-001 法规决策依据）
NSFL_COMPILER = ROOT.parent / "tdca-nsfl-compiler"
if NSFL_COMPILER.exists():
    sys.path.insert(0, str(NSFL_COMPILER))

# 复用基座: tdca-ns-runtime（static_list——L1-R1 静态清单 TAXLAW-001 L-1）
NS_RUNTIME = ROOT.parent / "tdca-ns-runtime"
if NS_RUNTIME.exists():
    sys.path.insert(0, str(NS_RUNTIME))

# 复用基座: tdca-toolchain（cognitive_distance——COGNITION-001 C-1 多主体认知）
TOOLCHAIN = ROOT.parent / "tdca-toolchain"
if TOOLCHAIN.exists():
    sys.path.insert(0, str(TOOLCHAIN))

# 复用基座: tdca-utility-genie（positive_sum_solver——COGNITION-001 C-2 效用精灵）
UTILITY_GENIE = ROOT.parent / "tdca-utility-genie"
if UTILITY_GENIE.exists():
    sys.path.insert(0, str(UTILITY_GENIE))
