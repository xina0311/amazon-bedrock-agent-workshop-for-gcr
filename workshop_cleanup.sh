#!/bin/bash
# 清理 mortgage_assistant 多智能体应用创建的所有资源

echo "开始清理 mortgage_assistant 资源..."

# 设置区域
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
  REGION="us-east-1"  # 默认区域
fi
echo "使用区域: $REGION"

# 检查虚拟环境是否存在
VENV_PATH=".venv"
if [ ! -d "$VENV_PATH" ]; then
  echo "错误: 虚拟环境 $VENV_PATH 不存在"
  echo "请确保您在正确的目录中，或者已经创建了虚拟环境"
  exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 切换到正确的目录
SCRIPT_DIR="/home/ec2-user/amazon-bedrock-agent-workshop-for-gcr/examples/multi_agent_collaboration/mortgage_assistant/"
if [ ! -d "$SCRIPT_DIR" ]; then
  echo "错误: 目录 $SCRIPT_DIR 不存在"
  echo "请检查路径是否正确"
  exit 1
fi

echo "切换到目录: $SCRIPT_DIR"
cd "$SCRIPT_DIR"

# 运行清理脚本
echo "运行清理脚本..."
python3 clean_up.py --region "$REGION" --delete_s3_bucket --verbose

# 检查清理脚本的退出状态
if [ $? -ne 0 ]; then
  echo "警告: 清理脚本可能未成功完成"
  echo "请检查上面的错误信息"
else
  echo "清理脚本成功完成"
fi

# 退出虚拟环境
deactivate

echo "清理完成！"
echo "现在您可以安全地删除 CloudFormation 堆栈。"