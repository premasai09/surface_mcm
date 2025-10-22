import pyodbc
from db_config import MSSQL_CONNECTION_STRING

# Helper to fetch table schema
def get_table_schema(cursor, table_name):
    print(f'📋 [DEBUG] Fetching schema for table: {table_name}')
    try:
        cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", (table_name,))
        schema = [(row[0], row[1]) for row in cursor.fetchall()]
        print(f'📋 [DEBUG] Schema for {table_name}: {len(schema)} columns found')
        for col_name, col_type in schema:
            print(f'📋 [DEBUG] - {col_name}: {col_type}')
        return schema
    except Exception as e:
        print(f'❌ [DEBUG] Error fetching schema for {table_name}: {e}')
        return []

# Helper to fetch all values from a single-column lookup table
def get_lookup_values(cursor, table_name, column_name):
    print(f'🔍 [DEBUG] Fetching lookup values from {table_name}.{column_name}')
    try:
        cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name}")
        values = [row[0] for row in cursor.fetchall()]
        print(f'🔍 [DEBUG] Found {len(values)} distinct values in {table_name}.{column_name}')
        for i, value in enumerate(values[:5], 1):  # Show first 5 values
            print(f'🔍 [DEBUG] - {i}. {value}')
        if len(values) > 5:
            print(f'🔍 [DEBUG] - ... and {len(values) - 5} more values')
        return values
    except Exception as e:
        print(f'❌ [DEBUG] Error fetching lookup values from {table_name}.{column_name}: {e}')
        return []

# Helper to fetch distinct product names, handling comma-separated values
def get_distinct_products(cursor, table_name, column_name):
    """
    Fetch distinct product names from the database, splitting comma-separated values
    and returning only unique individual products (not combinations).
    """
    print(f'🛍️ [DEBUG] Fetching distinct products from {table_name}.{column_name}')
    try:
        cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name}")
        raw_products = [row[0] for row in cursor.fetchall()]
        print(f'🛍️ [DEBUG] Found {len(raw_products)} raw product entries')
        
        # Log raw products
        for i, product in enumerate(raw_products[:3], 1):
            print(f'🛍️ [DEBUG] Raw product {i}: {product}')
        if len(raw_products) > 3:
            print(f'🛍️ [DEBUG] ... and {len(raw_products) - 3} more raw products')
        
        # Split comma-separated values and collect all individual products
        all_products = []
        for product_string in raw_products:
            if product_string:  # Check if not None or empty
                # Split by comma and strip whitespace
                individual_products = [p.strip() for p in product_string.split(',')]
                all_products.extend(individual_products)
                print(f'🛍️ [DEBUG] Split "{product_string}" into: {individual_products}')
        
        # Return only distinct individual products
        distinct_products = list(set(all_products))
        print(f'🛍️ [DEBUG] Processing complete:')
        print(f'🛍️ [DEBUG] - Raw entries: {len(raw_products)}')
        print(f'🛍️ [DEBUG] - Individual products: {len(all_products)}')
        print(f'🛍️ [DEBUG] - Distinct products: {len(distinct_products)}')
        print(f'🛍️ [DEBUG] - Final distinct products: {distinct_products}')
        
        return distinct_products
        
    except Exception as e:
        print(f'❌ [DEBUG] Error fetching distinct products from {table_name}.{column_name}: {e}')
        return []
from flask import Flask, jsonify, request
from flask_cors import CORS
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# Create Flask app
app = Flask(__name__)

# Configure CORS to allow requests from React frontend
CORS(app, origins=['http://localhost:3000'])

# Initialize Gemini LLM with explicit API key
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if API key is available
google_api_key = os.getenv('GOOGLE_API_KEY')
if not google_api_key:
    print("WARNING: GOOGLE_API_KEY not found. Gemini integration will use fallback mode.")
    print("   To enable Gemini: $env:GOOGLE_API_KEY='your-api-key-here'")
    llm = None
else:
    print("SUCCESS: GOOGLE_API_KEY found. Gemini integration enabled.")
    llm = ChatGoogleGenerativeAI(
        model='gemini-2.5-flash',
        google_api_key=google_api_key
    )

