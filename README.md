# MedVAT - Medical Video Assessment Tool

AI-powered desktop application for automated assessment of surgical and clinical skills videos using Google Gemini 1.5 Pro.

## Setup

### Virtual Environment

This project uses a Python virtual environment to isolate dependencies.

**To activate the virtual environment:**

On Windows (Git Bash):
```bash
source venv/Scripts/activate
```

On Windows (Command Prompt):
```bash
venv\Scripts\activate
```

On Windows (PowerShell):
```bash
venv\Scripts\Activate.ps1
```

**To deactivate:**
```bash
deactivate
```

### Dependencies

All dependencies are listed in `requirements.txt` and have been installed in the virtual environment:

- `google-generativeai` - Google Gemini API client
- `customtkinter` - Modern GUI framework
- `reportlab` - PDF generation
- `pandas` - Data handling

## Running the Application

1. Activate the virtual environment (see above)
2. Run the application:
```bash
python medvat_app.py
```

## Usage

1. **Enter API Key**: Paste your Google Gemini API key in the sidebar
2. **Select Rubric**: Choose from available assessment rubrics
3. **Select Video**: Choose a video file (MP4, MOV, AVI, MKV)
4. **Run Analysis**: Click "RUN AI ANALYSIS" to process the video
5. **Review & Edit**: Review AI-generated scores and feedback, edit as needed
6. **Export PDF**: Generate a professional PDF report

## Features

- AI-powered video analysis using Gemini 1.5 Pro
- Dynamic form generation based on rubric structure
- Binary (Yes/No) and Likert (1-5) scoring options
- Editable AI-generated feedback
- Professional PDF report generation
- Dark theme UI optimized for clinical settings

## Requirements

- Python 3.10+
- Google Gemini API key
- Video files in MP4, MOV, AVI, or MKV format


