#!/bin/bash

# ==========================================
# 1. 设定路径 (请确保这里是你电脑的真实路径)
# ==========================================
PROJECT_DIR="/Users/roy/Code/Web Scraper"
LOG_DIR="logs"

# ==========================================
# 2. 准备工作
# ==========================================
cd "$PROJECT_DIR"

# 自动建日志文件夹
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi

# 生成带时间戳的日志文件名
CURRENT_TIME=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/upload_only_$CURRENT_TIME.log"

# 定义“双向记录”函数 (屏幕+文件，且包含报错信息)
run_and_log() {
    "$@" 2>&1 | tee -a "$LOG_FILE"
}

# ==========================================
# 3. 开始执行
# ==========================================
# 激活 Python 虚拟环境
source .venv/bin/activate

echo "🚀 单独启动：每日英语听力上传助手" | tee -a "$LOG_FILE"
echo "📂 工作目录: $(pwd)" | tee -a "$LOG_FILE"
echo "📝 日志文件: $LOG_FILE" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

# === [核心修改] 只运行上传脚本 ===
echo "🤖 正在启动 Playwright 浏览器..." | tee -a "$LOG_FILE"
run_and_log python auto_upload.py

# ==========================================
# 4. 结束
# ==========================================
echo "" | tee -a "$LOG_FILE"
echo "🏁 运行结束。" | tee -a "$LOG_FILE"
read -p "按 [回车键] 关闭窗口..."