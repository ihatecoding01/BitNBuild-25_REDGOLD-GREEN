# Revuze Extension - Frontend Integration

This integration seamlessly connects the Revuze browser extension with both the backend API and a beautiful frontend dashboard.

## How It Works

### 1. Extension → Backend Integration
- Extension collects reviews from e-commerce sites (Amazon, Flipkart)
- Sends reviews to backend API (`POST /analyze`)
- Polls for results using job ID (`GET /results/{job_id}`)
- Displays analysis summary in extension popup

### 2. Extension → Frontend Integration
- After analysis completes, extension shows "View Detailed Analysis" button
- Clicking opens a beautiful HTML dashboard (`analysis-viewer.html`)
- Data is passed via localStorage bridge
- Dashboard displays rich analytics with charts and visualizations

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   E-commerce    │    │   Revuze        │    │   Backend       │
│   Website       │───▶│   Extension     │───▶│   API           │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Frontend      │
                       │   Dashboard     │
                       │                 │
                       └─────────────────┘
```

## Files Structure

### Extension Files:
- `manifest.json` - Extension configuration with necessary permissions
- `popup.js` - Main extension logic with backend integration
- `content_script.js` - Scrapes reviews from web pages
- `analysis-viewer.html` - Beautiful dashboard for detailed analysis
- `popup.html` - Extension popup interface

### Frontend Files (Optional):
- `frontend/` - Next.js dashboard (if you want to run a full frontend server)
- `analysis-viewer.html` - Standalone HTML viewer (already integrated in extension)

## Setup Instructions

1. **Start Backend**:
   ```bash
   cd backend
   python main.py
   ```

2. **Install Extension**:
   - Open Chrome
   - Go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `review_extension` folder

3. **Use Extension**:
   - Navigate to Amazon or Flipkart product page
   - Click the Revuze extension icon
   - Click "Analyze Reviews"
   - Wait for analysis to complete
   - Click "View Detailed Analysis" for full dashboard

## Data Flow

1. **Review Collection**: Content script extracts reviews from product pages
2. **Analysis Request**: Extension sends reviews to backend API
3. **Processing**: Backend processes reviews and returns sentiment analysis
4. **Quick View**: Extension popup shows summary results
5. **Detailed View**: HTML dashboard displays comprehensive analytics
6. **Data Bridge**: localStorage is used to pass data between extension and dashboard

## API Endpoints Used

- `GET /health` - Backend health check
- `POST /analyze` - Submit reviews for analysis
- `GET /results/{job_id}` - Get analysis results
- `GET /status/{job_id}` - Check analysis status

## Features

### Extension Popup:
- Purchase confidence score
- Authenticity assessment  
- Love/hate point analysis
- Category breakdown
- Sentiment chart
- Quick action buttons

### Detailed Dashboard:
- Interactive sentiment breakdowns
- Top positive/negative keywords
- Star rating visualization
- Source page information
- Professional styling with Tailwind CSS
- Responsive design

## Technical Details

- **Extension**: Manifest v3 Chrome extension
- **Backend**: FastAPI Python server
- **Dashboard**: Vanilla HTML/CSS/JS with Tailwind CSS
- **Data Transfer**: localStorage for extension-dashboard communication
- **Permissions**: Extension has access to active tab and backend API

## Troubleshooting

- Ensure backend is running on `http://localhost:8000`
- Check extension has proper permissions in Chrome
- Verify localStorage data is being stored correctly
- Use browser developer tools to debug any issues

This integration provides a seamless experience from review collection to detailed analysis visualization!