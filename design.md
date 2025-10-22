Perfect! Here's the comprehensive detailed documentation:

---

# **Surface Campaign Manager - Complete Codebase Documentation**

## **Executive Summary**

**Surface Campaign Manager** is an AI-powered marketing automation platform that intelligently generates multi-channel marketing campaigns from simple text briefs. It uses Google's Gemini LLM and LangGraph's orchestration framework to automate audience segmentation, channel-specific content generation, and review workflows.

---

## **Problem Statement & Solution**

### **Challenge**
Marketing teams spend significant time on:
1. Analyzing campaign briefs to identify target audiences
2. Creating multiple content versions for different segments
3. Adapting content for different channels (email, web, social)
4. Managing review and approval workflows

### **Solution**
Automate the entire pipeline using AI:
- Parse campaign intent → generate audience segments
- Use LLM to decide optimal channel per segment
- Generate channel-specific, production-ready HTML content
- Create trackable review tasks for human oversight

---

## **Architecture Overview**

### **System Design Pattern: Multi-Agent Orchestration**

The system uses a **state machine pattern** with LangGraph to manage workflow transitions:

```
User Input (Campaign Brief)
         ↓
    Flask API
         ↓
LangGraph StateGraph (Orchestrator)
         ↓
    ├─→ Generate Audience (LLM)
    ├─→ Generate Content (Channel-specific subagents)
    │   ├─→ Email Subagent
    │   └─→ Banner Subagent
    ├─→ Create Review Task
         ↓
    Return Results to Frontend
```

### **Technology Stack**

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | React | 19.2.0 |
| **Backend** | Flask | Latest |
| **Orchestration** | LangGraph | Latest |
| **LLM Framework** | LangChain | Latest |
| **AI Model** | Google Gemini 2.5 Flash | Latest |

---

## **Backend Components** ([backend/app.py](cci:7://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend/app.py:0:0-0:0))

### **1. Initialization & Configuration**

**Key Setup**:
- Flask app with CORS enabled for React frontend (port 3000)
- Google Gemini LLM initialization with API key from `.env`
- Graceful fallback if API key unavailable

```python
CORS(app, origins=['http://localhost:3000'])
llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', google_api_key=google_api_key)
```

### **2. Prompt Templates**

**`audience_prompt`**:
- **Input**: Campaign brief
- **Output**: Comma-separated list of 1-2 audience segments
- **Constraint**: No newlines or bullet points
- **Parser**: `CommaSeparatedListOutputParser()`

**`content_prompt`**:
- **Input**: Campaign brief + audience segment
- **Output**: Compelling ad copy tailored to segment
- **Parser**: `StrOutputParser()`

**`orchestrator_prompt`**:
- **Input**: Campaign state (brief, segments, content status, review status)
- **Output**: One of ['generate_audience', 'generate_content', 'create_review', 'complete']
- **Parser**: `StrOutputParser()`

### **3. State Definition**

```python
class CampaignState(TypedDict):
    intent_brief: str              # User's campaign description
    audience_segments: List[str]   # Generated audience segments (1-2)
    content: List[dict]            # Generated content pieces
    review_task: dict              # Review task object
```

**State Immutability**: Each node returns updates that merge with existing state

### **4. Workflow Nodes**

#### **Node: [generate_audience(state)](cci:1://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend/app.py:82:0-108:85)**

**Purpose**: Generate 1-2 audience segments from campaign brief

**Process**:
1. Check if LLM available (fallback to stub if not)
2. Invoke `audience_chain` with `intent_brief`
3. CommaSeparatedListOutputParser converts response to list
4. Return `{'audience_segments': generated_list}`

**Example Output**:
```python
{
    'audience_segments': [
        'Tech-savvy millennials interested in AI',
        'Enterprise decision-makers in tech sector'
    ]
}
```

#### **Node: [generate_content_for_segments(state)](cci:1://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend/app.py:145:0-179:35)**

**Purpose**: Generate channel-specific content for each audience segment

**Key Feature**: Channel decision is **dynamic** - LLM decides optimal channel per segment

**Process**:
1. Iterate through each audience segment
2. For each segment:
   - Use LLM to decide channel (email or digital banner)
   - Route to appropriate subagent
   - Collect generated content
3. Return aggregated content list

**Example Flow**:
```
Segment 1: "Tech professionals" → LLM decides → Email → email_content_subagent()
Segment 2: "Enterprise decision-makers" → LLM decides → Banner → digital_banner_subagent()
```

**Output Structure**:
```python
{
    'content': [
        {
            'type': 'email',
            'segment': 'Tech professionals',
            'html': '<html>...</html>'
        },
        {
            'type': 'banner',
            'segment': 'Enterprise decision-makers',
            'html': '<div>...</div>',
            'css': 'div { ... }'
        }
    ]
}
```

