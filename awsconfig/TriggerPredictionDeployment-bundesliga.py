import boto3
import io
import pandas as pd

s3_client = boto3.client('s3')
sagemaker = boto3.client('sagemaker-runtime')

def lambda_handler(event, context):
    # Extract the bucket name and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    try:
        # Retrieve the CSV file from S3
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        csv_data = s3_response['Body'].read().decode('utf-8')
        
        # Invoke the SageMaker endpoint with the CSV data
        response = sagemaker.invoke_endpoint(
            EndpointName='sagemaker-xgboost-2024-08-21-17-46-40-284',  # Replace with your actual endpoint name
            ContentType='text/csv',
            Body=csv_data
        )
        
        # Parse and print the response from the SageMaker endpoint
        result = response['Body'].read().decode('utf-8')
        print(f"Prediction result: {result}")
        
    except Exception as e:
        print(f"Error during Lambda function execution: {str(e)}")


