# Create audience prompt template
audience_prompt = ChatPromptTemplate.from_template(
    """You are an expert marketing strategist with access to customer data. Your task is to analyze the campaign brief and available customer data to generate precise audience segments that maximize marketing reach and effectiveness.

CAMPAIGN BRIEF: {intent_brief}

AVAILABLE CUSTOMER DATA:
{database_context}

MARKETING REACH OPTIMIZATION STRATEGY:
To improve marketing reach, consider these proven segmentation approaches:

1. BEHAVIORAL SEGMENTATION:
   - Target customers based on their actual behaviors from the database
   - Look for high-value behaviors like "Frequent online shopping", "Price comparison research"
   - Consider engagement patterns like "Email newsletter subscription", "Social media engagement"
   - Segment by purchase intent behaviors

2. GEOGRAPHIC SEGMENTATION:
   - Use actual locations from the database for targeted campaigns
   - Consider market density and economic factors of each location
   - Target high-potential geographic areas for maximum reach
   - Create location-specific messaging opportunities

3. PRODUCT-BASED SEGMENTATION:
   - Leverage actual products from the database for precise targeting
   - Group customers by product interests and purchase patterns
   - Consider complementary products for cross-selling opportunities
   - Target customers with specific product affinities

4. DEMOGRAPHIC SEGMENTATION:
   - Use age, location, and behavioral data to create demographic profiles
   - Consider life stage and purchasing power
   - Target segments with highest conversion potential

5. PSYCHOGRAPHIC SEGMENTATION:
   - Combine behavioral patterns with product interests
   - Create lifestyle-based segments
   - Target based on values, interests, and attitudes

SEGMENT GENERATION GUIDELINES:
- Create segments that are MUTUALLY EXCLUSIVE but collectively EXHAUSTIVE
- Ensure each segment is LARGE ENOUGH to be profitable
- Make segments MEASURABLE with clear criteria
- Ensure segments are ACCESSIBLE through available channels
- Create segments that are ACTIONABLE for marketing campaigns

REACH OPTIMIZATION TACTICS:
- Target segments with HIGHEST PURCHASE INTENT based on behaviors
- Focus on segments with STRONG PRODUCT AFFINITY from database
- Consider segments with GEOGRAPHIC ADVANTAGE for local campaigns
- Leverage segments with PROVEN ENGAGEMENT PATTERNS
- Target segments with CROSS-SELLING POTENTIAL

SEGMENT NAMING CONVENTION:
Use descriptive names that include:
- Key demographic indicator (age, location, behavior)
- Primary product interest or need
- Behavioral characteristic
- Geographic relevance

EXAMPLES OF HIGH-REACH SEGMENTS:
- "Tech-savvy professionals in major cities interested in productivity tools"
- "Price-conscious shoppers in suburban areas with frequent online shopping behavior"
- "Young professionals in tech hubs with mobile-first purchasing patterns"
- "Small business owners in metropolitan areas needing office equipment"

INSTRUCTIONS:
1. Analyze the campaign brief to understand goals and target market
2. Review available customer data to identify high-potential segments
3. Apply reach optimization strategies to maximize marketing effectiveness
4. Create 2 distinct, high-reach audience segments
5. Ensure segments are based on actual database information
6. Make segments specific enough for targeted marketing campaigns

IMPORTANT: Return your answer as a single, comma-separated list of exactly 2 segments. Do not use newlines or bullet points."""
)

# Create content prompt template
content_prompt = ChatPromptTemplate.from_template(
    "You are a creative copywriter. Based on the campaign brief and the *specific* target audience, write compelling ad copy.\n"
    "BRIEF: {intent_brief}\n\n"
    "TARGET AUDIENCE: {audience_segment}"
)

# Create orchestrator prompt template
orchestrator_prompt = ChatPromptTemplate.from_template(
    "You are a campaign orchestration agent. Analyze the campaign brief and determine next steps.\n"
    "Current Campaign State:\n"
    "- Brief: {intent_brief}\n"
    "- Audience Segments: {audience_segments}\n"
    "- Content Generated: {has_content}\n"
    "- Review Task: {has_review}\n\n"
    "Determine the next step needed:\n"
    "- If no audience segments exist, return 'generate_audience'\n"
    "- If segments exist but no content, return 'generate_content'\n"
    "- If content exists but no review, return 'create_review'\n"
    "- If all steps are complete, return 'complete'\n\n"
    "Return ONLY ONE of these exact words."
)

