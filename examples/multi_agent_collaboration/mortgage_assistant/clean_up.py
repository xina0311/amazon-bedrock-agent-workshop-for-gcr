#!/usr/bin/env python

import sys
from pathlib import Path
import boto3
import logging
import argparse
import time
import json
import botocore

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.utils.bedrock_agent import Agent
from src.utils.knowledge_base_helper import KnowledgeBasesForAmazonBedrock

# 设置日志
logging.basicConfig(format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_opensearch_collection(collection_name, region=None):
    """
    删除OpenSearch集合
    
    参数:
    collection_name (str): 集合名称
    region (str): AWS区域
    """
    try:
        # 创建OpenSearch客户端
        if region:
            opensearch_client = boto3.client('opensearchserverless', region_name=region)
        else:
            opensearch_client = boto3.client('opensearchserverless')
        
        # 获取集合ID
        collections = opensearch_client.list_collections()
        collection_id = None
        
        for collection in collections.get('collectionSummaries', []):
            if collection['name'] == collection_name:
                collection_id = collection['id']
                break
        
        if not collection_id:
            logger.warning(f"未找到OpenSearch集合: {collection_name}")
            return
        
        # 删除集合
        logger.info(f"删除OpenSearch集合: {collection_name} (ID: {collection_id})")
        response = opensearch_client.delete_collection(id=collection_id)
        
        # 等待集合删除完成
        logger.info("等待OpenSearch集合删除完成...")
        while True:
            try:
                opensearch_client.get_collection(id=collection_id)
                time.sleep(10)
            except opensearch_client.exceptions.ResourceNotFoundException:
                logger.info(f"OpenSearch集合 {collection_name} 已成功删除")
                break
        
        return response
    except Exception as e:
        logger.error(f"删除OpenSearch集合时出错: {str(e)}")
        return None

def delete_lambda_function(function_name, region=None):
    """
    删除Lambda函数
    
    参数:
    function_name (str): Lambda函数名称
    region (str): AWS区域
    """
    try:
        # 创建Lambda客户端
        if region:
            lambda_client = boto3.client('lambda', region_name=region)
        else:
            lambda_client = boto3.client('lambda')
        
        # 删除Lambda函数
        logger.info(f"删除Lambda函数: {function_name}")
        
        # 首先删除函数的事件源映射
        try:
            mappings = lambda_client.list_event_source_mappings(FunctionName=function_name)
            for mapping in mappings.get('EventSourceMappings', []):
                logger.info(f"删除Lambda事件源映射: {mapping['UUID']}")
                lambda_client.delete_event_source_mapping(UUID=mapping['UUID'])
        except Exception as e:
            logger.warning(f"删除Lambda事件源映射时出错: {str(e)}")
        
        # 删除函数的权限策略
        try:
            policy = lambda_client.get_policy(FunctionName=function_name)
            policy_json = json.loads(policy['Policy'])
            for statement in policy_json.get('Statement', []):
                sid = statement.get('Sid')
                if sid:
                    logger.info(f"删除Lambda函数权限: {sid}")
                    lambda_client.remove_permission(
                        FunctionName=function_name,
                        StatementId=sid
                    )
        except lambda_client.exceptions.ResourceNotFoundException:
            pass  # 没有策略，继续
        except Exception as e:
            logger.warning(f"删除Lambda函数权限时出错: {str(e)}")
        
        # 删除函数
        response = lambda_client.delete_function(FunctionName=function_name)
        logger.info(f"Lambda函数 {function_name} 已成功删除")
        return response
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.warning(f"Lambda函数不存在: {function_name}")
        return None
    except Exception as e:
        logger.error(f"删除Lambda函数时出错: {str(e)}")
        return None

def find_kb_resources(kb_name, region=None):
    """
    查找与知识库相关的资源（OpenSearch集合和Lambda函数）
    
    参数:
    kb_name (str): 知识库名称
    region (str): AWS区域
    
    返回:
    dict: 包含OpenSearch集合名称和Lambda函数名称的字典
    """
    try:
        # 创建Bedrock客户端
        if region:
            bedrock_client = boto3.client('bedrock-agent', region_name=region)
        else:
            bedrock_client = boto3.client('bedrock-agent')
        
        # 获取知识库列表
        knowledge_bases = bedrock_client.list_knowledge_bases()
        kb_id = None
        
        # 查找指定知识库
        for kb in knowledge_bases.get('knowledgeBaseSummaries', []):
            if kb['name'] == kb_name:
                kb_id = kb['knowledgeBaseId']
                break
        
        if not kb_id:
            logger.warning(f"未找到知识库: {kb_name}")
            return {}
        
        # 获取知识库详情
        kb_details = bedrock_client.get_knowledge_base(knowledgeBaseId=kb_id)
        
        # 提取资源信息
        resources = {}
        
        # 提取OpenSearch集合名称
        if 'opensearchServerlessConfiguration' in kb_details.get('storageConfiguration', {}):
            collection_arn = kb_details['storageConfiguration']['opensearchServerlessConfiguration']['collectionArn']
            collection_name = collection_arn.split('/')[-1]
            resources['opensearch_collection'] = collection_name
        
        # 提取Lambda函数名称
        data_source_id = None
        data_sources = bedrock_client.list_data_sources(knowledgeBaseId=kb_id)
        if data_sources.get('dataSourceSummaries'):
            data_source_id = data_sources['dataSourceSummaries'][0]['dataSourceId']
        
        if data_source_id:
            data_source = bedrock_client.get_data_source(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id
            )
            
            if 'vectorIngestionConfiguration' in data_source:
                lambda_arn = data_source['vectorIngestionConfiguration'].get('customTransformationLambdaArn')
                if lambda_arn:
                    lambda_name = lambda_arn.split(':')[-1]
                    resources['lambda_function'] = lambda_name
        
        return resources
    except Exception as e:
        logger.error(f"查找知识库资源时出错: {str(e)}")
        return {}

def find_and_delete_iam_roles_policies(prefix):
    """
    查找并删除以指定前缀开头的IAM角色和策略
    
    参数:
    prefix (str): IAM角色和策略名称的前缀
    """
    try:
        # 创建IAM客户端
        iam_client = boto3.client('iam')
        
        # 查找并删除角色
        paginator = iam_client.get_paginator('list_roles')
        for page in paginator.paginate():
            for role in page['Roles']:
                role_name = role['RoleName']
                if role_name.startswith(prefix):
                    logger.info(f"找到IAM角色: {role_name}")
                    
                    # 删除角色策略
                    try:
                        # 列出并分离附加的策略
                        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
                        for policy in attached_policies.get('AttachedPolicies', []):
                            policy_arn = policy['PolicyArn']
                            logger.info(f"分离策略 {policy['PolicyName']} 从角色 {role_name}")
                            iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                        
                        # 列出并删除内联策略
                        inline_policies = iam_client.list_role_policies(RoleName=role_name)
                        for policy_name in inline_policies.get('PolicyNames', []):
                            logger.info(f"删除内联策略 {policy_name} 从角色 {role_name}")
                            iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
                        
                        # 删除角色
                        logger.info(f"删除角色: {role_name}")
                        iam_client.delete_role(RoleName=role_name)
                        logger.info(f"成功删除角色: {role_name}")
                    except Exception as e:
                        logger.warning(f"删除角色 {role_name} 时出错: {str(e)}")
        
        # 查找并删除策略
        paginator = iam_client.get_paginator('list_policies')
        for page in paginator.paginate(Scope='Local'):  # 只查找客户管理的策略
            for policy in page['Policies']:
                policy_name = policy['PolicyName']
                policy_arn = policy['Arn']
                if policy_name.startswith(prefix):
                    logger.info(f"找到IAM策略: {policy_name}")
                    
                    try:
                        # 列出并分离使用此策略的所有实体
                        entities = iam_client.list_entities_for_policy(PolicyArn=policy_arn)
                        
                        # 从角色分离
                        for role in entities.get('PolicyRoles', []):
                            logger.info(f"分离策略 {policy_name} 从角色 {role['RoleName']}")
                            iam_client.detach_role_policy(
                                RoleName=role['RoleName'],
                                PolicyArn=policy_arn
                            )
                        
                        # 删除除默认版本外的所有版本
                        versions = iam_client.list_policy_versions(PolicyArn=policy_arn)
                        for version in versions.get('Versions', []):
                            if not version.get('IsDefaultVersion', False):
                                logger.info(f"删除策略版本: {version['VersionId']}")
                                iam_client.delete_policy_version(
                                    PolicyArn=policy_arn,
                                    VersionId=version['VersionId']
                                )
                        
                        # 删除策略
                        logger.info(f"删除策略: {policy_name}")
                        iam_client.delete_policy(PolicyArn=policy_arn)
                        logger.info(f"成功删除策略: {policy_name}")
                    except Exception as e:
                        logger.warning(f"删除策略 {policy_name} 时出错: {str(e)}")
    except Exception as e:
        logger.warning(f"查找和删除IAM角色和策略时出错: {str(e)}")

def clean_up(verbose=True, delete_s3_bucket=False, region=None):
    """
    清理所有部署的资源，包括Bedrock Agent、知识库、OpenSearch集合、Lambda函数和IAM角色/策略
    
    参数:
    verbose (bool): 是否显示详细日志
    delete_s3_bucket (bool): 是否删除S3存储桶
    region (str): AWS区域
    """
    logger.info("开始清理资源...")
    
    # 初始化知识库助手
    kb_helper = KnowledgeBasesForAmazonBedrock()
    
    # 设置强制重新创建为True，确保删除操作能够执行
    Agent.set_force_recreate_default(True)
    
    # 查找知识库相关资源
    kb_name = "general-mortgage-kb"
    kb_resources = find_kb_resources(kb_name, region)
    
    # 删除主要的Supervisor Agent
    logger.info("删除Supervisor Agent: mortgages_assistant")
    Agent.delete_by_name("mortgages_assistant", verbose=verbose)
    
    # 删除各个子Agent
    agent_names = [
        "general_mortgage_questions",
        "existing_mortgage_assistant", 
        "mortgage_application_agent",
        "mortgage_greeting_agent"
    ]
    
    for agent_name in agent_names:
        try:
            logger.info(f"删除Agent: {agent_name}")
            Agent.delete_by_name(agent_name, verbose=verbose)
        except Exception as e:
            logger.warning(f"删除Agent {agent_name} 时出错: {str(e)}")
    
    # 删除知识库
    try:
        logger.info(f"删除知识库: {kb_name}")
        kb_helper.delete_kb(kb_name, delete_s3_bucket=delete_s3_bucket)
    except Exception as e:
        logger.warning(f"删除知识库时出错: {str(e)}")
    
    # 删除OpenSearch集合
    if 'opensearch_collection' in kb_resources:
        try:
            collection_name = kb_resources['opensearch_collection']
            logger.info(f"删除OpenSearch集合: {collection_name}")
            delete_opensearch_collection(collection_name, region)
        except Exception as e:
            logger.warning(f"删除OpenSearch集合时出错: {str(e)}")
    
    # 删除Lambda函数
    if 'lambda_function' in kb_resources:
        try:
            lambda_name = kb_resources['lambda_function']
            logger.info(f"删除Lambda函数: {lambda_name}")
            delete_lambda_function(lambda_name, region)
        except Exception as e:
            logger.warning(f"删除Lambda函数时出错: {str(e)}")
    
    # 删除特定的Lambda函数
    specific_lambda_functions = [
        "mortgage_application_agent_ag",
        "existing_mortgage_assistant_ag"
    ]
    
    for function_name in specific_lambda_functions:
        try:
            logger.info(f"删除Lambda函数: {function_name}")
            delete_lambda_function(function_name, region)
        except Exception as e:
            logger.warning(f"删除Lambda函数 {function_name} 时出错: {str(e)}")
    
    # 删除IAM角色和策略
    try:
        # 删除与Bedrock Agent相关的IAM角色和策略
        logger.info("删除与Bedrock Agent相关的IAM角色和策略")
        prefixes = [
            "AmazonBedrockExecutionRoleForAgents_",
            "bedrock-agent-",
            "BedrockAgentRole",
            "mortgages_assistant",
            "general_mortgage_questions",
            "existing_mortgage_assistant",
            "mortgage_application_agent",
            "mortgage_greeting_agent",
            "general-mortgage-kb"
        ]
        
        for prefix in prefixes:
            find_and_delete_iam_roles_policies(prefix)
    except Exception as e:
        logger.warning(f"删除IAM角色和策略时出错: {str(e)}")
    
    logger.info("资源清理完成")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='清理Amazon Bedrock Agents和知识库资源')
    parser.add_argument('--verbose', action='store_true', default=True, 
                        help='显示详细日志 (默认: True)')
    parser.add_argument('--delete_s3_bucket', action='store_true', default=False, 
                        help='是否删除S3存储桶 (默认: False)')
    parser.add_argument('--region', type=str, default=None,
                        help='AWS区域 (默认: 使用默认配置)')
    
    args = parser.parse_args()
    clean_up(verbose=args.verbose, delete_s3_bucket=args.delete_s3_bucket, region=args.region)
