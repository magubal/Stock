#!/bin/bash
# 10분마다 배치 진행 상황 출력
OUTFILE="C:/Users/calm_/AppData/Local/Temp/claude/f--PSJ-AntigravityWorkPlace-Stock-Test-02/tasks/b7cff05.output"

while true; do
    if [ ! -f "$OUTFILE" ]; then
        echo "[$(date)] Output file not found. Batch may have ended."
        break
    fi

    # 마지막 진행 번호 추출
    LAST=$(grep -oP '\[\d+/2085\]' "$OUTFILE" | tail -1)
    # 성공/실패 카운트
    OK=$(grep -c 'ok_해자=' "$OUTFILE" 2>/dev/null || echo 0)
    FAIL=$(grep -c '실패:' "$OUTFILE" 2>/dev/null || echo 0)
    SAVES=$(grep -c '중간저장' "$OUTFILE" 2>/dev/null || echo 0)
    # 마지막 종목
    LAST_STOCK=$(grep -oP '\] .+ \(\d+\) ' "$OUTFILE" | tail -1)
    # 배치 완료 여부
    DONE=$(grep -c '배치 완료' "$OUTFILE" 2>/dev/null || echo 0)

    echo "=============================="
    echo "[$(date '+%H:%M:%S')] Batch Progress"
    echo "  Current: $LAST"
    echo "  Last: $LAST_STOCK"
    echo "  Saves: $SAVES"
    echo "=============================="

    if [ "$DONE" -gt 0 ]; then
        echo "BATCH COMPLETE!"
        tail -5 "$OUTFILE"
        break
    fi

    sleep 600  # 10분
done
