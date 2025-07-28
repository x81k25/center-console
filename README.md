# Center Console - Media Management Dashboard

A Streamlit-based web application for managing the Rear Differential media processing pipeline. This application provides multiple interfaces for reviewing training data, analyzing ML predictions, browsing media collections, and monitoring system health.

## Features

### 🎬 Media Pipeline Management
- Search media items by hash or title
- View and update pipeline status (`ingested`, `parsed`, `rejected`, `downloading`, `complete`, etc.)
- Manage error conditions and rejection status
- Color-coded status indicators with icons

### 📚 Training Backlog Review
- Review unreviewed movies from the training dataset
- Binary classification: `would_watch` vs `would_not_watch`
- Display movie metadata (RT score, IMDB votes, genre, country, year)
- Expandable details with comprehensive movie information
- Auto-refresh after each review decision

### 🔍 Prediction Anomalies Analysis
- Review ML model predictions with confusion matrix filtering
- Analyze false positives and false negatives for model improvement
- Update labels for mispredicted items
- Display prediction probability and actual vs predicted labels
- Filter by: All, False Positives, False Negatives, True Positives, True Negatives
- Sortable by prediction confidence (high to low / low to high)

### 🎬 Media Library Browser
- Browse complete media collection with pagination
- View detailed metadata for movies and TV shows
- Pipeline status tracking and error monitoring
- Search and filter capabilities

### 🗃️ Database Migration History
- View Flyway migration history and status
- Track successful and failed migrations
- Monitor database schema changes over time

### 🔧 Debug Features
- **API Call Visibility**: All pages display the exact API URL being called
- **Real-time Parameter Display**: See API parameters update as you change filters/sorts
- **Response Debugging**: Monitor API responses for troubleshooting

## Quick Start

### Prerequisites
- Python 3.9 or higher
- uv package manager (recommended)
- Docker (for containerized deployment)

### Local Installation

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and enter the project directory
cd center-console

# Install dependencies using uv
uv sync

# Create .env file for local development
cat > .env << EOF
REAR_DIFF_HOST=192.168.50.2
REAR_DIFF_PORT_EXTERNAL=30812
REAR_DIFF_PREFIX=rear-diff
CENTER_CONSOLE_API_TIMEOUT=30
EOF

# Run the application
uv run streamlit run app.py
```

The application will be available at http://localhost:8501

### Adding New Dependencies

```bash
# Add a new package
uv add <package-name>

# Add a development dependency  
uv add --dev <package-name>

# Install dependencies after adding
uv sync
```

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

## API Integration

### Endpoints Used

**Training Data**:
- `GET /rear-diff/training` - Fetch training data with filters
- `PATCH /rear-diff/training/{imdb_id}/label` - Update label and mark as reviewed
- `PATCH /rear-diff/training/{imdb_id}/reviewed` - Mark as reviewed only

**Prediction Data**:
- `GET /rear-diff/prediction/` - Fetch ML predictions with cm_value filtering

**Media Data**:
- `GET /rear-diff/media/` - Browse media collection
- `PATCH /rear-diff/media/{hash_id}/pipeline` - Update pipeline status

**System Health**:
- `GET /rear-diff/flyway/` - Database migration history
- `GET /rear-diff/health` - Health check endpoint

### Query Parameters

**Training Backlog**:
- `limit=20`, `sort_by=updated_at`, `sort_order=desc`
- `reviewed=false`, `media_type=movie`

**Prediction Anomalies**:
- `limit=20`, `sort_by=probability`, `sort_order=asc|desc`
- `cm_value=tp|tn|fp|fn` (optional filter)

**Media Browser**:
- `page=1`, `limit=20`, `sort_by=updated_at`, `sort_order=desc`

## File Structure

```
├── app.py                    # Main Streamlit homepage
├── pages/                    # Streamlit pages
│   ├── training_backlog.py   # Training data review interface
│   ├── prediction_anomalies.py # ML prediction analysis
│   ├── get_media.py          # Media collection browser
│   ├── get_flyway_migrations.py # Database migration history
│   └── media_pipeline.py     # Pipeline status management
├── config.py                 # Configuration management
├── pyproject.toml           # Project dependencies and metadata
├── uv.lock                  # Dependency lock file
├── Dockerfile               # Docker container configuration
├── .env                     # Local environment variables (not in git)
├── CLAUDE.md               # Project documentation
└── README.md               # This file
```

## Usage

### Training Backlog Page
1. Review unreviewed movies one by one
2. Click "would_watch" (blue) or "would_not" (red) buttons
3. Expand details to see full movie metadata
4. Items are automatically marked as reviewed after labeling

### Prediction Anomalies Page
1. Filter by confusion matrix value (tp/tn/fp/fn)
2. Sort by prediction confidence (high to low / low to high)
3. Review model predictions vs actual labels
4. Update labels for mispredicted items to improve training data

### Media Library Page
1. Browse paginated media collection
2. Adjust page size and navigate through pages
3. View detailed metadata and pipeline status
4. Monitor processing status and errors

### API Debug Features
- Each page shows the exact API URL being called
- Parameters update in real-time as you change filters
- Use displayed URLs for direct API testing and troubleshooting

## Development

### Architecture
- **Multi-page Streamlit app** with sidebar navigation
- **config.py**: Centralized configuration and endpoint management
- **pyproject.toml**: Modern Python dependency management with uv
- **No caching on prediction_anomalies**: Fresh API calls on every parameter change
- **Real-time API URL display**: Debugging and testing visibility

### Key Implementation Details
- **Server-side filtering**: Uses API parameters instead of client-side filtering
- **Dynamic UI updates**: Real-time parameter changes trigger fresh API calls
- **Error handling**: Graceful API failure handling with user guidance
- **Modern tooling**: uv for fast dependency management and virtual environments

### Performance Considerations
- Strategic caching on some pages (training_backlog: 5min TTL)
- No caching on prediction_anomalies for real-time debugging
- Pagination prevents large dataset memory issues
- Minimal dependencies keep container size small

## Implementation Status

✅ **Completed Features**
- Multi-page Streamlit application with sidebar navigation
- Training backlog review with binary classification
- Prediction anomaly analysis with confusion matrix filtering
- Media collection browser with pagination and status tracking
- Database migration history viewer
- Pipeline status management interface
- Real-time API URL display on all pages
- Modern dependency management with pyproject.toml and uv
- Docker containerization with uv-based builds
- Comprehensive error handling and user feedback
- Environment variable validation and configuration management