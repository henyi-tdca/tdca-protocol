FROM python:3.12-slim
# TDCA NL 意图导航边车（真实外部模型调用 × 规则表降级 × 算力熔断，GSEQ-0645；
# SITE-SEC-001 A 段：会话锁＋IP 限流＋单日配额，成本与供应商名只在内日志，响应体零外露）
RUN pip install --no-cache-dir fastapi "uvicorn>=0.52" httpx pyyaml
COPY deploy/nl/nl_service.py /app/nl_service.py
COPY tools/enforce_entry.py /app/enforce_entry.py
WORKDIR /app
ENV PYTHONPATH=/app
EXPOSE 8002
CMD ["uvicorn", "nl_service:app", "--host", "0.0.0.0", "--port", "8002"]