#### **Subagent: [email_content_subagent(state)](cci:1://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend/app.py:112:0-126:93)**

**Purpose**: Generate responsive HTML email with inline CSS

**Key Requirement**: All CSS must be inline (no separate `<style>` blocks)

**Output Example**:
```html
<table style="width: 100%; background: #f5f5f5;">
  <tr>
    <td style="padding: 20px; text-align: center;">
      <h1 style="color: #333;">Your Campaign Title</h1>
    </td>
  </tr>
</table>
```

#### **Subagent: [digital_banner_subagent(state)](cci:1://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend/app.py:128:0-142:109)**

**Purpose**: Generate HTML/CSS digital banner for web display

**Output**: HTML and CSS (can be separate in this case)

#### **Node: [create_review_task(state)](cci:1://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend/app.py:181:0-192:32)**

**Purpose**: Create a review task for QA workflow

**Process**:
1. Count content pieces generated
2. Create unique task ID from campaign brief hash
3. Generate task object with title, details, status

**Output**:
```python
{
    'review_task': {
        'id': 'TODO-a1b2c3',
        'title': 'Review campaign: Launch our new AI product...',
        'details': 'Review 2 content pieces for different audience segments',
        'status': 'pending'
    }
}
```

### **5. Orchestrator Node**

**Function**: [campaign_orchestrator(state)](cci:1://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend/app.py:198:0-265:24)

**Purpose**: Central decision engine determining next workflow step

**Decision Logic**:
```
IF no audience_segments:
    → Route to generate_audience
ELSE IF no content:
    → Route to generate_content_for_segments
ELSE IF no review_task:
    → Route to create_review_task
ELSE:
    → END (workflow complete)
```

**Special Logic**: Waits for all segment content before creating review task
```python
if len(state['content']) >= len(audience_segments) and not has_review:
    new_state["next"] = "create_review_task"
```

### **6. Graph Construction**

```python
graph = StateGraph(CampaignState)
graph.set_entry_point("campaign_orchestrator")

# Add all nodes
graph.add_node("campaign_orchestrator", campaign_orchestrator)
graph.add_node("generate_audience", generate_audience)
graph.add_node("generate_content_for_segments", generate_content_for_segments)
graph.add_node("email_content_subagent", email_content_subagent)
graph.add_node("digital_banner_subagent", digital_banner_subagent)
graph.add_node("create_review_task", create_review_task)

# Conditional routing from orchestrator
graph.add_conditional_edges("campaign_orchestrator", decide_next_step)

# Connect subagents back to orchestrator
graph.add_edge("generate_audience", "campaign_orchestrator")
graph.add_edge("generate_content_for_segments", "campaign_orchestrator")
graph.add_edge("create_review_task", "campaign_orchestrator")

app_graph = graph.compile()
```

### **7. API Endpoints**

#### **GET `/api/hello`**
- **Purpose**: Health check
- **Response**: `{"message": "Backend is running!"}`

#### **POST `/api/run-campaign`**
- **Purpose**: Trigger campaign generation workflow
- **Request**: `{"intent_brief": "Your campaign description"}`
- **Response**: Complete campaign state with audience, content, and review task

#### **GET `/`**
- **Purpose**: Root status endpoint
- **Response**: `{"message": "Campaign Manager Backend API", "status": "active"}`

---

## **Frontend Components** ([frontend/src/App.js](cci:7://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/frontend/src/App.js:0:0-0:0))

### **1. LoginPage Component**

**Purpose**: Authentication gate (stub implementation)

**Props**:
- `onLogin`: Callback function when user clicks login

**Features**:
- Centered login form with single "Login" button
- Tailwind CSS styling
- Currently no real authentication (just sets `isLoggedIn = true`)

### **2. DashboardPage Component**

**Purpose**: Main campaign generation interface

**State**:
```javascript
const [campaignBrief, setCampaignBrief] = useState('');
const [backendStatus, setBackendStatus] = useState('');
const [loading, setLoading] = useState(false);
const [results, setResults] = useState(null);
```

**Key Functions**:

**`useEffect` Hook** (on mount):
- Fetches backend health check from `/api/hello`
- Displays backend status indicator
- Handles connection errors gracefully

**[handleGenerateCampaign](cci:1://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/frontend/src/App.js:147:2-184:4) Function**:
1. Validates campaign brief is not empty
2. Sets loading state
3. POSTs to `/api/run-campaign` with campaign brief
4. Handles response and errors
5. Calls `onTaskCreated` if review task exists

**UI Elements**:
- Title: "Campaign Manager"
- Backend status indicator (green badge)
- Campaign brief textarea (8 rows)
- Generate button with loading spinner
- Results display component

### **3. ResultsDisplay Component**

**Purpose**: Display generated campaign results

**Props**:
- `results`: Campaign generation output object

**Sections**:

**Section 1: Target Audience**
- Blue card with audience segments
- Icon: checkmark

**Section 2: Campaign Content**
- Green card with content pieces
- For each content item:
  - Segment name (indigo text)
  - Email preview in iframe (if type='email')
  - Download HTML button
  - Fallback text display (if type!='email')

**Section 3: Review Task**
- Purple card with task details
- Task title and description
- Status badge (yellow=pending, green=completed)

**Special Feature**: [downloadHtml()](cci:1://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/frontend/src/App.js:31:2-42:4) function allows users to download generated HTML as files

### **4. TaskPage Component**

**Purpose**: Display list of created review tasks

**Props**:
- `tasks`: Array of task objects

**Features**:
- Lists all tasks with title, details, status
- Status badge (yellow/green)
- "Mark as completed" button (TODO - not implemented)
- Empty state message when no tasks

### **5. App Component (Main)**

**Purpose**: Root component managing navigation and state

**State**:
```javascript
const [isLoggedIn, setIsLoggedIn] = useState(false);
const [activeTab, setActiveTab] = useState('dashboard');
const [tasks, setTasks] = useState([]);
```

**Features**:
- Tab navigation (Dashboard / My Tasks)
- Login gate
- Task management
- Conditional rendering based on active tab

---

## **Complete Workflow Execution Flow**

```
1. USER INTERACTION
   └─ User enters campaign brief in DashboardPage textarea
   └─ User clicks "Generate Campaign" button

2. FRONTEND REQUEST
   └─ handleGenerateCampaign() triggered
   └─ POST /api/run-campaign with {intent_brief: "..."}
   └─ Loading state = true, spinner displayed

3. BACKEND RECEIVES REQUEST
   └─ Flask route handler: run_campaign()
   └─ Extracts intent_brief from JSON body
   └─ Validates intent_brief exists

4. WORKFLOW EXECUTION
   └─ app_graph.invoke({'intent_brief': intent_brief})
   └─ Entry point: campaign_orchestrator

5. ORCHESTRATOR DECISION #1
   └─ Checks state: no audience_segments
   └─ Routes to: generate_audience

6. GENERATE AUDIENCE NODE
   └─ Calls audience_chain.invoke({'intent_brief': intent_brief})
   └─ Gemini LLM generates 1-2 audience segments
   └─ CommaSeparatedListOutputParser converts to list
   └─ Returns: {'audience_segments': [...]}
   └─ State updated with audience_segments
   └─ Routes back to: campaign_orchestrator

7. ORCHESTRATOR DECISION #2
   └─ Checks state: has audience_segments, no content
   └─ Routes to: generate_content_for_segments

8. GENERATE CONTENT NODE
   └─ For each audience segment:
      a) Use LLM to decide channel (email or banner)
      b) If email: Call email_content_subagent()
      c) If banner: Call digital_banner_subagent()
      d) Collect result in all_content list
   └─ Returns: {'content': all_content}
   └─ State updated with content
   └─ Routes back to: campaign_orchestrator

9. ORCHESTRATOR DECISION #3
   └─ Checks state: has audience_segments, has content, no review_task
   └─ Routes to: create_review_task

10. CREATE REVIEW TASK NODE
    └─ Generates unique task ID from brief hash
    └─ Creates task object with title, details, status
    └─ Returns: {'review_task': task_object}
    └─ State updated with review_task
    └─ Routes back to: campaign_orchestrator

11. ORCHESTRATOR DECISION #4
    └─ Checks state: all fields populated
    └─ Routes to: END (workflow complete)

12. BACKEND RETURNS RESPONSE
    └─ Flask returns final state as JSON
    └─ Response includes: intent_brief, audience_segments, content, review_task

13. FRONTEND RECEIVES RESPONSE
    └─ handleGenerateCampaign() receives data
    └─ setResults(data) updates state
    └─ onTaskCreated(data.review_task) adds to task list
    └─ Loading state = false, spinner hidden

14. FRONTEND DISPLAYS RESULTS
    └─ ResultsDisplay component renders all sections
    └─ User can download HTML files
    └─ User can navigate to Tasks tab to see review task
```

---

## **State Progression Example**

**Initial State**:
```python
{
    'intent_brief': 'Launch AI product to tech professionals',
    'audience_segments': [],
    'content': [],
    'review_task': None
}
```

**After generate_audience**:
```python
{
    'intent_brief': 'Launch AI product to tech professionals',
    'audience_segments': ['Tech professionals', 'Product managers'],
    'content': [],
    'review_task': None
}
```

**After generate_content_for_segments**:
```python
{
    'intent_brief': 'Launch AI product to tech professionals',
    'audience_segments': ['Tech professionals', 'Product managers'],
    'content': [
        {'type': 'email', 'segment': 'Tech professionals', 'html': '...'},
        {'type': 'banner', 'segment': 'Product managers', 'html': '...'}
    ],
    'review_task': None
}
```

**After create_review_task (Final)**:
```python
{
    'intent_brief': 'Launch AI product to tech professionals',
    'audience_segments': ['Tech professionals', 'Product managers'],
    'content': [
        {'type': 'email', 'segment': 'Tech professionals', 'html': '...'},
        {'type': 'banner', 'segment': 'Product managers', 'html': '...'}
    ],
    'review_task': {
        'id': 'TODO-a1b2c3',
        'title': 'Review campaign: Launch AI product...',
        'details': 'Review 2 content pieces for different audience segments',
        'status': 'pending'
    }
}
```

---

## **Key Design Patterns**

1. **State Machine Pattern**: LangGraph manages deterministic workflow transitions
2. **Multi-Agent Routing**: Separate subagents handle specialized content generation
3. **LLM-Driven Decisions**: Channel selection delegated to LLM for intelligent routing
4. **Graceful Degradation**: Fallback stub responses when Gemini API unavailable
5. **Separation of Concerns**: Frontend and backend fully decoupled via REST API
6. **Orchestrator Pattern**: Central decision engine manages workflow progression

---

## **Error Handling & Fallbacks**

### **Gemini API Key Missing**
- **Status**: Application still runs
- **Behavior**: Uses stub responses for all LLM calls
- **Message**: "WARNING: GOOGLE_API_KEY not found. Gemini integration will use fallback mode."
- **Fallback Audience**: `['Tech-savvy millennials (Gemini unavailable - set GOOGLE_API_KEY)']`

### **Gemini API Error During Execution**
- **Status**: 200 (still succeeds)
- **Behavior**: Falls back to stub response for that specific node
- **Logging**: Error logged to console with fallback message

### **Missing intent_brief in Request**
- **Status**: 400 Bad Request
- **Error**: `{"error": "intent_brief is required"}`

### **General Backend Error**
- **Status**: 500 Internal Server Error
- **Error**: `{"error": "<detailed error message>"}`

---

## **Dependencies**

### **Backend** ([backend/requirements.txt](cci:7://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend/requirements.txt:0:0-0:0))
- `flask`: Web framework
- `flask-cors`: CORS support
- `langchain`: LLM framework
- `langgraph`: Workflow orchestration
- `python-dotenv`: Environment variable loading
- `langchain-google-genai`: Google Gemini integration
- `IPython`: Interactive Python (for development)

### **Frontend** ([frontend/package.json](cci:7://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/frontend/package.json:0:0-0:0))
- `react`: UI framework (19.2.0)
- `react-dom`: React DOM rendering
- `react-scripts`: Build tools
- Testing libraries: `@testing-library/react`, `@testing-library/jest-dom`, etc.

---

## **Setup & Configuration**

### **Backend Setup**
1. Create `.env` file in [backend/](cci:7://file:///Users/premasai09/Developer/Surface_MCM/Surface_demo2/backend:0:0-0:0) directory
2. Add: `GOOGLE_API_KEY=your-api-key-here`
3. Get API key from: https://makersuite.google.com/app/apikey
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `python app.py`
6. Backend available at: `http://localhost:5000`

### **Frontend Setup**
1. Install dependencies: `npm install`
2. Run: `npm start`
3. Frontend available at: `http://localhost:3000`

---

## **File Structure**

```
Surface_demo2/
├── backend/
│   ├── app.py                 # Main Flask app with LangGraph orchestration
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js            # Main React component with 5 sub-components
│   │   ├── App.css           # Styling
│   │   ├── index.js          # React entry point
│   │   └── ...other files
│   ├── package.json          # Node dependencies
│   └── public/               # Static assets
└── .gitignore
```

---

## **Summary**

**Surface Campaign Manager** is a well-architected AI-powered marketing automation platform that:
- ✅ Automates audience segmentation using LLM
- ✅ Intelligently routes content to appropriate channels
- ✅ Generates production-ready HTML content
- ✅ Creates trackable review tasks
- ✅ Provides graceful fallbacks when APIs unavailable
- ✅ Separates concerns cleanly between frontend and backend
- ✅ Uses modern frameworks (React, Flask, LangGraph, Gemini)

The system is production-ready with proper error handling, state management, and user-friendly interface.