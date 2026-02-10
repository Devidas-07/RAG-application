from minio import Minio
from minio.error import S3Error
from app.core.config import config
import io

class MinIOClient:
    """MinIO client for document storage"""
    
    def __init__(self):
        self.client = Minio(
            config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=False
        )
        self.bucket = config.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"Bucket '{self.bucket}' created")
        except S3Error as e:
            print(f"MinIO error: {e}")
    
    def upload_file(self, file_path: str, object_name: str = None):
        """Upload a file to MinIO"""
        if object_name is None:
            object_name = file_path.split("/")[-1]
        
        try:
            self.client.fput_object(self.bucket, object_name, file_path)
            print(f"File '{file_path}' uploaded as '{object_name}'")
            return object_name
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return None
    
    def download_file(self, object_name: str, file_path: str = None):
        """Download a file from MinIO"""
        try:
            if file_path is None:
                file_path = object_name
            self.client.fget_object(self.bucket, object_name, file_path)
            print(f"File '{object_name}' downloaded to '{file_path}'")
            return file_path
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return None
    
    def get_file_bytes(self, object_name: str):
        """Get file content as bytes"""
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            return data
        except S3Error as e:
            print(f"Error retrieving file: {e}")
            return None
    
    def list_objects(self, prefix: str = ""):
        """List all objects in bucket"""
        try:
            objects = self.client.list_objects(self.bucket, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing objects: {e}")
            return []
    
    def delete_object(self, object_name: str):
        """Delete an object from MinIO"""
        try:
            self.client.remove_object(self.bucket, object_name)
            print(f"File '{object_name}' deleted")
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False

# Lazy client proxy
_minio_client_instance = None

class LazyMinIOClientProxy:
    """Lazy proxy that creates MinIOClient only when first accessed"""
    
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        global _minio_client_instance
        if _minio_client_instance is None:
            _minio_client_instance = MinIOClient()
        return _minio_client_instance
    
    def __getattr__(self, name):
        return getattr(self._get_client(), name)

minio_client = LazyMinIOClientProxy()
