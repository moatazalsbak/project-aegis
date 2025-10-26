"""
Project Aegis - Discovery Engine
This Lambda function discovers cost optimization opportunities using AWS Compute Optimizer API.
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Any

# Initialize AWS clients
compute_optimizer = boto3.client('compute-optimizer')
ec2 = boto3.client('ec2')
rds = boto3.client('rds')
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Environment variables
OPTIMIZATION_MODE = os.environ.get('OPTIMIZATION_MODE', 'balanced')
STATE_TABLE = os.environ.get('STATE_TABLE', 'aegis-optimization-state')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

# Risk thresholds based on optimization mode
RISK_THRESHOLDS = {
    'conservative': {'confidence': 'VeryHigh', 'min_savings': 20},
    'balanced': {'confidence': 'High', 'min_savings': 10},
    'aggressive': {'confidence': 'Medium', 'min_savings': 5}
}


def lambda_handler(event, context):
    """
    Main handler function for the discovery engine.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        dict: Response with discovered opportunities
    """
    print(f"Starting Aegis Discovery Engine in {OPTIMIZATION_MODE} mode")
    
    try:
        # Discover optimization opportunities across different resource types
        opportunities = []
        
        # EC2 Instance Recommendations
        ec2_opportunities = discover_ec2_recommendations()
        opportunities.extend(ec2_opportunities)
        
        # Lambda Function Recommendations
        lambda_opportunities = discover_lambda_recommendations()
        opportunities.extend(lambda_opportunities)
        
        # RDS Recommendations
        rds_opportunities = discover_rds_recommendations()
        opportunities.extend(rds_opportunities)
        
        # Filter opportunities based on optimization mode
        threshold = RISK_THRESHOLDS[OPTIMIZATION_MODE]
        filtered_opportunities = filter_opportunities(
            opportunities, 
            threshold['min_savings']
        )
        
        # Store opportunities in DynamoDB
        store_opportunities(filtered_opportunities)
        
        # Send notification
        if filtered_opportunities:
            notify_opportunities(filtered_opportunities)
        
        print(f"Discovery complete. Found {len(filtered_opportunities)} opportunities")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'opportunities_found': len(filtered_opportunities),
                'total_estimated_savings': sum(
                    opp.get('estimated_monthly_savings', 0) 
                    for opp in filtered_opportunities
                ),
                'mode': OPTIMIZATION_MODE
            })
        }
        
    except Exception as e:
        print(f"Error in discovery engine: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def discover_ec2_recommendations() -> List[Dict[str, Any]]:
    """
    Discover EC2 instance optimization opportunities.
    
    Returns:
        List of EC2 optimization opportunities
    """
    print("Discovering EC2 optimization opportunities...")
    opportunities = []
    
    try:
        response = compute_optimizer.get_ec2_instance_recommendations(
            maxResults=1000
        )
        
        for recommendation in response.get('instanceRecommendations', []):
            instance_arn = recommendation['instanceArn']
            instance_id = instance_arn.split('/')[-1]
            current_type = recommendation['currentInstanceType']
            
            for option in recommendation.get('recommendationOptions', []):
                recommended_type = option['instanceType']
                estimated_savings = option.get('estimatedMonthlySavings', {}).get('value', 0)
                
                if estimated_savings > 0:
                    opportunities.append({
                        'resource_id': instance_id,
                        'resource_type': 'EC2',
                        'current_config': current_type,
                        'recommended_config': recommended_type,
                        'estimated_monthly_savings': estimated_savings,
                        'confidence': option.get('performanceRisk', 'Unknown'),
                        'timestamp': int(datetime.now().timestamp())
                    })
        
        print(f"Found {len(opportunities)} EC2 opportunities")
        
    except Exception as e:
        print(f"Error discovering EC2 recommendations: {str(e)}")
    
    return opportunities


def discover_lambda_recommendations() -> List[Dict[str, Any]]:
    """
    Discover Lambda function optimization opportunities.
    
    Returns:
        List of Lambda optimization opportunities
    """
    print("Discovering Lambda optimization opportunities...")
    opportunities = []
    
    try:
        response = compute_optimizer.get_lambda_function_recommendations(
            maxResults=1000
        )
        
        for recommendation in response.get('lambdaFunctionRecommendations', []):
            function_arn = recommendation['functionArn']
            function_name = function_arn.split(':')[-1]
            current_memory = recommendation['currentMemorySize']
            
            for option in recommendation.get('memorySizeRecommendationOptions', []):
                recommended_memory = option['memorySize']
                estimated_savings = option.get('estimatedMonthlySavings', {}).get('value', 0)
                
                if estimated_savings > 0:
                    opportunities.append({
                        'resource_id': function_name,
                        'resource_type': 'Lambda',
                        'current_config': f"{current_memory}MB",
                        'recommended_config': f"{recommended_memory}MB",
                        'estimated_monthly_savings': estimated_savings,
                        'confidence': 'High',
                        'timestamp': int(datetime.now().timestamp())
                    })
        
        print(f"Found {len(opportunities)} Lambda opportunities")
        
    except Exception as e:
        print(f"Error discovering Lambda recommendations: {str(e)}")
    
    return opportunities


def discover_rds_recommendations() -> List[Dict[str, Any]]:
    """
    Discover RDS instance optimization opportunities.
    Includes Graviton (ARM) migration recommendations.
    
    Returns:
        List of RDS optimization opportunities
    """
    print("Discovering RDS optimization opportunities...")
    opportunities = []
    
    try:
        # Get all RDS instances
        response = rds.describe_db_instances()
        
        for db in response.get('DBInstances', []):
            db_identifier = db['DBInstanceIdentifier']
            current_class = db['DBInstanceClass']
            
            # Check if Graviton migration is possible
            if is_graviton_compatible(current_class):
                graviton_class = get_graviton_equivalent(current_class)
                estimated_savings = calculate_graviton_savings(current_class)
                
                opportunities.append({
                    'resource_id': db_identifier,
                    'resource_type': 'RDS',
                    'current_config': current_class,
                    'recommended_config': graviton_class,
                    'estimated_monthly_savings': estimated_savings,
                    'confidence': 'High',
                    'optimization_type': 'Graviton',
                    'timestamp': int(datetime.now().timestamp())
                })
        
        print(f"Found {len(opportunities)} RDS opportunities")
        
    except Exception as e:
        print(f"Error discovering RDS recommendations: {str(e)}")
    
    return opportunities


def is_graviton_compatible(instance_class: str) -> bool:
    """
    Check if an instance class is compatible with Graviton migration.
    """
    # Simplified logic - in production, this would be more comprehensive
    x86_patterns = ['db.m5.', 'db.r5.', 'db.t3.']
    return any(pattern in instance_class for pattern in x86_patterns)


def get_graviton_equivalent(instance_class: str) -> str:
    """
    Get the Graviton equivalent of an x86 instance class.
    """
    mapping = {
        'db.m5.': 'db.m6g.',
        'db.r5.': 'db.r6g.',
        'db.t3.': 'db.t4g.'
    }
    
    for x86, graviton in mapping.items():
        if x86 in instance_class:
            return instance_class.replace(x86, graviton)
    
    return instance_class


def calculate_graviton_savings(instance_class: str) -> float:
    """
    Calculate estimated monthly savings from Graviton migration.
    Based on typical 25% cost reduction.
    """
    # Simplified - in production, this would use actual pricing API
    base_cost_map = {
        'db.m5.large': 140,
        'db.m5.xlarge': 280,
        'db.r5.large': 200,
        'db.r5.xlarge': 400,
        'db.t3.medium': 60,
        'db.t3.large': 120
    }
    
    base_cost = base_cost_map.get(instance_class, 100)
    return base_cost * 0.25  # 25% savings


def filter_opportunities(opportunities: List[Dict[str, Any]], 
                        min_savings: float) -> List[Dict[str, Any]]:
    """
    Filter opportunities based on minimum savings threshold.
    """
    return [
        opp for opp in opportunities 
        if opp.get('estimated_monthly_savings', 0) >= min_savings
    ]


def store_opportunities(opportunities: List[Dict[str, Any]]) -> None:
    """
    Store discovered opportunities in DynamoDB.
    """
    if not opportunities:
        return
    
    table = dynamodb.Table(STATE_TABLE)
    
    for opportunity in opportunities:
        try:
            table.put_item(
                Item={
                    **opportunity,
                    'status': 'discovered',
                    'expiration': int(datetime.now().timestamp()) + (30 * 24 * 3600)  # 30 days TTL
                }
            )
        except Exception as e:
            print(f"Error storing opportunity: {str(e)}")


def notify_opportunities(opportunities: List[Dict[str, Any]]) -> None:
    """
    Send notification about discovered opportunities.
    """
    if not SNS_TOPIC_ARN:
        return
    
    total_savings = sum(opp.get('estimated_monthly_savings', 0) for opp in opportunities)
    
    message = f"""
🛡️ Aegis Discovery Report

Mode: {OPTIMIZATION_MODE}
Opportunities Found: {len(opportunities)}
Estimated Monthly Savings: ${total_savings:.2f}

Breakdown:
"""
    
    by_type = {}
    for opp in opportunities:
        resource_type = opp['resource_type']
        by_type[resource_type] = by_type.get(resource_type, 0) + 1
    
    for resource_type, count in by_type.items():
        message += f"  - {resource_type}: {count} opportunities\n"
    
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Aegis: New Cost Optimization Opportunities',
            Message=message
        )
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