# Create chains (only if LLM is available)
if llm:
    audience_chain = audience_prompt | llm | CommaSeparatedListOutputParser()
    content_chain = content_prompt | llm | StrOutputParser()
    orchestrator_chain = orchestrator_prompt | llm | StrOutputParser()
else:
    audience_chain = None
    content_chain = None
    orchestrator_chain = None

# Define the graph's state
class CampaignState(TypedDict):
    intent_brief: str
    audience_segments: List[str]
    content: List[dict]  # Will store {'segment': '...', 'copy': '...'}
    review_task: str

# Define the workflow nodes (stub functions)
def generate_audience(state: CampaignState):
    """Generate audience segments based on intent brief using Gemini LLM"""
    print('🎯 [DEBUG] Starting audience generation...')
    print(f'🎯 [DEBUG] Campaign brief: {state.get("intent_brief", "No brief provided")}')
    
    # Connect to MSSQL and fetch schemas and lookup values
    print('🔌 [DEBUG] Attempting database connection...')
    print(f'🔌 [DEBUG] Connection string: {MSSQL_CONNECTION_STRING[:50]}...')
    
    try:
        print('🔌 [DEBUG] Connecting to database...')
        conn = pyodbc.connect(MSSQL_CONNECTION_STRING)
        cursor = conn.cursor()
        print('✅ [DEBUG] Database connection successful!')
        
        # Test basic connection
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f'📊 [DEBUG] SQL Server version: {version[:50]}...')
        
        # Fetch schemas with detailed logging
        print('📋 [DEBUG] Fetching table schemas...')
        
        print('📋 [DEBUG] Getting Customers schema...')
        customers_schema = get_table_schema(cursor, 'Customers')
        print(f'📋 [DEBUG] Customers schema: {customers_schema}')
        
        print('📋 [DEBUG] Getting Behaviors schema...')
        behaviors_schema = get_table_schema(cursor, 'Behaviors')
        print(f'📋 [DEBUG] Behaviors schema: {behaviors_schema}')
        
        print('📋 [DEBUG] Getting Compliance schema...')
        compliance_schema = get_table_schema(cursor, 'Compliance')
        print(f'📋 [DEBUG] Compliance schema: {compliance_schema}')
        
        # Fetch lookup values with detailed logging
        print('🔍 [DEBUG] Fetching lookup values...')
        
        print('🔍 [DEBUG] Getting distinct products...')
        distinct_products = get_distinct_products(cursor, 'Distinct_Products', 'product_name')
        print(f'🔍 [DEBUG] Found {len(distinct_products)} distinct products: {distinct_products}')
        
        print('🔍 [DEBUG] Getting distinct locations...')
        distinct_locations = get_lookup_values(cursor, 'Distinct_Locations', 'location_name')
        print(f'🔍 [DEBUG] Found {len(distinct_locations)} distinct locations: {distinct_locations}')
        
        print('🔍 [DEBUG] Getting distinct behaviors...')
        distinct_behaviors = get_lookup_values(cursor, 'Distinct_Behaviors', 'behaviour_description')
        print(f'🔍 [DEBUG] Found {len(distinct_behaviors)} distinct behaviors: {distinct_behaviors}')
        
        # Test data quality
        print('🧪 [DEBUG] Testing data quality...')
        print(f'🧪 [DEBUG] Products data type: {type(distinct_products)}, Length: {len(distinct_products) if distinct_products else 0}')
        print(f'🧪 [DEBUG] Locations data type: {type(distinct_locations)}, Length: {len(distinct_locations) if distinct_locations else 0}')
        print(f'🧪 [DEBUG] Behaviors data type: {type(distinct_behaviors)}, Length: {len(distinct_behaviors) if distinct_behaviors else 0}')
        
        # Check for empty data
        if not distinct_products:
            print('⚠️ [DEBUG] WARNING: No products found in database!')
        if not distinct_locations:
            print('⚠️ [DEBUG] WARNING: No locations found in database!')
        if not distinct_behaviors:
            print('⚠️ [DEBUG] WARNING: No behaviors found in database!')
        
        conn.close()
        print('✅ [DEBUG] Database connection closed successfully')
        
    except Exception as db_err:
        print(f'❌ [DEBUG] Database connection failed!')
        print(f'❌ [DEBUG] Error type: {type(db_err).__name__}')
        print(f'❌ [DEBUG] Error message: {str(db_err)}')
        print(f'❌ [DEBUG] Connection string used: {MSSQL_CONNECTION_STRING}')
        return {'audience_segments': ['Error: Could not connect to MSSQL or fetch schema/lookup values.']}

    # Prepare comprehensive database context for LLM
    print('📝 [DEBUG] Preparing database context for LLM...')
    
    # Log data before processing
    print(f'📝 [DEBUG] Raw products count: {len(distinct_products)}')
    print(f'📝 [DEBUG] Raw locations count: {len(distinct_locations)}')
    print(f'📝 [DEBUG] Raw behaviors count: {len(distinct_behaviors)}')
    
    # Create database context with error handling
    try:
        products_str = ', '.join(distinct_products) if distinct_products else 'No products available'
        locations_str = ', '.join(distinct_locations) if distinct_locations else 'No locations available'
        behaviors_str = ', '.join(distinct_behaviors) if distinct_behaviors else 'No behaviors available'
        
        database_context = f"""
CUSTOMER DATA SCHEMA:
- Customers: {customers_schema}
- Behaviors: {behaviors_schema}  
- Compliance: {compliance_schema}

AVAILABLE PRODUCTS: {products_str}

AVAILABLE LOCATIONS: {locations_str}

AVAILABLE BEHAVIORS: {behaviors_str}

DATA INSIGHTS:
- Total Products Available: {len(distinct_products)} distinct products
- Geographic Coverage: {len(distinct_locations)} locations
- Behavioral Patterns: {len(distinct_behaviors)} behavior types
- Customer Demographics: Age, location, and behavior tracking available
"""
        
        print(f'📝 [DEBUG] Database context prepared successfully')
        print(f'📝 [DEBUG] Context length: {len(database_context)} characters')
        print(f'📝 [DEBUG] Products string: {products_str[:100]}...')
        print(f'📝 [DEBUG] Locations string: {locations_str[:100]}...')
        print(f'📝 [DEBUG] Behaviors string: {behaviors_str[:100]}...')
        
    except Exception as context_err:
        print(f'❌ [DEBUG] Error preparing database context: {context_err}')
        database_context = "Database context preparation failed"

    # Check if Gemini is available
    if not audience_chain:
        print('Gemini not available, using strategic data-driven fallback response')
        # Create fallback segments optimized for marketing reach
        fallback_segments = []
        
        # Strategic segment 1: High-value product enthusiasts
        if distinct_products:
            high_value_products = [p for p in distinct_products if any(keyword in p.lower() for keyword in ['laptop', 'desktop', 'monitor', 'tablet'])]
            if high_value_products:
                product_segment = f"Tech professionals in major cities interested in {', '.join(high_value_products[:2])}"
            else:
                product_segment = f"Tech enthusiasts interested in {', '.join(distinct_products[:3])}"
            fallback_segments.append(product_segment)
        
        # Strategic segment 2: Geographic + behavioral targeting
        if distinct_locations and distinct_behaviors:
            major_cities = [loc for loc in distinct_locations if any(city in loc.lower() for city in ['new york', 'los angeles', 'chicago', 'houston', 'phoenix'])]
            high_intent_behaviors = [b for b in distinct_behaviors if any(keyword in b.lower() for keyword in ['frequent', 'shopping', 'research', 'engagement'])]
            
            if major_cities and high_intent_behaviors:
                location_segment = f"Active shoppers in {', '.join(major_cities[:2])} with {high_intent_behaviors[0].lower()}"
            else:
                location_segment = f"Customers in {', '.join(distinct_locations[:2])} markets"
            fallback_segments.append(location_segment)
        
        # Fallback to generic high-reach segments if no data
        if not fallback_segments:
            fallback_segments = [
                'Tech-savvy professionals in metropolitan areas',
                'Price-conscious consumers with frequent online shopping behavior'
            ]
        
        return {'audience_segments': fallback_segments}

    try:
        # Get the intent brief from the state
        intent_brief = state['intent_brief']
        print(f'🤖 [DEBUG] Starting LLM processing...')
        print(f'🤖 [DEBUG] Intent brief: {intent_brief}')
        
        # Pass campaign brief and database context to LLM
        prompt_input = {
            'intent_brief': intent_brief,
            'database_context': database_context
        }
        
        print(f'🤖 [DEBUG] Prompt input prepared:')
        print(f'🤖 [DEBUG] - Intent brief length: {len(intent_brief)} characters')
        print(f'🤖 [DEBUG] - Database context length: {len(database_context)} characters')
        print(f'🤖 [DEBUG] - Intent brief preview: {intent_brief[:100]}...')
        print(f'🤖 [DEBUG] - Database context preview: {database_context[:200]}...')
        
        print(f'🤖 [DEBUG] Invoking LLM with audience chain...')
        print(f'🤖 [DEBUG] Audience chain available: {audience_chain is not None}')
        
        generated_audience = audience_chain.invoke(prompt_input)
        
        print(f'✅ [DEBUG] LLM processing completed successfully!')
        print(f'✅ [DEBUG] Generated audience type: {type(generated_audience)}')
        print(f'✅ [DEBUG] Generated audience content: {generated_audience}')
        print(f'✅ [DEBUG] Generated audience length: {len(generated_audience) if generated_audience else 0}')
        
        # Validate the response
        if isinstance(generated_audience, list) and len(generated_audience) > 0:
            print(f'✅ [DEBUG] Audience segments are valid list with {len(generated_audience)} items')
            for i, segment in enumerate(generated_audience, 1):
                print(f'✅ [DEBUG] Segment {i}: {segment}')
        else:
            print(f'⚠️ [DEBUG] WARNING: Generated audience is not a valid list: {generated_audience}')
        
        return {'audience_segments': generated_audience}
        
    except Exception as e:
        print(f'❌ [DEBUG] LLM processing failed!')
        print(f'❌ [DEBUG] Error type: {type(e).__name__}')
        print(f'❌ [DEBUG] Error message: {str(e)}')
        print(f'❌ [DEBUG] Intent brief was: {intent_brief}')
        print(f'❌ [DEBUG] Database context length: {len(database_context) if database_context else 0}')
        print('🔄 [DEBUG] Falling back to stub response')
        return {'audience_segments': ['Tech-savvy professionals (LLM processing failed)', 'Price-conscious consumers (LLM processing failed)']}


