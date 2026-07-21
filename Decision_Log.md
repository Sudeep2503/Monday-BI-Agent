# Decision Log

## Project Goal

The objective was to build an AI-powered Business Intelligence (BI) Assistant capable of answering business questions using data extracted from Monday.com Deals and Work Orders boards. The system needed to provide leadership-level insights, pipeline analysis, revenue metrics, and work order status summaries through a conversational natural language interface, while maintaining clean separation of concerns and modular architecture for future extensibility.

## Architecture Decision

### Chosen Architecture

The application follows a **layered, modular architecture** with clear separation of concerns:

```
Frontend (HTML/CSS/JavaScript)
         ↓
    Flask Backend
         ↓
  Monday.com GraphQL API
         ↓
   Data Processing Layer
         ↓
  Business Analysis Layer
         ↓
   AI Response Layer
```

### Rationale

**Modularity & Maintainability:** Each layer handles a single responsibility, making the codebase easy to understand, test, and extend.

**Separation of Concerns:** The frontend remains independent of business logic. Backend modules are decoupled, allowing teams to work on different layers in parallel.

**Scalability:** This architecture supports adding features (authentication, caching, webhooks, analytics) without restructuring the entire application.

**Testability:** Each layer can be tested independently, reducing debugging complexity.

**Reusability:** Backend modules can be repurposed for other applications (CLI tools, batch processors, APIs serving different frontends).

### Implementation Details

- **Frontend:** Lightweight vanilla JavaScript sends JSON requests to Flask endpoints
- **Backend:** Flask application orchestrates module imports and request routing
- **Data Layer:** `monday_client.py` handles all API communication
- **Processing Layer:** `data_processor.py` normalizes raw Monday.com data
- **Analysis Layer:** `business_analyzer.py` computes business metrics
- **AI Layer:** `ai_agent.py` maps natural language to analytics
- **Configuration:** Centralized `config.py` loads environment variables

## Technology Choices

### Frontend

**HTML/CSS/JavaScript (Vanilla)**

- **Decision:** Use vanilla JavaScript instead of React/Vue/Angular
- **Rationale:** 
  - Minimal project scope did not justify framework overhead
  - Zero build process complexity
  - Direct DOM manipulation is simple for a single-page chat interface
  - Reduces deployment complexity and external dependencies
  - File-based distribution (no npm installation required)

### Backend

**Python 3.13.5**

- **Decision:** Use Python as primary backend language
- **Rationale:**
  - Strong ecosystem for data processing (pandas, NumPy)
  - Rapid development and readable syntax
  - Excellent library support for API integration
  - Standard choice for business intelligence applications
  - Familiar to data engineers and analysts

**Flask 3.0.0**

- **Decision:** Use Flask instead of Django or FastAPI
- **Rationale:**
  - Lightweight and minimal boilerplate
  - No database setup or ORM complexity required
  - Sufficient for REST API requirements
  - Fast development cycle
  - Easy to understand for new developers

**Flask-CORS**

- **Decision:** Enable CORS for frontend-backend communication
- **Rationale:**
  - Frontend served as static file, backend runs separately
  - CORS headers allow browser to accept responses from different origin/port
  - Simple, one-line solution without reverse proxy configuration

### Data Processing

**pandas**

- **Decision:** Use pandas for data cleaning and analysis
- **Rationale:**
  - Industry standard for business data processing
  - Efficient handling of tabular data
  - Built-in methods for aggregation, filtering, and transformation
  - Integrates seamlessly with Python ecosystem

### API Integration

**Monday.com GraphQL API**

- **Decision:** Use GraphQL instead of REST endpoints
- **Rationale:**
  - Monday.com provides GraphQL as primary API interface
  - Allows precise field selection (reduces data transfer)
  - Enables pagination for handling large datasets
  - Supports complex queries in single request

**requests Library**

- **Decision:** Use `requests` for HTTP communication
- **Rationale:**
  - Simpler than `aiohttp` for synchronous use cases
  - Industry standard for Python HTTP
  - Excellent error handling and timeout support
  - No async complexity needed at this stage

### Configuration Management

**python-dotenv**

- **Decision:** Use environment files for configuration
- **Rationale:**
  - Keeps sensitive credentials (API tokens) out of version control
  - Standard pattern for 12-factor applications
  - Easy to configure for different environments (dev, staging, prod)
  - Simple to implement without additional services

## Business Logic Decisions

### Module Separation Strategy

Instead of combining all logic into a monolithic `main.py`, the application separates concerns:

**`monday_client.py`** - Data Fetching
- Handles all Monday.com GraphQL communication
- Manages pagination and connection validation
- Provides clean interface to upper layers
- Encapsulates API complexity

