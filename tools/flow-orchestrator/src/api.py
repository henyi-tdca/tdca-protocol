# SPDX-License-Identifier: Apache-2.0
"""
TDCA-FC-012 C-3 FastAPI 服务（6 接口）
制度锚定: TDCA-FC-012-PRES-001 Section 3（前端对接接口契约）
Granted-By: TDCA-FC-012-DESIGN-002
NSFL: Token 验证委托 FC-002；NCA 由 FC-001 生成
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_engine import FlowEngine

try:
    from fastapi import FastAPI, Header, HTTPException
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


if FASTAPI_AVAILABLE:
    app = FastAPI(title="TDCA Flow Orchestrator API", version="1.0.0")
    engine = FlowEngine()

    # ---- 数据模型 ----

    class StartRequest(BaseModel):
        intent: dict

    class AdvanceRequest(BaseModel):
        flow_id: str
        context: dict = {}

    class FuseRequest(BaseModel):
        flow_id: str
        reason: str
        level: str = "LEVEL_1"

    class RollbackRequest(BaseModel):
        flow_id: str
        target_phase: str

    class ApproveRequest(BaseModel):
        flow_id: str
        tax_in: float = 0.0
        tax_out: float = 0.0
        human_signature: bool = True

    # ---- 鉴权（简化：前缀检查，生产委托 FC-002） ----

    def _check_auth(token: str):
        if not token or not token.startswith('TDCA-CRT-'):
            raise HTTPException(status_code=401, detail="无效配置权 Token")

    # ---- 接口 ----

    @app.post("/api/v1/flow/start")
    def flow_start(req: StartRequest, authorization: str = Header(None)):
        """启动生命周期（Phase 0）"""
        _check_auth(authorization or "")
        state = engine.start(req.intent)
        return state.to_dict()

    @app.get("/api/v1/flow/status")
    def flow_status(flow_id: str, authorization: str = Header(None)):
        """当前 Phase 状态"""
        _check_auth(authorization or "")
        try:
            state = engine._get_state(flow_id)
            return state.to_dict()
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.post("/api/v1/flow/advance")
    def flow_advance(req: AdvanceRequest, authorization: str = Header(None)):
        """推进下一 Phase"""
        _check_auth(authorization or "")
        try:
            state = engine.advance(req.flow_id, req.context)
            return state.to_dict()
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.post("/api/v1/flow/fuse")
    def flow_fuse(req: FuseRequest, authorization: str = Header(None)):
        """触发熔断"""
        _check_auth(authorization or "")
        try:
            state = engine.fuse(req.flow_id, req.reason, req.level)
            return state.to_dict()
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.post("/api/v1/flow/rollback")
    def flow_rollback(req: RollbackRequest, authorization: str = Header(None)):
        """回退 Phase"""
        _check_auth(authorization or "")
        try:
            state = engine.rollback(req.flow_id, req.target_phase)
            return state.to_dict()
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.post("/api/v1/flow/approve")
    def flow_approve(req: ApproveRequest, authorization: str = Header(None)):
        """人类批准（P8→COMPLETED + MOU 闭环）"""
        _check_auth(authorization or "")
        try:
            state = engine.human_approve(req.flow_id, {
                'tax_in': req.tax_in,
                'tax_out': req.tax_out,
                'human_signature': req.human_signature,
            })
            return state.to_dict()
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    @app.get("/api/v1/flow/trajectory")
    def flow_trajectory(flow_id: str, authorization: str = Header(None)):
        """全流程 NCA 轨迹"""
        _check_auth(authorization or "")
        try:
            return engine.trajectory(flow_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "flow-orchestrator"}

else:
    app = None


if __name__ == '__main__':
    if not FASTAPI_AVAILABLE:
        print("[NSFL-TRIGGER] FastAPI 未安装，请执行: pip install fastapi uvicorn")
        sys.exit(1)
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)
