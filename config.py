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
    
    def get_label_update_endpoint(self, imdb_id):
        """Get the label update endpoint for a specific IMDB ID"""
        return f"{self.base_url}training/{imdb_id}/label"
    
    @property
    def media_endpoint(self):
        """Get the media data endpoint"""
        return f"{self.base_url}media/"