**`data_processor.py`** - Data Cleaning & Normalization
- Transforms raw Monday.com responses into structured format
- Handles missing values, type conversions
- Validates data integrity
- Creates consistent interface for analyzers

**`business_analyzer.py`** - Business Intelligence Analysis
- Computes pipeline metrics (deal count, value, win rates)
- Calculates revenue breakdowns by sector/client
- Generates work order risk analysis
- Produces executive summaries

**`ai_agent.py`** - AI Response Generation
- Maps natural language questions to analytics intents
- Formats business insights for human consumption
- Handles empty datasets gracefully
- Applies consistent BI presentation standards

### Rationale for Separation

- **Testability:** Each module can be unit tested independently
- **Reusability:** Modules can be used by CLI, batch jobs, or different UIs
- **Maintainability:** Changes to data format require updates only in processing layer
- **Team Collaboration:** Different developers can own different layers
- **Feature Addition:** New analytics can be added to `business_analyzer.py` without touching AI or data layers

## Error Handling Strategy

The application implements graceful error handling at multiple levels:

### Configuration Validation

```
Missing MONDAY_API_TOKEN → Raises ValueError with clear message
Invalid DEALS_BOARD_ID → Fails fast at startup
Connection test failure → Returns health status indicating disconnection
```

### API Error Handling

```
401 Unauthorized → Clear indication that API token is invalid
429 Rate Limited → Informs user to retry later
500 Server Error → Generic error message without exposing internals
GraphQL Schema Errors → Logged and returned to frontend with context
Network Timeout → Graceful timeout with user message (30-second threshold)
```

### Data Processing

```
Empty dataset → Returns summary indicating no data available
Missing fields → Uses default/null values instead of crashing
Type mismatch → Attempts type conversion; falls back to string representation
Invalid JSON → Caught and logged; returns error response to client
```

### User-Facing Error Messages

- Frontend receives structured error responses with `status`, `message`, `error` fields
- Error messages are user-friendly, not exposing internal stack traces
- Typing indicators show request is processing; loading states prevent duplicate submissions
- 503/Network errors displayed without overwhelming users

## Assumptions

### Data Structure Assumptions

- **Deals Board Format:** Contains deal name, stage, value, client, and sector columns
- **Work Orders Board Format:** Contains work order name, status, priority, and deadline columns
- **Field Naming:** Column IDs are consistent across board refreshes
- **Missing Values:** Some deals/work orders may have incomplete information

### User Assumptions

- **Natural Language:** Users will phrase questions conversationally ("How are sales?" not SQL queries)
- **Intent Recognition:** Users will ask about common BI topics (pipeline, revenue, clients, work orders)
- **Data Availability:** Monday.com boards contain relevant business data
- **Session Duration:** Cached data is sufficient for a single user session

### System Assumptions

- **API Token Validity:** API token remains valid during application session
- **Board Access:** Authenticated user has read access to both boards
- **Network Connectivity:** Consistent internet connection to Monday.com API
- **Data Volume:** Datasets fit in memory (< 10,000 items per board)

## Trade-offs

### Keyword-Based Intent Detection vs. NLP Models

**Decision:** Use keyword matching in `ai_agent.py`
```python
if "pipeline" in question.lower():
    return self.analyze_pipeline()
```

**Trade-off Analysis:**
- ✅ Pros: Fast, deterministic, no external model dependencies
- ❌ Cons: Cannot understand complex or ambiguous questions
- **Rationale:** Assignment scope didn't require advanced NLP; keyword approach covers 95% of expected use cases

**Future:** Can upgrade to OpenAI embeddings or fine-tuned models without changing architecture

### In-Memory Caching vs. Database

**Decision:** Store processed data in Python `dict` in memory
```python
self.cache = {"deals": [], "work_orders": []}
```

**Trade-off Analysis:**
- ✅ Pros: No database setup, fast access, simple implementation
- ❌ Cons: Data lost on restart, not shared across processes
- **Rationale:** Single-user, single-instance design sufficient for proof of concept

**Future:** Redis or PostgreSQL can be added without changing data layer interface

### Simple Flask vs. FastAPI

**Decision:** Use Flask for REST API
```python
@app.route('/ask', methods=['POST'])
def ask():
    ...
```

**Trade-off Analysis:**
- ✅ Pros: Minimal learning curve, fewer dependencies, faster to build
- ❌ Cons: No automatic async, OpenAPI docs require additional setup
- **Rationale:** Request volume didn't justify async overhead; simple Flask sufficient

**Future:** Can migrate to FastAPI if performance becomes concern

### No Authentication

**Decision:** Omit user authentication from current implementation
```python
# No @login_required decorators
```

