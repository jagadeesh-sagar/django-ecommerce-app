from celery import shared_task
from django.conf import settings
import boto3
import logging
from django.core.mail import send_mail


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
    
@shared_task(bind=True,max_retries=3,default_retry_delay=60)

def delete_product(user_name,product_id):
  s3_client=boto3.client("s3",
                           aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_S3_REGION_NAME )
  try:

    response=s3_client.list_objects_v2(
      Bucket=settings.AWS_STORAGE_BUCKET_NAME,
      Prefix=f'{user_name}/{product_id}' 
      )
    
 
    if 'Contents' in response:
        objects=[{'Key':obj['Key']} for obj in response['Contents']]

        s3_client.delete_objects(
          Bucket=settings.AWS_STORAGE_BUCKET_NAME,
          Delete={'Objects':objects}
        )

  except Exception as e:
    logger.error(f's3 object deletion for product image failed:{e}')

@shared_task(bind=True,max_retries=3,default_retry_delay=60)
def delete_s3_file(self, object_key):
  s3_client=boto3.client("s3",
                           aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_S3_REGION_NAME )
  try:
    s3_client.delete_object(
      Bucket=settings.AWS_STORAGE_BUCKET_NAME,
      Key=object_key
    )
  except Exception as e:
    logger.error(f's3 object deletion failed for key {object_key}:{e}')

@shared_task(bind=True,max_retries=3,default_retry_delay=60)
def delete_s3_files(self, object_keys):
    if not object_keys:
        return
    s3_client=boto3.client("s3",
                             aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                              region_name=settings.AWS_S3_REGION_NAME )
    try:
        objects=[{'Key': key} for key in object_keys]
        s3_client.delete_objects(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Delete={'Objects': objects}
        )
    except Exception as e:
        logger.error(f's3 bulk object deletion failed: {e}')


@shared_task
def send_otp_email(user_email, otp):
    send_mail(
        subject='Your OTP for product deletion',
        message=f'Your OTP is: {otp}. Valid for 5 minutes.',
        from_email='noreply@chatram.in',
        recipient_list=[user_email],
    )