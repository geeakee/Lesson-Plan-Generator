import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
import json
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="DepEd AI Lesson Planner", layout="wide")
st.title("📚 AI Weekly Lesson Plan Generator (DLL)")

# --- 2. SIDEBAR INPUTS ---
with st.sidebar:
    st.header("1. API Setup")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    
    st.header("2. Class Details")
    grade_level = st.text_input("Grade Level", "Grade 5")
    subject = st.text_input("Subject", "Science")
    quarter = st.text_input("Quarter/Week", "Quarter 1 - Week 1")
    
    st.header("3. Standards")
    content_std = st.text_area("Content Standard", height=100)
    perf_std = st.text_area("Performance Standard", height=100)
    competency = st.text_area("Learning Competency", height=100)
    
    st.header("4. Upload Module")
    uploaded_file = st.file_uploader("Upload Module", type=['txt', 'pdf'])

# --- 3. MAIN AREA: OBJECTIVES ---
st.subheader("Daily Objectives")
cols = st.columns(5)
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
objectives = {}

for i, day in enumerate(days):
    with cols[i]:
        objectives[day] = st.text_area(f"{day}", height=100)

# --- 4. HELPER FUNCTION ---
def get_gemini_model():
    """Tries to find a working Gemini model."""
    try:
        valid_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        return valid_models[0] # Default to flash for speed
    except:
        return "gemini-1.5-flash"

# --- 5. GENERATION LOGIC ---
if st.button("Generate Lesson Plan", type="primary"):
    # Error Checks first (prevents deep nesting)
    if not api_key:
        st.error("⚠️ Please enter your API Key in the sidebar.")
        st.stop()
    
    if not uploaded_file:
        st.error("⚠️ Please upload a module (PDF or Text).")
        st.stop()

    # If we pass checks, run the AI
    status_text = st.empty()
    status_text.info("⏳ AI is reading your module... please wait.")

    try:
        # A. Setup AI
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(get_gemini_model())
        
        # B. Prepare Data
        file_bytes = uploaded_file.getvalue()
        
        prompt = f"""
        You are a DepEd Curriculum Expert. Create a Weekly Lesson Plan (DLL) for {grade_level} {subject}.
        
        Context:
        - Content Standard: {content_std}
        - Performance Standard: {perf_std}
        - Competency: {competency}
        - Daily Objectives: {json.dumps(objectives)}
        
        Task:
        Using the attached file as the source, fill out the DLL matrix.
        
        Output Format:
        Return ONLY valid JSON. Structure:
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

        # C. Call AI
        response = model.generate_content([
            {'mime_type': uploaded_file.type, 'data': file_bytes},
            prompt
        ])

        # D. Clean JSON
        json_str = response.text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1]
            
        data = json.loads(json_str)

        # E. Create Document
        doc = Document()
        
        # Styles
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Arial'
        font.size = Pt(11)

        doc.add_heading(f'Daily Lesson Log - {subject} {grade_level}', 0)
        doc.add_paragraph(f'Week: {quarter}')
        doc.add_paragraph(f'Content Standard: {content_std}')
        doc.add_paragraph(f'Performance Standard: {perf_std}')
        doc.add_paragraph(f'Competency: {competency}')

        # Table Setup
        table = doc.add_table(rows=1, cols=6)
        table.style = 'Table Grid'
        
        # Headers
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Parts of the Lesson"
        for i, day in enumerate(days):
            hdr_cells[i+1].text = day
        
        # Rows
        row_labels = [
            ("review", "Reviewing previous lesson"),
            ("purpose", "Establishing purpose"),
            ("examples", "Presenting examples"),
            ("discuss_1", "Discussing new concepts #1"),
            ("discuss_2", "Discussing new concepts #2"),
            ("mastery", "Developing Mastery"),
            ("application", "Practical application"),
            ("generalization", "Making generalizations"),
            ("evaluation", "Evaluating learning"),
            ("remediation", "Additional activities")
        ]

        for key, label in row_labels:
            row_cells = table.add_row().cells
            row_cells[0].text = label
            if key in data:
                for i, day in enumerate(days):
                    row_cells[i+1].text = data[key].get(day, "")

        # F. Download Button
        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)

        status_text.success("✅ Lesson Plan Generated Successfully!")
        
        st.download_button(
            label="Download Word File (.docx)",
            data=doc_io,
            file_name=f"DLL_{subject}_{grade_level}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        status_text.error(f"An error occurred: {e}")
