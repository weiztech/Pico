import boto3
from backend import settings
from backend.logger import logger
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from urllib.parse import urlparse

def generate_fetch_presigned_url(key, bucket_name, expires_in=60):
    """
    Generate a presigned url to get an object (file, image ...etc) from aws3.
    Specificly for objects that lives under a private bucket WE CANT ACCESS THEM DIRECTLY.
    :param expires_in: The number of seconds that the presigned URL is valid for. default 01 minute.
    """

    # Create an S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    # Generate the pre-signed URL
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_name,
            'Key': key
        },
        ExpiresIn=expires_in 
    )

    return url


def generate_upload_presigned_url(key, expires_in=600):
    """
    Generate a presigned S3 on Outposts URL that can be used to perform an upload action.
    :param key: File name inside the aws s3 bucket.
    :param expires_in: The number of seconds that the presigned URL is valid for. default 10Min
    :return: {
        url: <string> aws upload url,
        fields: <object>
            - Key: File name inside aws s3 bucket.
            - AWSAccessKeyId: aws client access key ID.
            - policy: include expiry date ...etc.
            - signature: generated signature will be verified later on aws side when a request to upload is initiated.
        
        NB: all these field should be included inside the post request along side with a file field named <file>.
    }.
    """
    # logger.info("Generating upload presignid URL with the key: " + key)
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    #Generate the presigned URL
    response = s3_client.generate_presigned_post(
        Bucket =  settings.AWS_STORAGE_BUCKET_NAME,
        Key = key,
        ExpiresIn = expires_in
    )


    url = response["url"]
    fields = response["fields"]

    return {
        "url": url,
        "fields": fields
    }

def s3_direct_file_uplaod(full_file_path, object_key, bucket_name):
    """
    Upload a file to aws s3.
    :param: full_file_path
    :param: object_key: file name / path inside aws s3 bucket
    :param: bucket_name
    """
    # Ensure you have your AWS credentials set up properly
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    s3 = session.resource('s3')
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    file_path = full_file_path
    s3_key = object_key

    try:
        s3.Bucket(bucket_name).upload_file(file_path, s3_key)
    except (NoCredentialsError, PartialCredentialsError):
        print("Credentials not available")
    except Exception as e:
        print(f"An error occurred: {e}")



def get_preview_url_from_instance(file_field, expires_in=3600):
    """
    Generates a presigned S3 URL that allows previewing a PDF file in the browser,
    using the given Django FileField (e.g., instance.file).
    """
    # Extract the S3 object key from the file's URL
    # Example: https://bucket.s3.amazonaws.com/docs/myfile.pdf → key = "docs/myfile.pdf"
    parsed_url = urlparse(file_field.url)
    key = parsed_url.path.lstrip('/')  # Remove leading slash from path
    key = key.replace(f"{settings.AWS_STORAGE_BUCKET_NAME}/", "") # remove bucket name from key

    # Generate a presigned URL with:
    # Create an S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    # Generate the pre-signed URL
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': key,
            'ResponseContentDisposition': 'inline',
            'ResponseContentType': 'application/pdf',
        },
        ExpiresIn=expires_in, # in seconds by default 3600 (1H) 
    )
    return url  # Return the presigned previewable URL
