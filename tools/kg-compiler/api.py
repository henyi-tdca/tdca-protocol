"""
TDCA-FC-20260803-005 FastAPI 服务
制度锚定: FC-005-SPEC §4 接口契约
Granted-By: FC-005-SPEC

NSFL-Declaration:
  - 所有接口调用需配置权 Token 验证
  - 外部数据接入需负空间检查
  - 敏感领域需额外审批标记
SPDX-License-Identifier: Apache-2.0
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tdca_kg_compiler import TDCAKnowledgeGraphCompiler

try:
    from fastapi import FastAPI, Header, HTTPException
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# ---- 鉴权（LIM-004: 委托 FC-002 验证，独立于 FastAPI 可用性） ----

# 生产环境注入 FC-002 验证客户端
_fc002_validator = None


def _set_fc002_validator(validator):
    """注入 FC-002 配置权验证客户端（validate_token(token) -> dict）"""
    global _fc002_validator
    _fc002_validator = validator


def _check_auth(token: str):
    """配置权 Token 验证

    LIM-004: 委托 FC-002 ConfigRightTokenGenerator 验证接口，
    检查 valid / expired / puf_bound，API 层不自行实现验证逻辑。
    """
    if not token:
        raise _http_exception(401, "缺少配置权 Token")

    if _fc002_validator is not None:
        # 生产路径：委托 FC-002
        try:
            validation = _fc002_validator.validate_token(token)
        except Exception as e:
            raise _http_exception(503, f"FC-002 验证服务异常: {e}")
        if not validation.get('valid', False):
            raise _http_exception(401, "Token 无效")
        if validation.get('expired', False):
            raise _http_exception(401, "Token 已过期")
        if not validation.get('puf_bound', True):
            raise _http_exception(401, "Token 未绑定 PUF")
    else:
        # 开发路径：简化前缀检查（V1.1.0 过渡，生产必须注入 FC-002）
        if not token.startswith('TDCA-CRT-'):
            raise _http_exception(401, "无效配置权 Token")


class TDCAHttpError(Exception):
    """模块级 HTTP 错误（非 FastAPI 环境也可捕获）"""
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _http_exception(status_code: int, detail: str):
    """延迟导入 HTTPException，使鉴权逻辑可独立于 FastAPI 测试"""
    if FASTAPI_AVAILABLE:
        return HTTPException(status_code=status_code, detail=detail)
    # 非 FastAPI 环境：抛出模块级等价异常以便测试
    return TDCAHttpError(status_code, detail)


if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="TDCA KnowledgeGraphCompiler API",
        version="1.1.0",
        description="FC-005 知识图谱编译器 - 先验分布编译服务",
    )
    compiler = TDCAKnowledgeGraphCompiler()

    # ---- 数据模型 ----

    class BuildFromNCARequest(BaseModel):
        scenario: str = ""
        time_range: dict = {}
        subject_dids: list = []

    class BuildFromNCAResponse(BaseModel):
        nodes_created: int
        node_refs: list
        nca_query_summary: dict
        stats: dict

    class CompilePriorRequest(BaseModel):
        graph_ref: str
        node_selection: list = []
        distribution_type: str = "BAYESIAN"
        min_confidence: float = 0.0
        conflict_resolution: str = "WEIGHTED_AVERAGE"

    class CompilePriorResponse(BaseModel):
        prior_output: dict
        status: str
        warnings: list

    # ---- 接口 ----

    @app.post("/api/v1/kg/build-from-nca", response_model=BuildFromNCAResponse)
    def build_from_nca(req: BuildFromNCARequest, authorization: str = Header(None)):
        """FR-001: 从 NCA 构建知识节点"""
        _check_auth(authorization or "")
        query = {
            'scenario': req.scenario,
            'time_range': req.time_range,
            'subject_dids': req.subject_dids,
        }
        result = compiler.build_from_nca(query)
        return result

    @app.post("/api/v1/kg/compile-prior", response_model=CompilePriorResponse)
    def compile_prior(req: CompilePriorRequest, authorization: str = Header(None)):
        """FR-005: 编译先验分布"""
        _check_auth(authorization or "")
        result = compiler.compile_prior(
            graph_ref=req.graph_ref,
            node_selection=req.node_selection,
            distribution_type=req.distribution_type,
            min_confidence=req.min_confidence,
            conflict_resolution=req.conflict_resolution,
        )
        return result

    @app.get("/health")
    def health():
        """健康检查"""
        return {"status": "ok", "version": TDCAKnowledgeGraphCompiler.VERSION}
else:
    app = None


if __name__ == '__main__':
    if not FASTAPI_AVAILABLE:
        print("[NSFL-TRIGGER] FastAPI 未安装，请执行: pip install fastapi uvicorn")
        sys.exit(1)
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
