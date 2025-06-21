# Rear Diff Training Data Viewer

A Streamlit application for viewing and managing training data from the Rear Differential API. This application provides an interactive interface for browsing, sorting, and updating training data labels used in the Rear Differential system.

## Features

- **Dynamic Data Display**: Automatically generates table columns based on API response structure
- **Label Management**: Edit labels inline with dropdown selection populated from existing values
- **Advanced Pagination**: Navigate through large datasets with customizable page sizes (25/50/100 records)
- **Column Controls**: Sort by any column, filter visible columns, and customize display
- **Real-time Updates**: Instant feedback for label updates with automatic data refresh
- **Robust Error Handling**: Comprehensive error messages and recovery guidance
- **API Response Caching**: 5-minute TTL cache for improved performance

## Requirements

### Core Functionality

**Data Display**
- Fetch training data from `GET /rear-diff/training` endpoint
- Dynamically generate table columns based on API response structure
- Display data in interactive table/dataframe with all available fields
- Implement pagination controls (limit/offset parameters)

**Label Management**
- Dynamically populate label dropdown options from existing column values
- Convert `label` column to editable dropdown widgets
- Update labels via `PATCH /rear-diff/training/{imdb_id}/label` endpoint
- Provide visual feedback for successful/failed updates

**Streamlit Error Handling**
- Use `st.error()` for startup failures (missing env vars, API connectivity)
- Use `st.warning()` for partial failures (individual record updates)
- Use `st.info()` for loading states and operation feedback
- Display clear instructions for fixing configuration issues

**Dynamic Features**
- Column sorting: `st.dataframe()` with sortable=True
- Column selection: `st.multiselect()` for visible columns
- Default sort parameter: `sort_by=updated_at&sort_order=desc`
- Auto-generate filter options from current dataset

**Error Handling**
- Fail-fast startup with user-friendly error messages in Streamlit UI
- Environment variable validation with clear instructions
- API connectivity checks with retry guidance
- Graceful degradation for partial API failures

### Technical Requirements

**API Integration**
- Base URL via environment variable (e.g., `http://192.168.50.2:30812/rear-diff/`)
- Error handling for API failures (500, 404, 400 responses)
- Request timeout handling
- API response validation
- No authentication required (internal network deployment)

**UI/UX**
- Graceful error display via Streamlit UI for startup/connection failures
- Human-readable error messages for configuration issues
- Loading states during API calls
- Success notifications for label updates
- Sortable columns (default: updated_at DESC)
- Column visibility controls for customizable display
- Pagination navigation (25 records per page)

**Data Handling**
- Cache API responses (5-minute TTL)
- Pagination: 25 records per page default
- Validate IMDB ID format (tt + 7-8 digits) before PATCH
- Default sort: `updated_at DESC`

## Quick Start

### Prerequisites
- Python 3.11 or higher
- uv package manager (optional but recommended)
- Docker (for containerized deployment)

### Local Installation

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
# OR without uv:
# pip install -r requirements.txt

# Create .env file for local development
cat > .env << EOF
REAR_DIFF_HOST=192.168.50.2
REAR_DIFF_PORT=30812
REAR_DIFF_PATH=/rear-diff/
API_TIMEOUT=30
EOF

# Run the application
streamlit run app.py
```

The application will be available at http://localhost:8501

## Docker Deployment

### Build and Run with Docker

```bash
# Build the Docker image
docker build -t center-console .

# Run the container
docker run -d \
  --name center-console \
  -p 8501:8501 \
  -e REAR_DIFF_HOST=192.168.50.2 \
  -e REAR_DIFF_PORT=30812 \
  -e REAR_DIFF_PATH=/rear-diff/ \
  -e API_TIMEOUT=30 \
  center-console

# View logs
docker logs center-console

# Stop and remove container
docker stop center-console
docker rm center-console
```

### Kubernetes Deployment

For Kubernetes deployment on bare-metal clusters:
- Internal network only (no external exposure required)
- Configure environment variables via ConfigMap or namespace configuration
- No authentication/authorization required for internal API access
- Service should expose port 8501

## Configuration

**Environment Variables**
- `REAR_DIFF_HOST`: API host address (e.g., `192.168.50.2`)
- `REAR_DIFF_PORT`: API port number (e.g., `30812`)
- `REAR_DIFF_PATH`: API base path (e.g., `/rear-diff/`)
- `API_TIMEOUT`: Request timeout in seconds (default: 30)

**Environment Management**
- Local development: `.env` file with `python-dotenv`
- K8s deployment: Environment variables via namespace configuration

**API Documentation**
- Full API docs: `http://{HOST}:{PORT}{PATH}openapi.json`
- Interactive docs: `http://{HOST}:{PORT}{PATH}docs`
- Health check: `GET http://{HOST}:{PORT}{PATH}health`

## File Structure

```
├── app.py              # Main Streamlit application
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker container configuration
├── .env               # Local environment variables (not in git)
├── CLAUDE.md          # Project documentation and deployment report
└── readme.md          # This file
```

## Usage

### Application Interface

1. **Data Table**: Browse training data with all available fields displayed dynamically
2. **Pagination Controls**: Navigate through records with customizable page sizes
3. **Sorting**: Click column headers or use sort controls to order data
4. **Column Visibility**: Select which columns to display using the multiselect control
5. **Label Editing**: Use dropdown menus to update labels for individual records
6. **Save Changes**: Click "Save" buttons to commit label updates via API

### API Endpoints Used

- `GET /rear-diff/training` - Fetch paginated training data
- `PATCH /rear-diff/training/{imdb_id}/label` - Update label for specific record  
- `GET /rear-diff/health` - Health check endpoint

### Troubleshooting

**Configuration Errors**: Application will display clear error messages with setup instructions if environment variables are missing or API is unreachable.

**Performance**: Large datasets are handled through pagination and response caching. Adjust page size if needed for your dataset size.

**Label Updates**: If label updates fail, check network connectivity and API logs. The application validates IMDB ID format before attempting updates.

## Implementation Status

✅ **Completed Features**
- Dynamic data table generation from API response
- Pagination with customizable page sizes (25/50/100)
- Column sorting and visibility controls
- Label management with dropdown selection
- Real-time label updates via PATCH API
- Comprehensive error handling and user feedback
- API response caching (5-minute TTL)
- Environment variable validation
- Docker containerization
- Local and containerized deployment tested

## Development Notes

### Architecture
- **app.py**: Main Streamlit application with UI components and API integration
- **config.py**: Environment configuration and validation with endpoint construction
- **requirements.txt**: Minimal dependency list for production deployment
- **Dockerfile**: Multi-stage build optimized for container deployment

### Key Implementation Details
- **Dynamic columns**: Table structure adapts automatically to API response schema
- **Session state**: Tracks pending label changes before API submission
- **Cache invalidation**: Automatic refresh after successful updates
- **Error boundaries**: Graceful handling of API failures with user guidance
- **IMDB ID validation**: Format checking (tt + 7-8 digits) before PATCH requests

### Performance Considerations
- 5-minute response caching reduces API load
- Pagination prevents large dataset memory issues
- Minimal dependencies keep container size small
- Session state prevents unnecessary re-renders