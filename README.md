# Monday BI Agent

An AI-powered Business Intelligence Assistant that connects to Monday.com to extract, analyze, and provide actionable insights from your business data. The agent answers natural language questions about pipeline health, revenue performance, work order status, and leadership metrics through a responsive chat interface.

## Features

- **Monday.com Integration** - Seamless connection to Monday.com using GraphQL API
- **Multi-Board Support** - Reads data from Deals Board and Work Orders Board
- **Data Processing** - Cleans, normalizes, and validates business data
- **Business Intelligence Analysis** - Performs pipeline, revenue, client, and work order analytics
- **Natural Language Interface** - Answers business questions in conversational English
- **Leadership Summary Generation** - Automated executive-level summaries
- **Responsive Chat Interface** - Modern, mobile-friendly web-based UI
- **Real-Time Data Refresh** - On-demand data synchronization from Monday.com

## Tech Stack

### Frontend
- HTML5
- CSS3 (responsive design)
- Vanilla JavaScript

### Backend
- Python 3.13.5
- Flask 3.0.0
- Flask-CORS

### Integration
- Monday.com GraphQL API

### Libraries
- `requests` - HTTP requests to Monday.com API
- `pandas` - Data processing and analysis
- `python-dotenv` - Environment variable management
- `flask-cors` - Cross-origin request handling

## Project Structure

```
Monday-BI-Agent/
├── backend/
│   ├── app.py                  # Flask application and API routes
│   ├── config.py               # Configuration and environment variables
│   ├── monday_client.py        # Monday.com GraphQL client
│   ├── data_processor.py       # Data cleaning and normalization
│   ├── business_analyzer.py    # Business intelligence analysis
│   ├── ai_agent.py             # Natural language intent mapping
│   ├── prompts.py              # Prompt templates
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Environment variables (not committed)
├── frontend/
│   ├── index.html              # Main chat interface
│   ├── style.css               # Responsive styles
│   └── script.js               # Chat interaction logic
└── README.md                   # This file
```

## Installation

### Prerequisites
- Python 3.13.5 or higher
- Monday.com account with API access
- A Monday.com workspace with Deals and Work Orders boards

### Setup Steps

1. **Clone the repository**
   ```bash
   cd d:\skylark_assignment\Monday-BI-Agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   
   On Windows (PowerShell):
   ```bash
   .venv\Scripts\Activate.ps1
   ```
   
   On macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Create a `.env` file in the `backend` directory with your Monday.com credentials:
   ```
   MONDAY_API_TOKEN=your_api_token_here
   MONDAY_API_URL=https://api.monday.com/graphql
   DEALS_BOARD_ID=your_deals_board_id
   WORK_ORDERS_BOARD_ID=your_work_orders_board_id
   OPENAI_API_KEY=your_openai_key_here (optional)
   ```

6. **Start the backend server**
   ```bash
   python app.py
   ```
   
   The API will be available at `http://127.0.0.1:5000`

7. **Open the frontend**
   
   Open `frontend/index.html` in your web browser, or serve it via a local web server:
   ```bash
   # Using Python
   python -m http.server 8000
   ```
   
   Then navigate to `http://localhost:8000/frontend/`

## Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `MONDAY_API_TOKEN` | Your Monday.com API token for authentication | Yes |
| `MONDAY_API_URL` | Monday.com GraphQL API endpoint (default: `https://api.monday.com/graphql`) | No |
| `DEALS_BOARD_ID` | Monday.com Board ID for deals data | Yes |
| `WORK_ORDERS_BOARD_ID` | Monday.com Board ID for work orders | Yes |
| `OPENAI_API_KEY` | OpenAI API key for enhanced AI responses (optional) | No |

**How to obtain Monday.com API Token:**
1. Go to your Monday.com workspace
2. Navigate to Admin → Developers → API
3. Generate a new API token
4. Copy and paste into your `.env` file

## API Endpoints

### `GET /`
Returns basic project information and status.

**Response:**
```json
{
  "project": "Monday BI Agent",
  "status": "running",
  "version": "1.0"
}
```

### `GET /health`
Health check endpoint to verify backend connectivity.

**Response:**
```json
{
  "status": "healthy",
  "monday_connection": "connected",
  "cache_status": "initialized"
}
```

### `GET /refresh`
Fetches and refreshes all data from Monday.com boards.

**Response:**
```json
{
  "status": "success",
  "message": "Data refreshed successfully",
  "deals_count": 346,
  "work_orders_count": 45
}
```

### `GET /summary`
Returns a comprehensive summary of business metrics.

**Response:**
```json
{
  "pipeline_summary": "...",
  "revenue_summary": "...",
  "work_order_summary": "...",
  "timestamp": "2026-07-21T16:07:37Z"
}
```

### `POST /ask`
Processes a natural language question and returns a BI-focused response.

**Request:**
```json
{
  "question": "How is our pipeline?"
}
```

**Response:**
```json
{
  "question": "How is our pipeline?",
  "answer": "📊 Pipeline Summary • Total Deals: 346 • Won Deals: 0 • Lost Deals: 0 • Open Deals: 0 • Win Rate: 0.0% • Pipeline Value: ₹0 • Average Deal Size: ₹0",
  "intent": "pipeline_health"
}
```

## Example Questions

The AI agent recognizes and responds to various natural language questions:

- **"How is our pipeline?"** - Pipeline health and deal metrics
- **"Leadership summary"** - Executive-level business overview
- **"Top clients"** - Key client information and metrics
- **"Revenue by sector"** - Revenue breakdown by business sector
- **"Delayed work orders"** - Work orders at risk or overdue
- **"Monthly pipeline"** - Monthly pipeline trends and forecasts
- **"How are sales?"** - Sales performance overview
- **"Executive summary"** - High-level business summary

## Future Improvements

- **OpenAI Integration** - Enhanced natural language understanding with GPT models
- **Data Visualization** - Charts, graphs, and dashboards for better insights
- **Authentication** - User authentication and role-based access control
- **Advanced Caching** - Redis-based caching for improved performance
- **Role-Based Dashboards** - Custom dashboards per user role
- **Predictive Analytics** - ML-based forecasting and trend analysis
- **Export Functionality** - Export reports as PDF or CSV
- **Mobile App** - Native mobile application
- **Historical Trending** - Time-series analysis of business metrics
- **Alerts & Notifications** - Proactive alerts for business anomalies

## Future Development

This project provides a solid foundation for an enterprise Business Intelligence platform. Potential enhancements include integration with additional data sources, advanced analytics, machine learning predictions, and comprehensive reporting capabilities.

## Author

[Your Name / Organization]

---

**Last Updated:** July 21, 2026

For questions or support, please refer to the Monday.com API documentation or contact your workspace administrator.