# --- New Subagents for Channel-Specific Content ---
def email_content_subagent(state: CampaignState):
    """Generate email channel content (HTML/CSS) for a segment using LLM"""
    print(f"[EmailContentSubAgent] Generating email content for: {state.get('audience_segment')}")
    if not llm:
        return {'content': {'type': 'email', 'segment': state.get('audience_segment'), 'html': '<p style="color: blue;">Stub email content</p>'}}
    prompt = ChatPromptTemplate.from_template(
        "You are an expert email marketer. Write a responsive HTML email for the following campaign brief and audience segment. All CSS must be inline, not in a separate <style> block or file. Do not return any CSS separately.\n"
        "BRIEF: {intent_brief}\nAUDIENCE SEGMENT: {audience_segment}\n"
        "Return only the HTML with inline CSS, no explanations."
    )
    html = (prompt | llm | StrOutputParser()).invoke({
        'intent_brief': state['intent_brief'],
        'audience_segment': state['audience_segment']
    })
    return {'content': {'type': 'email', 'segment': state['audience_segment'], 'html': html}}

def digital_banner_subagent(state: CampaignState):
    """Generate digital banner content (HTML/CSS) for a segment using LLM"""
    print(f"[DigitalBannerSubAgent] Generating banner content for: {state.get('audience_segment')}")
    if not llm:
        return {'content': {'type': 'banner', 'segment': state.get('audience_segment'), 'html': '<div>Stub banner</div>', 'css': 'div { background: yellow; }'}}
    prompt = ChatPromptTemplate.from_template(
        "You are a digital designer. Create a simple, visually appealing HTML/CSS digital banner for the following campaign brief and audience segment.\n"
        "BRIEF: {intent_brief}\nAUDIENCE SEGMENT: {audience_segment}\n"
        "Return only the HTML and CSS, no explanations."
    )
    html_css = (prompt | llm | StrOutputParser()).invoke({
        'intent_brief': state['intent_brief'],
        'audience_segment': state['audience_segment']
    })
    return {'content': {'type': 'banner', 'segment': state['audience_segment'], 'html': html_css, 'css': ''}}

