import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Inches, Pt
import json
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="DepEd AI Lesson Planner", layout="wide")

st.title("📚 AI Weekly Lesson Plan Generator (DLL)")
st.markdown("Generates a formatted Word file based on your inputs and module.")

# --- 2. SIDEBAR INPUTS ---
with st.sidebar:
    st.header("1. API Setup")
    api_key = st.text_input("Enter Google Gemini API Key", type="password", help="Get this from aistudio.google.com")
    
    st.header("2. Class Details")
    grade_level = st.text_input("Grade Level", "Grade 5")
    subject = st.text_input("Subject", "Science")
    quarter = st.text_input("Quarter/Week", "Quarter 1 - Week 1")
    
    st.header("3. Standards")
    content_std = st.text_area("Content Standard", height=100)
    perf_std = st.text_area("Performance Standard", height=100)
    competency = st.text_area("Learning Competency", height=100)
    
    st.header("4. Upload Module")
    uploaded_file = st.file_uploader("Upload Module (Text/PDF)", type=['txt', 'pdf'])

# --- 3. DAILY OBJECTIVES INPUT ---
st.subheader("Daily Objectives")
cols = st.columns(5)
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
objectives = {}

for i, day in enumerate(days):
    with cols[i]:
        objectives[day] = st.text_area(f"{day} Objective", height=100)

# --- HELPER: FIND VALID MODEL ---
def get_valid_model():
    """Finds the best available model to avoid 404 errors."""
    try:
        # Try specific stable models first
        priority_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-pro"]
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Check if any priority model exists in the available list
        for p_model in priority_models:
             # The API usually returns names like 'models/gemini-1.5-flash', so we check if our string is in there
            for avail in available_models:
                if p_model in avail:
                    return avail
        
        # Fallback: Just take the first available model
        return available_models[0]
    except Exception as e:
        # If listing fails, default to a safe bet
        return "gemini-1.5-flash"

# --- 4. GENERATION LOGIC ---
if st.button("Generate Lesson Plan", type="primary"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar.")
    elif not uploaded_file:
        st.error("Please upload a module/material.")
    else:
        with st.spinner("AI is reading your module and creating the lesson plan... (This takes about 30 seconds)"):
            try:
                # Configure AI
                genai.configure(api_key=api_key)
                
                # Get Valid Model Name Dynamically
                model_name = get_valid_model()
                # st.info(f"Using AI Model: {model_name}") # Uncomment to see which model is being used
                
                # Process File
                file_bytes = uploaded_file.getvalue()
                
                # Setup Model
                model = genai.GenerativeModel(model_name)
                
                # Create the Prompt
                prompt_text = f"""
                You are a DepEd Curriculum Expert. Create a Weekly Lesson Plan (DLL) for {grade_level} {subject}.
                
                Context:
                - Content Standard: {content_std}
                - Performance Standard: {perf_std}
                - Competency: {competency}
                - Daily Objectives: {json.dumps(objectives)}
                
                Task:
                Using the attached file as the learning resource, fill out the specific DLL matrix.
                
                Output Format:
                Return ONLY valid JSON. The JSON should be a list of objects where keys are the lesson parts and values are objects containing days.
                
                Structure:
                {{
                    "review": {{"Monday": "...", "Tuesday": "...", ...}},
                    "purpose": {{"Monday": "...", "Tuesday": "...", ...}},
                    "examples": {{"Monday": "...", "Tuesday": "...", ...}},
                    "discuss_1": {{"Monday": "...", "Tuesday": "...", ...}},
                    "discuss_2": {{"Monday": "...", "Tuesday": "...", ...}},
                    "mastery": {{"Monday": "...", "Tuesday": "...", ...}},
                    "application": {{"Monday": "...", "Tuesday": "...", ...}},
                    "generalization": {{"Monday": "...", "Tuesday": "...", ...}},
                    "evaluation": {{"Monday": "...", "Tuesday": "...", ...}},
                    "remediation": {{"Monday": "...", "Tuesday": "...", ...}}
                }}
                """
                
                # Generate content
                response = model.generate_content([
                    {'mime_type': uploaded_file.type, 'data': file_bytes},
                    prompt_text
                ])
                
                # Parse JSON (Handle potential markdown formatting)
                json_str = response.text
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                     json_str = json_str.split("```")[1]
                
                data = json.loads(json_str)
                
                # --- 5. CREATE WORD DOC ---
                doc = Document()
                
                # Title
                style
