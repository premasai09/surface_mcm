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
    "You are an expert marketer. Given this campaign brief, generate 3-5 distinct audience segments. "
    "BRIEF: {intent_brief}\n\n"
    "IMPORTANT: Return your answer as a single, comma-separated list. Do not use newlines or bullet points."
    "\nEXAMPLE: Tech-savvy millennials, Small business owners, Remote workers, Fitness enthusiasts"
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
    print('Generating audience...')
    
    # Check if Gemini is available
    if not audience_chain:
        print('Gemini not available, using fallback response')
        return {'audience_segments': ['Tech-savvy millennials (Gemini unavailable - set GOOGLE_API_KEY)']}
    
    try:
        # Get the intent brief from the state
        intent_brief = state['intent_brief']
        
        # Invoke the audience chain with the brief
        # CommaSeparatedListOutputParser already returns a list
        generated_audience = audience_chain.invoke({'intent_brief': intent_brief})
        
        # Print the generated audience
        print(f'Generated audience: {generated_audience}')
        
        # Return the generated audience as a list
        return {'audience_segments': generated_audience}
        
    except Exception as e:
        print(f'Error generating audience with Gemini: {e}')
        print('Falling back to stub response')
        return {'audience_segments': ['Tech-savvy millennials (Gemini unavailable)']}

def generate_content_for_segments(state: CampaignState):
    """Generate campaign content for each audience segment using Gemini LLM"""
    print('---GENERATING CONTENT FOR EACH SEGMENT---')
    
    # Check if Gemini is available
    if not content_chain:
        print('Gemini not available, using fallback response')
        stub_content = [{'segment': 'Tech-savvy millennials', 'copy': 'STUBBED_CONTENT: Check out our new gadget! (Gemini unavailable - set GOOGLE_API_KEY)'}]
        return {'content': stub_content}
    
    try:
        # Get intent_brief and audience_segments from the state
        intent_brief = state['intent_brief']
        audience_segments = state.get('audience_segments', [])
        all_content = []
        
        # Ensure audience_segments is a list
        if isinstance(audience_segments, str):
            # If it's a string, split it into a list
            audience_segments = [s.strip() for s in audience_segments.split(',')]
        
        print(f"Processing {len(audience_segments)} audience segments")
        
        # Generate content for each segment
        for segment in audience_segments:
            print(f'Generating content for: {segment}')
            try:
                # Call the content_chain for each segment
                generated_copy = content_chain.invoke({
                    'intent_brief': intent_brief,
                    'audience_segment': segment
                })
                all_content.append({'segment': segment, 'copy': generated_copy})
            except Exception as segment_error:
                print(f'Error generating content for segment {segment}: {segment_error}')
                all_content.append({
                    'segment': segment, 
                    'copy': f'Error generating content for this segment: {str(segment_error)}'
                })
            
        print(f'Generated content for {len(all_content)} segments')
        return {'content': all_content}
        
    except Exception as e:
        print(f'Error generating content with Gemini: {e}')
        print('Falling back to stub response')
        stub_content = [{'segment': 'Tech-savvy millennials', 'copy': 'STUBBED_CONTENT: Check out our new gadget! (Gemini error - check API key)'}]
        return {'content': stub_content}

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
graph.add_node("create_review_task", create_review_task)

# Connect orchestrator to next steps using conditional edges
graph.add_conditional_edges(
    "campaign_orchestrator",
    decide_next_step
)

# Connect other nodes back to orchestrator
graph.add_edge("generate_audience", "campaign_orchestrator")
graph.add_edge("generate_content_for_segments", "campaign_orchestrator")
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