# --- Channel Decision and Routing ---
def generate_content_for_segments(state: CampaignState):
    """Route to channel-specific subagents for each segment, aggregate results, and return to orchestrator."""
    print('---GENERATING CONTENT FOR EACH SEGMENT (ROUTED)---')
    if not llm:
        print('LLM not available, using fallback response')
        stub_content = [{'segment': 'Tech-savvy millennials', 'type': 'email', 'html': '<p>Stub email</p>', 'css': ''}]
        return {'content': stub_content}
    intent_brief = state['intent_brief']
    audience_segments = state.get('audience_segments', [])
    print(f"[DEBUG] Input audience_segments: {audience_segments}")
    if isinstance(audience_segments, str):
        audience_segments = [s.strip() for s in audience_segments.split(',')]
    all_content = []
    for segment in audience_segments:
        print(f"[DEBUG] Processing segment: {segment}")
        # Use LLM to decide channel
        channel_decision_prompt = ChatPromptTemplate.from_template(
            "Given the campaign brief and audience segment, should the content be delivered as an 'email' or 'digital banner'?\n"
            "BRIEF: {intent_brief}\nSEGMENT: {audience_segment}\n"
            "Return only 'email' or 'digital banner'."
        )
        channel = (channel_decision_prompt | llm | StrOutputParser()).invoke({
            'intent_brief': intent_brief,
            'audience_segment': segment
        }).strip().lower()
        print(f"Routing segment '{segment}' to channel: {channel}")
        subagent_state = {'intent_brief': intent_brief, 'audience_segment': segment}
        if 'email' in channel:
            result = email_content_subagent(subagent_state)
        else:
            result = digital_banner_subagent(subagent_state)
        all_content.append(result['content'])
    print(f'[DEBUG] All generated content: {all_content}')
    print(f'Generated content for {len(all_content)} segments')
    return {'content': all_content}

