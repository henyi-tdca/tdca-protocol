#!/usr/bin/env bash
# TDCA 部署门禁 · 启用/回退开关（批C-C1 · 创始人一句即回退）
# 用法: gate-ctl.sh enable|disable|status   —— disable 即回退【待启用】，全程留痕 gate-breakglass.log
set -u
BASE=/root/tdca/deploy
FLAG=$BASE/GATE-ENABLED
LOG=$BASE/gate-breakglass.log
ts() { date +%Y-%m-%dT%H:%M+08:00; }
case "${1:-}" in
  enable)
    printf 'ENABLED %s by 批C-C1（创始人「先批C」授权）\n' "$(ts)" > "$FLAG"
    echo "$(ts) GATE-ENABLE 启用（批C-C1）" >> "$LOG"
    echo "GATE=ENABLED  ($(cat "$FLAG"))"
    ;;
  disable)
    rm -f "$FLAG"
    echo "$(ts) GATE-DISABLE 回退【待启用】（创始人一句即回退之开关）" >> "$LOG"
    echo "GATE=DISABLED（回退完成，deploy_gate 校验器仍在机、随取随复用）"
    ;;
  status)
    if [ -f "$FLAG" ]; then echo "GATE=ENABLED ($(cat "$FLAG"))"; else echo "GATE=DISABLED（待启用）"; fi
    ;;
  *)
    echo "usage: gate-ctl.sh enable|disable|status"; exit 2;;
esac
