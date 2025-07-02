# Center Console - Training Backlog Viewer

A Streamlit application for viewing and managing the training backlog from the Rear Differential API. This application provides an interactive interface for reviewing unreviewed movies and updating their watch labels.

## Features

- **Training Backlog Display**: Shows 20 unreviewed movies sorted by updated_at (descending)
- **Label Toggle Button**: Flip between "would_watch" (blue) and "would_not_watch" (red) labels
- **Confirm Button**: Mark items as reviewed without changing the label
- **Auto-refresh**: Automatically fetches new items after each action
- **Backlog Status**: Shows "Backlog cleared" when no unreviewed items remain
- **Real-time Updates**: Instant feedback with automatic data refresh
- **API Response Caching**: 5-minute TTL cache for improved performance

## How It Works

1. **Query Training Endpoint**: Fetches 20 unreviewed movies (`reviewed=false`, `media_type=movie`) sorted by `updated_at` descending
2. **Display Items**: Shows `media_title`, `rt_score`, and `imdb_votes` for each movie
3. **Label Button**: 
   - Shows current label value ("would_watch" in blue, "would_not_watch" in red)
   - Clicking flips the label value and marks item as `human_labeled=true` and `reviewed=true`
4. **Confirm Button**: Marks item as `reviewed=true` without changing the label
5. **Auto-refresh**: After any button click, fetches fresh data from the API
6. **Completion**: Shows "Backlog cleared" when no unreviewed items remain

### API Integration

**Endpoints Used**:
- `GET /rear-diff/training` - Fetch training data with filters
- `PATCH /rear-diff/training/{imdb_id}/label` - Update label and mark as reviewed
- `PATCH /rear-diff/training/{imdb_id}/reviewed` - Mark as reviewed only

**Query Parameters**:
- `limit=20` - Number of items to fetch
- `sort_by=updated_at` - Sort field
- `sort_order=desc` - Sort direction  
- `reviewed=false` - Filter unreviewed items
- `media_type=movie` - Filter movies only

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
REAR_DIFF_PORT_EXTERNAL=30812
REAR_DIFF_PREFIX=rear-diff
CENTER_CONSOLE_API_TIMEOUT=30
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
  -e REAR_DIFF_PORT_EXTERNAL=30812 \
  -e REAR_DIFF_PREFIX=rear-diff \
  -e CENTER_CONSOLE_API_TIMEOUT=30 \
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
- `REAR_DIFF_PORT_EXTERNAL`: API port number (e.g., `30812`)
- `REAR_DIFF_PREFIX`: API base path without slashes (e.g., `rear-diff`)
- `CENTER_CONSOLE_API_TIMEOUT`: Request timeout in seconds (default: 30)

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