def create_review_task(state: CampaignState):
    """Create review task for the generated campaign"""
    print('---CREATING REVIEW TASK---')
    num_pieces = len(state['content'])
    timestamp = "TODO-" + str(hash(state['intent_brief']))[:6]  # Create a unique ID
    task = {
        'id': timestamp,
        'title': f"Review campaign: {state['intent_brief'][:50]}...",
        'details': f"Review {num_pieces} content pieces for different audience segments",
        'status': 'pending'
    }
    return {'review_task': task}

# Initialize the StateGraph
graph = StateGraph(CampaignState)

# Define orchestrator function
def campaign_orchestrator(state: CampaignState):
    """Orchestrates the campaign workflow by determining next steps"""
    print('---CAMPAIGN ORCHESTRATOR---')
    
    # Create new state dict to avoid modifying the input
    new_state = state.copy()
    
    # Check if Gemini is available
    if not orchestrator_chain:
        print('Gemini not available for orchestration, using simple logic')
        if 'audience_segments' not in state or not state['audience_segments']:
            new_state["next"] = "generate_audience"
        elif 'content' not in state or not state['content']:
            new_state["next"] = "generate_content_for_segments"
        elif 'review_task' not in state or not state['review_task']:
            new_state["next"] = "create_review_task"
        else:
            new_state["next"] = END
        return new_state
    
    try:
        # Prepare state info for orchestrator
        has_content = 'content' in state and bool(state['content'])
        has_review = 'review_task' in state and bool(state['review_task'])
        audience_segments = state.get('audience_segments', [])

        # Wait for all segment content before review
        if has_content and audience_segments:
            # If content exists for all segments, proceed to review
            if len(state['content']) >= len(audience_segments) and not has_review:
                print('All segment content received, proceeding to review task')
                new_state["next"] = "create_review_task"
                return new_state

        # Get orchestrator decision
        next_step = orchestrator_chain.invoke({
            'intent_brief': state['intent_brief'],
            'audience_segments': audience_segments,
            'has_content': has_content,
            'has_review': has_review
        }).strip().lower()

        print(f'Orchestrator decided next step: {next_step}')

        # Map the orchestrator's decision to the appropriate next step
        if next_step == 'generate_audience':
            new_state["next"] = "generate_audience"
        elif next_step == 'generate_content':
            new_state["next"] = "generate_content_for_segments"
        elif next_step == 'create_review':
            new_state["next"] = "create_review_task"
        else:  # 'complete' or any other response
            new_state["next"] = END

        return new_state

    except Exception as e:
        print(f'Error in orchestrator: {e}')
        print('Using fallback logic')
        if 'audience_segments' not in state or not state['audience_segments']:
            new_state["next"] = "generate_audience"
        elif 'content' not in state or not state['content']:
            new_state["next"] = "generate_content_for_segments"
        elif 'review_task' not in state or not state['review_task']:
            new_state["next"] = "create_review_task"
        else:
            new_state["next"] = END
        return new_state

