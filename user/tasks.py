from celery import shared_task
from django.conf import settings
import boto3
import logging

logger = logging.getLogger(__name__)

@shared_task
def notify_product_creator(product_name,username):
  try:
    sns_client=boto3.client('sns',region_name= settings.AWS_S3_REGION_NAME)
    SNS_TOPIC_ARN=settings.AWS_SNS_ARN

    sns_client.publish(TopicArn=SNS_TOPIC_ARN,
                                Message=f'$Mr.{username} you added {product_name}',
                                Subject="seller created product",)

  except Exception as e:
    logger.error(f'sns notification failed:{e}')
