#!/bin/bash
# 清理 mortgage_assistant 多智能体应用创建的所有资源

echo "开始清理 mortgage_assistant 资源..."
echo "$(date): 开始执行清理脚本" >> /var/log/workshop-cleanup.log

# 设置区域
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
  REGION="us-east-1"  # 默认区域
fi
echo "使用区域: $REGION"
echo "$(date): 使用区域: $REGION" >> /var/log/workshop-cleanup.log

# 检查目录是否存在
SCRIPT_DIR="/home/ec2-user/amazon-bedrock-agent-workshop-for-gcr/examples/multi_agent_collaboration/mortgage_assistant/"
if [ ! -d "$SCRIPT_DIR" ]; then
  echo "错误: 目录 $SCRIPT_DIR 不存在"
  echo "$(date): 错误: 目录 $SCRIPT_DIR 不存在" >> /var/log/workshop-cleanup.log
  echo "请检查路径是否正确"
  exit 1
fi

echo "切换到目录: $SCRIPT_DIR"
cd "$SCRIPT_DIR"

# 创建虚拟环境（如果不存在）
if [ ! -d ".venv" ]; then
  echo "创建虚拟环境..."
  echo "$(date): 创建虚拟环境..." >> /var/log/workshop-cleanup.log
  python3 -m venv .venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
echo "$(date): 激活虚拟环境..." >> /var/log/workshop-cleanup.log
source .venv/bin/activate

# 安装必要的依赖
echo "安装必要的依赖..."
echo "$(date): 安装必要的依赖..." >> /var/log/workshop-cleanup.log
pip install -q boto3 requests

# 运行清理脚本
echo "运行清理脚本..."
echo "$(date): 运行清理脚本..." >> /var/log/workshop-cleanup.log
python3 clean_up.py --region "$REGION" --delete_s3_bucket --verbose

# 检查清理脚本的退出状态
if [ $? -ne 0 ]; then
  echo "警告: 清理脚本可能未成功完成"
  echo "$(date): 警告: 清理脚本可能未成功完成" >> /var/log/workshop-cleanup.log
  echo "请检查上面的错误信息"
else
  echo "清理脚本成功完成"
  echo "$(date): 清理脚本成功完成" >> /var/log/workshop-cleanup.log
fi

# 退出虚拟环境
deactivate

echo "清理完成！"
echo "$(date): 清理完成" >> /var/log/workshop-cleanup.log