# Define conditional edge function
def decide_next_step(state):
    """Determines the next step based on current state"""
    next_step = state.get("next", "")
    if next_step == "generate_audience":
        return "generate_audience"
    elif next_step == "generate_content_for_segments":
        return "generate_content_for_segments"
    elif next_step == "create_review_task":
        return "create_review_task"
    else:
        return END

# Define the workflow with orchestrator
graph.set_entry_point("campaign_orchestrator")


# Add nodes
graph.add_node("campaign_orchestrator", campaign_orchestrator)
graph.add_node("generate_audience", generate_audience)
graph.add_node("generate_content_for_segments", generate_content_for_segments)
graph.add_node("email_content_subagent", email_content_subagent)
graph.add_node("digital_banner_subagent", digital_banner_subagent)
graph.add_node("create_review_task", create_review_task)

# Connect orchestrator to next steps using conditional edges
graph.add_conditional_edges(
    "campaign_orchestrator",
    decide_next_step
)


# Add conditional edges for channel-specific subagents under generate_content_for_segments
# def decide_channel(state: CampaignState):
#     # This function is not used for routing in this implementation, but placeholder for graph conditional edge
#     return "email_content_subagent" if state.get('channel') == 'email' else "digital_banner_subagent"

graph.add_conditional_edges(
    "generate_content_for_segments",
    lambda state: []  # Prevents redundant subagent calls; all routing is handled inside the agent
)

# Connect subagents back to orchestrator
graph.add_edge("email_content_subagent", "campaign_orchestrator")
graph.add_edge("digital_banner_subagent", "campaign_orchestrator")
graph.add_edge("generate_audience", "campaign_orchestrator")
graph.add_edge("create_review_task", "campaign_orchestrator")

# Compile the graph
app_graph = graph.compile()

@app.route('/api/hello', methods=['GET'])
def hello():
    """Test endpoint to verify backend is running"""
    return jsonify({'message': 'Backend is running!'})

@app.route('/api/run-campaign', methods=['POST'])
def run_campaign():
    """Run the campaign generation workflow"""
    try:
        # Get the intent brief from the request
        data = request.get_json()
        if not data or 'intent_brief' not in data:
            return jsonify({'error': 'intent_brief is required'}), 400
        
        intent_brief = data['intent_brief']
        
        # Run the compiled graph with the intent brief
        result = app_graph.invoke({'intent_brief': intent_brief})
        
        # Return the final state as JSON
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({'message': 'Campaign Manager Backend API', 'status': 'active'})

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Backend will be available at: http://localhost:5000")
    print("Test endpoint: http://localhost:5000/api/hello")
    print("Campaign endpoint: http://localhost:5000/api/run-campaign")
    
    if not google_api_key:
        print("\nGEMINI INTEGRATION DISABLED")
        print("   To enable real AI: Set GOOGLE_API_KEY environment variable")
        print("   Get API key: https://makersuite.google.com/app/apikey")
        print("   Set it: $env:GOOGLE_API_KEY='your-api-key-here'")
    else:
        print("\nGEMINI INTEGRATION ENABLED")
        print("   Real AI audience generation is active!")
    
    app.run(debug=True, host='0.0.0.0', port=9000)
