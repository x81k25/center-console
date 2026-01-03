import os
from dotenv import load_dotenv

# Load .env file if it exists (for local development)
# In K8s, environment variables are injected directly
load_dotenv(override=False)

class Config:
    def __init__(self):
        self.rear_diff_host = os.getenv('REAR_DIFF_HOST')
        self.rear_diff_port = os.getenv('REAR_DIFF_PORT_EXTERNAL')
        self.rear_diff_prefix = os.getenv('REAR_DIFF_PREFIX', 'rear-diff')
        self.api_timeout = int(os.getenv('CENTER_CONSOLE_API_TIMEOUT', '30'))

        # MLflow configuration
        self.mlflow_host = os.getenv('CENTER_CONSOLE_MLFLOW_HOST')
        self.mlflow_port = os.getenv('CENTER_CONSOLE_MLFLOW_PORT')
        self.mlflow_username = os.getenv('CENTER_CONSOLE_MLFLOW_USERNAME')
        self.mlflow_password = os.getenv('CENTER_CONSOLE_MLFLOW_PASSWORD')
        
        self._validate_config()
        
    def _validate_config(self):
        """Validate required configuration values"""
        missing = []
        
        if not self.rear_diff_host:
            missing.append('REAR_DIFF_HOST')
        if not self.rear_diff_port:
            missing.append('REAR_DIFF_PORT_EXTERNAL')
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @property
    def base_url(self):
        """Construct the base URL for the API"""
        return f"http://{self.rear_diff_host}:{self.rear_diff_port}/{self.rear_diff_prefix}/"
    
    @property
    def training_endpoint(self):
        """Get the training data endpoint"""
        return f"{self.base_url}training"
    
    @property
    def health_endpoint(self):
        """Get the health check endpoint"""
        return f"{self.base_url}health"
    
    def get_training_update_endpoint(self, imdb_id):
        """Get the training update endpoint for a specific IMDB ID"""
        return f"{self.base_url}training/{imdb_id}"
    
    def get_media_pipeline_endpoint(self, hash_id):
        """Get the media pipeline patch endpoint for a specific hash ID"""
        return f"{self.base_url}media/{hash_id}/pipeline"

    def get_training_would_not_watch_endpoint(self, imdb_id):
        """Get the training would_not_watch endpoint for a specific IMDB ID"""
        return f"{self.base_url}training/{imdb_id}/would_not_watch"

    def get_training_would_watch_endpoint(self, imdb_id):
        """Get the training would_watch endpoint for a specific IMDB ID"""
        return f"{self.base_url}training/{imdb_id}/would_watch"
    
    @property
    def media_endpoint(self):
        """Get the media data endpoint"""
        return f"{self.base_url}media/"
    
    @property
    def flyway_endpoint(self):
        """Get the flyway history endpoint"""
        return f"{self.base_url}flyway"

    @property
    def mlflow_base_url(self):
        """Construct the base URL for MLflow API"""
        if not self.mlflow_host or not self.mlflow_port:
            return None
        return f"http://{self.mlflow_host}:{self.mlflow_port}"

    @property
    def mlflow_auth(self):
        """Get MLflow basic auth tuple"""
        if not self.mlflow_username or not self.mlflow_password:
            return None
        return (self.mlflow_username, self.mlflow_password)