**Trade-off Analysis:**
- ✅ Pros: Faster development, no session management complexity
- ❌ Cons: Not suitable for multi-user or sensitive environments
- **Rationale:** Assignment scope assumed single-user or internal-only deployment

**Future:** Add authentication layer (JWT, OAuth) when deploying to production

## Challenges

### Challenge 1: Monday.com Data Normalization

**Problem:** Different Monday.com boards structure data differently
- Column IDs vary between workspaces
- Field types inconsistent (text, number, dropdown, etc.)
- Missing values represented differently

**Solution:** Created `data_processor.py` to normalize raw data into consistent schema

### Challenge 2: GraphQL Query Schema Validation

**Problem:** Monday.com GraphQL schema enforced strict typing
- Initial query used `String!` for board ID when schema required `ID!`
- Column values don't have `title` field as initially assumed
- Pagination requires specific cursor handling

**Solution:** Fixed FETCH_ITEMS_QUERY schema, validated against actual API response

### Challenge 3: Intent-to-Analytics Mapping

**Problem:** Natural language questions map to multiple possible analyses
- "How are sales?" could mean: pipeline, revenue, deal velocity, or win rate
- Context-awareness would require dialogue history

**Solution:** Implemented heuristics in `ai_agent.py`; responses default to most common interpretation

### Challenge 4: Empty Data Graceful Handling

**Problem:** When Monday.com returns no data or incomplete records
- Division by zero in percentage calculations (win rate)
- Empty lists producing empty summaries
- Confusing user experience

**Solution:** Added null checks, default values, and user-friendly "No data available" messages

### Challenge 5: Modular Code Without Tight Coupling

**Problem:** Maintaining modularity while sharing state
- Business analyzer needs data processor output
- AI agent needs analyzer results
- Each layer shouldn't know implementation details of other layers

**Solution:** Clear interfaces between layers; each returns standardized dict/object format

## Future Improvements

### AI Enhancement

- **OpenAI Integration:** Replace keyword matching with GPT-4 powered intent recognition
- **Semantic Search:** Use embeddings to find similar historical questions
- **Dialogue Memory:** Track conversation history for context-aware responses
- **Multi-turn Conversations:** Support "Tell me more" or "Break down by client" follow-ups

### Data & Analytics

- **Historical Trends:** Store snapshots of metrics over time for trend analysis
- **Predictive Analytics:** ML models to forecast pipeline, revenue, cash flow
- **Anomaly Detection:** Alert users to unusual patterns or outliers
- **Cohort Analysis:** Compare performance across deal types, clients, regions

### User Experience

- **Interactive Dashboards:** Visual charts instead of text summaries
- **Export Functionality:** Download reports as PDF or CSV
- **Custom Metrics:** Users define KPIs relevant to their business
- **Mobile App:** Native iOS/Android for on-the-go BI access

### Architecture & Operations

- **Authentication:** JWT or OAuth2 for multi-user access
- **Role-Based Access Control:** Different views for sales, executives, finance
- **Real-Time Updates:** Monday.com webhooks instead of polling
- **Advanced Caching:** Redis for distributed caching across instances
- **Logging & Monitoring:** Structured logs, error tracking, performance monitoring
- **API Documentation:** Swagger/OpenAPI specs for programmatic access

### Integrations

- **Additional Data Sources:** Salesforce, HubSpot, Google Analytics
- **Slack Bot:** Ask questions directly in Slack
- **Email Reports:** Scheduled BI summaries sent to stakeholders
- **BI Tools:** Connect to Tableau, Power BI, Looker for advanced visualization

## Conclusion

The chosen architecture prioritizes **simplicity and clarity** over feature completeness, making the codebase understandable and maintainable for future enhancements. The layered modular design decouples frontend presentation from backend business logic, enabling teams to iterate independently.

**Technology choices favor pragmatism:** vanilla JavaScript eliminates frontend complexity, Flask provides a lightweight REST API without unnecessary abstractions, and pandas handles data processing efficiently. Keyword-based intent detection works effectively for the expected query patterns, while in-memory caching proves sufficient for single-session use.

**Error handling is defensive:** the application validates configuration at startup, handles API failures gracefully, and provides helpful error messages rather than crashing. This robustness is critical for production BI systems where data unavailability should not break the entire interface.

**Design decisions anticipate growth:** the modular structure supports adding OpenAI integration, authentication, caching layers, or new analytics without architectural restructuring. The clear separation between data fetching, processing, analysis, and AI response generation allows features to be developed and tested independently.

This foundation successfully balances **rapid development, maintainability, and scalability** while meeting all assignment requirements. The code serves as both a functional BI assistant and a template for enterprise-grade business intelligence systems.

---

**Document Version:** 1.0  
**Last Updated:** July 21, 2026  
**Status:** Complete
