import logging
from google.cloud import storage, exceptions

logger = logging.getLogger('main_logger')


def upload_blob(bucket_name, destination_file_name, file_object, content_type):
    """Uploads a file object to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_file_name)
    try:
        blob.upload_from_file(file_object, rewind=True,  content_type=content_type)
    except exceptions.GoogleCloudError as e:
        logger.error("[ERROR] While attempting to upload application to GCS bucket:")
        logger.exception(e)
        return {
            'err': e,
            'success': False
        }
    return {
        'success': True
    }
    # print(
    #     f"File {source_file_name} uploaded to {destination_blob_name}."
    # )
