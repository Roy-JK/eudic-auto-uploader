#!/bin/bash

# 1. 切到脚本所在目录
cd "$(dirname "$0")"
echo "📂 工作目录已切换至：$(pwd)"

# 2. 只用本项目 .venv 里的 Python
VENV_PYTHON="./.venv/bin/python"

# 3. 如果 .venv 不存在，直接报错退出
if [ ! -x "$VENV_PYTHON" ]; then
    echo "❌ 未找到虚拟环境：$VENV_PYTHON"
    echo "请先在当前目录创建并安装依赖，例如："
    echo "    python3 -m venv .venv"
    echo "    source .venv/bin/activate"
    echo "    pip install -r requirements.txt"
    read -p "按 [回车键] 关闭窗口..."  # 防止窗口一闪而过
    exit 1
fi

echo "🐍 使用虚拟环境 Python: $VENV_PYTHON"
echo "----------------------------------------"
echo "🚀 正在启动自动上传助手..."

# 4. 用虚拟环境里的 Python 运行主脚本
"$VENV_PYTHON" main.py
RET=$?

# 5. 根据返回码给出提示
if [ $RET -eq 0 ]; then
    echo "✅ 程序执行成功！"
else
    echo "❌ 程序执行出错，请检查上方报错信息。"
fi

echo "🏁 运行结束。"
read -p "按 [回车键] 关闭窗口..."
