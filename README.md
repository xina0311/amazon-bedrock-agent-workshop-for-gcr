# Amazon Bedrock Agent Workshop for GCR

<h2 align="center">Amazon Bedrock Agent 中国区工作坊</h2>
<p align="center">
  :wave: :wave: 欢迎来到 Amazon Bedrock Agent 中国区工作坊 :wave: :wave:
</p>

## 关于本仓库

本仓库是 [Amazon Bedrock Agent Samples](https://github.com/awslabs/amazon-bedrock-agent-samples) 的分支的版本，为亚马逊云科技中国区的用户提供动手练习工作坊。通过本工作坊，您可以使用 Amazon Nova Pro 模型来部署运行 mortgage_assistant（按揭贷款多智能体应用），体验 Amazon Bedrock Multi Agent Collaboration（多代理协作）的强大功能和优势。

## 工作坊指南

完整的操作指南可以在这个地址找到：[基于Amazon Bedrock 构建按揭贷款多智能体应用](https://studio.us-east-1.prod.workshops.aws/preview/d674f40f-d636-4654-9322-04dafc7cc63e/builds/30a7eb13-bfdf-4ebe-bd1f-5eef38bd8565/zh-CN/4-lab-3)

![Amazon Bedrock Multi Agent Collaboration Demo](images/workshop_bedrock_multi_agent.gif)

*上图展示了按揭贷款多代理应用的组织结构*

## 自助实验环境部署

如果您想在自己的AWS账户中自行完成这个动手练习，可以按照以下步骤操作：

1. 使用 `workshop_cfn_vscodeserver_with_AgentCode.yaml` CloudFormation 模板部署实验资源。
2. 模板会自动启动一台t3.large 规格的Amazon Linux EC2 实例，自动安装 VSCode Server 并克隆所需的代码仓库到 EC2 实例。
3. 然后按照[动手操作指南](https://studio.us-east-1.prod.workshops.aws/preview/d674f40f-d636-4654-9322-04dafc7cc63e/builds/30a7eb13-bfdf-4ebe-bd1f-5eef38bd8565/zh-CN/4-lab-3)完成多智能体应用部署，并进行交互测试。
4. 本实验还提供一个彩蛋，免费注册 [Amazon Builder ID](https://docs.aws.amazon.com/zh_cn/signin/latest/userguide/create-aws_builder_id.html)，安装 [Amazon Q Developer CLI 工具](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line.html)。体验 Q Chat 智能开发辅助工具提升代码相关工作效率

## 实验清理

**重要提示**：实验完成后，请记得执行 `workshop_cleanup.sh` 脚本以清理资源，避免不必要的费用产生。

## 主要功能

通过本工作坊，您将能够：
- 了解Amazon Bedrock Agents的基本概念和工作原理
- 使用Amazon Nova Pro模型构建智能代理
- 体验多代理协作如何解决复杂问题
- 实际操作部署mortgage_assistant（按揭助手）应用
- 学习Amazon Bedrock的最佳实践

## 系统要求

- 有效的AWS账户
- 对Amazon Bedrock服务的访问权限
- 基本的AWS CloudFormation使用经验

## 注意事项

本仓库中的示例仅用于教育和实验目的，不建议直接用于生产环境。请确保在实际应用中实施适当的安全措施和最佳实践。

---

[Amazon Bedrock Agent Samples (英文版)](README_EN.md)
