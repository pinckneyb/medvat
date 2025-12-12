import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import threading
import time
import json
import os
from datetime import datetime
import google.generativeai as genai
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class RubricManager:
    """
    Manages the definitions of different assessment rubrics.
    """
    @staticmethod
    def get_rubrics():
        return {
            "Suturing: Simple Interrupted": {
                "title": "Simple Interrupted Suture Assessment",
                "category": "Suturing",
                "subcategory": "Simple Interrupted",
                "items": [
                    {"name": "Perpendicular needle passes", "type": "likert", "desc": "Needle enters/exits at ~90°, symmetric bites."},
                    {"name": "Gentle tissue handling", "type": "likert", "desc": "Use of forceps without crushing or repeated grasping. Single clean grasp per edge, no trauma."},
                    {"name": "Square, secure knots", "type": "likert", "desc": "Flat, square, properly tightened, not loose."},
                    {"name": "Appropriate tension", "type": "likert", "desc": "Skin edges meet without squeezing or gaps. Edges just touch, no blanching or puckering."},
                    {"name": "Even spacing", "type": "likert", "desc": "Distance between stitches. Each 0.5-1cm apart, uniform."},
                    {"name": "Dermal and epidermal apposition", "type": "likert", "desc": "How well layers meet. Layers aligned; mild eversion fine but not required."},
                    {"name": "Economy of motion", "type": "likert", "desc": "Efficiency during suturing. Hands stay close to field, minimal unnecessary motion."}
                ]
            },
            "Suturing: Vertical Mattress": {
                "title": "Vertical Mattress Suture Assessment",
                "category": "Suturing",
                "subcategory": "Vertical Mattress",
                "items": [
                    {"name": "Correct far-far and near-near", "type": "likert", "desc": "Placement of deep and superficial bites. Deep supports wound, shallow closes skin."},
                    {"name": "Gentle tissue handling", "type": "likert", "desc": "Avoiding rough handling. Single, light grasps per edge."},
                    {"name": "Square, secure knots", "type": "likert", "desc": "Knot integrity. Flat, tight, not slipping."},
                    {"name": "Balanced deep/superficial tension", "type": "likert", "desc": "Relationship between inner and outer tension. Deep supports wound, superficial not strangling tissue."},
                    {"name": "Even spacing", "type": "likert", "desc": "Stitch intervals. Consistent, 0.5-1cm apart."},
                    {"name": "Proper eversion", "type": "likert", "desc": "Skin edges slightly raised. Uniform ridge, no inversion."},
                    {"name": "Economy of motion", "type": "likert", "desc": "Efficiency. Few wasted movements, steady rhythm."}
                ]
            },
            "Suturing: Subcuticular": {
                "title": "Subcuticular Suture Assessment",
                "category": "Suturing",
                "subcategory": "Subcuticular",
                "items": [
                    {"name": "Consistent dermal bites", "type": "likert", "desc": "Depth and spacing of bites in continuous run. Smooth, even rhythm without irregular spacing."},
                    {"name": "Entry/exit symmetry", "type": "likert", "desc": "How evenly left and right bites mirror. Same depth and offset each side."},
                    {"name": "No unintended surface breaches", "type": "likert", "desc": "Whether suture stays beneath epidermis. Only start/finish exposed; no loops outside."},
                    {"name": "Gentle tissue handling", "type": "likert", "desc": "Smooth needle driving and tension control. Controlled, atraumatic, no heavy pressure."},
                    {"name": "Square, secure knots", "type": "likert", "desc": "Knot formation and concealment. Square, tight, hidden or buried."},
                    {"name": "Flat skin approximation", "type": "likert", "desc": "Final cosmetic appearance. Smooth surface, no ridges or gaps."},
                    {"name": "Economy of motion", "type": "likert", "desc": "Efficiency and organization. Continuous, confident workflow, few interruptions."}
                ]
            },
            "Suturing: Auto-Detect": {
                "title": "Suturing Assessment (Pattern Auto-Detected)",
                "category": "Suturing",
                "subcategory": "Auto-Detect",
                "items": [
                    {"name": "Perpendicular needle passes", "type": "likert", "desc": "Needle enters/exits at ~90°, symmetric bites."},
                    {"name": "Gentle tissue handling", "type": "likert", "desc": "Use of forceps without crushing or repeated grasping."},
                    {"name": "Square, secure knots", "type": "likert", "desc": "Flat, square, properly tightened, not loose."},
                    {"name": "Appropriate tension", "type": "likert", "desc": "Skin edges meet without squeezing or gaps."},
                    {"name": "Even spacing", "type": "likert", "desc": "Distance between stitches. Each 0.5-1cm apart, uniform."},
                    {"name": "Economy of motion", "type": "likert", "desc": "Efficiency during suturing. Hands stay close to field, minimal unnecessary motion."}
                ],
                "auto_detect": True
            },
            "Chest Tube Insertion VOP": {
                "title": "VOP - Chest Tube Insertion",
                "category": "Procedures",
                "subcategory": None,
                "items": [
                    {"name": "Selects appropriate site for incision - mid axillary", "type": "binary", "desc": ""},
                    {"name": "Infiltrates local anesthetic at appropriate site", "type": "binary", "desc": ""},
                    {"name": "2 cm transverse incision through skin", "type": "binary", "desc": ""},
                    {"name": "Uses a Kelly to bluntly dissect down to chest wall", "type": "binary", "desc": ""},
                    {"name": "Blunt dissection on top of rib one interspace higher than incision", "type": "binary", "desc": ""},
                    {"name": "Dissects with gentle pressure through intercostals muscles, enters pleura", "type": "binary", "desc": ""},
                    {"name": "Grasps tube with Kelly, carefully", "type": "binary", "desc": ""},
                    {"name": "Advances chest tube past the last tube hole", "type": "binary", "desc": ""},
                    {"name": "Secures chest tube with a suture", "type": "binary", "desc": ""},
                    {"name": "Economy of Time and Motion", "type": "likert", "desc": "Many unnecessary / disorganized movements (1) → Organized time / motion, some unnecessary movements (3) → Maximum economy of movement and efficiency (5)"},
                    {"name": "Final Rating / Demonstrates Proficiency", "type": "binary", "desc": ""}
                ]
            },
            "Standardized Patient Encounter": {
                "title": "SP Communication Assessment",
                "category": "Communication",
                "subcategory": None,
                "items": [
                    {"name": "Introduction & Role ID", "type": "likert", "desc": "Clear introduction."},
                    {"name": "Open-ended questioning", "type": "likert", "desc": "Starts broad before narrowing."},
                    {"name": "Empathy & Validation", "type": "likert", "desc": "Acknowledges patient emotion."},
                    {"name": "No Medical Jargon", "type": "likert", "desc": "Uses lay terms."},
                    {"name": "Closure & Teach-back", "type": "likert", "desc": "Ensures patient understanding."}
                ]
            }
        }
    
    @staticmethod
    def get_rubrics_by_category():
        """Organize rubrics by category for hierarchical display."""
        rubrics = RubricManager.get_rubrics()
        categories = {}
        
        for key, rubric in rubrics.items():
            category = rubric.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append((key, rubric))
        
        return categories

class ErrorHandler:
    """
    Provides user-friendly error messages with actionable steps.
    """
    @staticmethod
    def format_error(error_type, error_details, is_fatal=False):
        """
        Format error messages in plain English with actionable steps.
        
        Args:
            error_type: Type of error (e.g., "Video Upload Failed", "API Error")
            error_details: Detailed error message
            is_fatal: Whether this error requires abandoning the assessment
        
        Returns:
            Formatted error message with steps to resolve
        """
        base_message = f"{error_type}\n\nDetails: {error_details}\n\n"
        
        if is_fatal:
            base_message += "⚠️ FATAL ERROR: This assessment cannot be completed.\n\n"
        else:
            base_message += "ℹ️ This error may be recoverable. Please try the steps below.\n\n"
        
        # Error-specific guidance
        if "404" in error_details or "not found" in error_details.lower():
            return base_message + """HOW TO FIX:
1. Check that your API key has access to the selected model
2. Try switching to a different model (e.g., gemini-2.5-flash)
3. Verify your API key is correct and active
4. Check Google AI Studio for model availability status"""
        
        elif "403" in error_details or "permission" in error_details.lower() or "forbidden" in error_details.lower():
            return base_message + """HOW TO FIX:
1. Verify your API key has the necessary permissions
2. Check your Google Cloud project billing status
3. Ensure your API key hasn't been revoked
4. Try regenerating your API key from Google AI Studio"""
        
        elif "401" in error_details or "invalid" in error_details.lower() or "unauthorized" in error_details.lower():
            return base_message + """HOW TO FIX:
1. Check that your API key is correct (no extra spaces)
2. Verify the API key is from Google AI Studio (not Google Cloud)
3. Try pasting the API key again
4. Generate a new API key if needed"""
        
        elif "timeout" in error_details.lower() or "timed out" in error_details.lower():
            return base_message + """HOW TO FIX:
1. Check your internet connection
2. The video may be too large - try a shorter video
3. Wait a few minutes and try again
4. Check Google AI service status"""
        
        elif "file" in error_details.lower() and ("not found" in error_details.lower() or "cannot" in error_details.lower()):
            return base_message + """HOW TO FIX:
1. Verify the video file still exists at the original location
2. Check that you have read permissions for the file
3. Ensure the file isn't open in another program
4. Try selecting the file again"""
        
        elif "json" in error_details.lower() or "parse" in error_details.lower() or "extra data" in error_details.lower():
            return base_message + """HOW TO FIX:
1. This is usually a temporary AI response issue
2. Try running the analysis again
3. If it persists, try switching to a different model
4. The video assessment may need to be abandoned if this continues"""
        
        elif "video processing failed" in error_details.lower() or "upload" in error_details.lower():
            return base_message + """HOW TO FIX:
1. Check that the video file is a valid format (MP4, MOV, AVI, MKV)
2. Ensure the video file isn't corrupted
3. Try converting the video to MP4 format
4. Check file size - very large files may timeout"""
        
        elif "quota" in error_details.lower() or "limit" in error_details.lower() or "rate limit" in error_details.lower():
            return base_message + """HOW TO FIX:
1. You've reached your API usage limit
2. Wait a few minutes before trying again
3. Check your Google AI Studio quota limits
4. Consider upgrading your API tier if needed"""
        
        else:
            return base_message + """HOW TO FIX:
1. Try running the analysis again
2. Check your internet connection
3. Verify your API key is valid
4. If the error persists, try restarting the application
5. Contact support if the problem continues"""

class ConfigManager:
    """
    Manages saving and loading configuration (API key).
    """
    CONFIG_FILE = "medvat_config.json"
    
    @staticmethod
    def load_config():
        """Load configuration from file."""
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    @staticmethod
    def save_config(config):
        """Save configuration to file."""
        try:
            with open(ConfigManager.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

class GeminiClient:
    """
    Handles the interaction with the Google Gemini API.
    """
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
    
    @staticmethod
    def fetch_available_models(api_key):
        """
        Query the API for available models that support generateContent.
        Returns (models_list, error_message)
        """
        # Safe fallback defaults
        FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
        
        if not api_key:
            print("[Model Discovery] No API key provided, using fallback models")
            return FALLBACK_MODELS, None
        
        try:
            genai.configure(api_key=api_key)
            
            # Query available models
            print("[Model Discovery] Querying API for available models...")
            models_iter = genai.list_models()
            models_list = list(models_iter)
            
            if not models_list:
                print("[Model Discovery] No models returned from API, using fallback")
                return FALLBACK_MODELS, "No models returned from API"
            
            # Filter models that support generateContent
            available_models = []
            for model in models_list:
                try:
                    # Safely access supported_generation_methods attribute
                    supported_methods = getattr(model, 'supported_generation_methods', [])
                    
                    # Check if model supports generateContent method
                    if supported_methods and 'generateContent' in supported_methods:
                        model_name = getattr(model, 'name', '')
                        # Extract just the model name (remove 'models/' prefix if present)
                        if '/' in model_name:
                            model_name = model_name.split('/')[-1]
                        if model_name:
                            available_models.append(model_name)
                            print(f"[Model Discovery] Found: {model_name}")
                except Exception as e:
                    print(f"[Model Discovery] Error processing model: {e}")
                    continue
            
            if available_models:
                print(f"[Model Discovery] Success! Found {len(available_models)} models with generateContent support:")
                for model in available_models:
                    print(f"  - {model}")
                return available_models, None
            else:
                print("[Model Discovery] No models found with generateContent support, using fallback")
                return FALLBACK_MODELS, "No models found with generateContent support"
                
        except Exception as e:
            error_msg = str(e)
            print(f"[Model Discovery] Error querying models: {error_msg}")
            print(f"[Model Discovery] Falling back to default models: {FALLBACK_MODELS}")
            
            # Check for specific error types
            if "401" in error_msg or "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return FALLBACK_MODELS, "Invalid API key"
            elif "403" in error_msg or "permission" in error_msg.lower():
                return FALLBACK_MODELS, "API key lacks permission to list models"
            else:
                return FALLBACK_MODELS, f"API error: {error_msg[:100]}"
    
    @staticmethod
    def check_model_availability(api_key, model_name):
        """
        Ping the model to check if it's available with the given API key.
        Returns (is_available, error_message)
        """
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name=model_name)
            # Simple test prompt to verify model access
            response = model.generate_content(
                "Say 'OK'",
                request_options={"timeout": 10}
            )
            return True, None
        except Exception as e:
            error_msg = str(e)
            # Check for common error patterns
            if "404" in error_msg or "not found" in error_msg.lower():
                return False, f"Model {model_name} not available (404)"
            elif "403" in error_msg or "permission" in error_msg.lower():
                return False, f"API key lacks access to {model_name}"
            elif "401" in error_msg or "invalid" in error_msg.lower():
                return False, "Invalid API key"
            else:
                return False, f"Error: {error_msg[:100]}"

    def analyze_video(self, video_path, rubric_data, progress_callback, model_name="gemini-2.5-flash", auto_detect_pattern=False, api_key=None):
        try:
            if api_key:
                genai.configure(api_key=api_key)
            
            # 1. Upload File
            progress_callback("Uploading video to Gemini...", 0.1)
            try:
                # Check if file exists
                if not os.path.exists(video_path):
                    error_msg = ErrorHandler.format_error(
                        "Video File Not Found",
                        f"The video file could not be found at: {video_path}",
                        is_fatal=True
                    )
                    return {"error": error_msg, "fatal": True}
                
                # Check file size (warn if very large)
                file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                if file_size_mb > 100:
                    print(f"Warning: Large video file ({file_size_mb:.1f} MB) may take longer to process")
                
                video_file = genai.upload_file(path=video_path)
            except FileNotFoundError:
                error_msg = ErrorHandler.format_error(
                    "Video File Not Found",
                    f"The video file could not be found. It may have been moved or deleted.",
                    is_fatal=True
                )
                return {"error": error_msg, "fatal": True}
            except PermissionError:
                error_msg = ErrorHandler.format_error(
                    "File Access Denied",
                    f"You don't have permission to read the video file. Check file permissions.",
                    is_fatal=True
                )
                return {"error": error_msg, "fatal": True}
            except Exception as e:
                error_msg = ErrorHandler.format_error(
                    "Video Upload Failed",
                    f"Could not upload video file: {str(e)}",
                    is_fatal=True
                )
                return {"error": error_msg, "fatal": True}
            
            # 2. Wait for Processing
            progress_callback("Processing video (this may take a moment)...", 0.3)
            max_wait_time = 300  # 5 minutes max wait
            wait_time = 0
            while video_file.state.name == "PROCESSING":
                if wait_time >= max_wait_time:
                    error_msg = ErrorHandler.format_error(
                        "Video Processing Timeout",
                        "The video processing took too long. This may be due to a very large file or server issues.",
                        is_fatal=True
                    )
                    try:
                        genai.delete_file(video_file.name)
                    except:
                        pass
                    return {"error": error_msg, "fatal": True}
                time.sleep(2)
                wait_time += 2
                try:
                    video_file = genai.get_file(video_file.name)
                except Exception as e:
                    error_msg = ErrorHandler.format_error(
                        "Video Processing Error",
                        f"Error checking video processing status: {str(e)}",
                        is_fatal=True
                    )
                    return {"error": error_msg, "fatal": True}
            
            if video_file.state.name == "FAILED":
                error_msg = ErrorHandler.format_error(
                    "Video Processing Failed",
                    "Google's servers could not process your video file. This may be due to file format, corruption, or size issues.",
                    is_fatal=True
                )
                return {"error": error_msg, "fatal": True}
            
            # 2.5. Auto-detect suturing pattern if needed
            detected_pattern = None
            if auto_detect_pattern:
                progress_callback("Detecting suturing pattern...", 0.4)
                detected_pattern = GeminiClient._detect_suturing_pattern(video_file, model_name, api_key)
                if detected_pattern:
                    # Update rubric_data with detected pattern's rubric
                    all_rubrics = RubricManager.get_rubrics()
                    pattern_key = f"Suturing: {detected_pattern}"
                    if pattern_key in all_rubrics:
                        rubric_data = all_rubrics[pattern_key]
                        progress_callback(f"Detected pattern: {detected_pattern}", 0.5)
                    else:
                        progress_callback("Pattern detection inconclusive, using generic rubric", 0.5)
                else:
                    progress_callback("Pattern detection inconclusive, using generic rubric", 0.5)
            
            # 3. Construct Prompt
            progress_callback(f"Analyzing content against rubric using {model_name}...", 0.6)
            
            rubric_text = json.dumps(rubric_data, indent=2)
            rubric_title = rubric_data.get('title', '')
            
            # Build rubric-specific instructions based on procedure type
            special_instructions = ""
            
            if "Chest Tube" in rubric_title:
                special_instructions = """
                
                CRITICAL ASSESSMENT DIRECTIVE: PATIENT IMPACT & FINESSE
                
                You must evaluate not just *if* a step was done, but *how* it was done, with a specific focus on patient trauma and pain.
                
                1. **Dissection Finesse (The "One-Pass" Rule):**
                   - **Ideal:** The practitioner should spread the intercostal muscles firmly and decisively in 1-2 motions to create the track.
                   - **Red Flag (Pain/Trauma):** Watch closely for "pecking," "searching," or repetitive small spreading motions with the Kelly clamp deep in the tissue.
                   - **Assessment Impact:** If you see multiple (>3) separate spreading maneuvers at the same depth, you must downgrade "Economy of Motion" and flag "Dissects with gentle pressure" as a potential failure due to excessive trauma, even if they eventually enter the pleura.
                   - **Rationale:** Repeated spreading of the intercostal muscles is excruciatingly painful for a conscious patient and increases the risk of intercostal nerve injury.
                
                2. **Economy of Motion as a Proxy for Competence:**
                   - Do not rate "Economy of Motion" highly just because the student is moving quickly.
                   - Look for *purposeful* movement. Fumbling with the suture, losing the tail, or repeatedly picking up/putting down instruments are signs of cognitive load overload and should lower the score.
                   - Watch the blunt dissection closely. Count the number of spreading maneuvers.
                   - Ideal technique is 'push, spread, advance.' Repetitive 'pecking' is incorrect.
                   - Flag any motion that looks like it would cause unnecessary pain in a conscious patient.
                
                3. **Holistic Impact:**
                   - If a step is technically completed (e.g., the tube goes in) but the technique was traumatic (excessive force, repetitive spreading), the specific step (e.g., "Enters pleura") should be marked as **"No"** or **"Marginal,"** and the feedback must explicitly mention "patient pain" or "excessive tissue trauma."
                
                CALIBRATION UPDATE: THE "NOVICE CURVE"
                
                You are evaluating a resident in training. Be critical of technique, but pragmatic about scoring.
                
                1. **The "Pecking" Rule:**
                   - Repetitive "pecking" or small spreading motions during dissection are common in novices.
                   - **Scoring:** If the dissection remains safely over the rib and enters the pleura without damaging surrounding structures, mark the step as **"YES"** (Pass).
                   - **Feedback:** Do NOT fail the step solely for pecking. Instead, use the "Feedback" box to strongly critique the inefficiency and mention the potential for increased patient pain.
                   - **Fail Criteria:** Only mark "No" if the motion creates a false track, slips off the rib dangerously, or is violent/uncontrolled.
                
                2. **Proficiency Threshold:**
                   - A student can demonstrate "Proficiency" (Pass) even with imperfect economy of motion.
                   - Proficiency means "Safe to perform under supervision," not "Master surgeon."
                   - If the tube is in safely and secured, lean towards a "Yes" on proficiency unless a critical safety violation occurred.
                
                """
            elif "Suturing" in rubric_title:
                special_instructions = """
                
                CRITICAL ASSESSMENT DIRECTIVE: PATIENT IMPACT & FINESSE
                
                You must evaluate not just *if* a step was done, but *how* it was done, with a specific focus on patient trauma and tissue handling.
                
                1. **Tissue Handling Finesse:**
                   - Watch for excessive force or repeated grasping of tissue with forceps, which causes trauma.
                   - Multiple attempts to grasp the same tissue indicate poor technique and should lower scores.
                   - Look for signs of crushing or tearing tissue during manipulation.
                
                2. **Economy of Motion:**
                   - Do not rate "Economy of Motion" highly just because the student is moving quickly.
                   - Look for *purposeful* movement. Dropping instruments, fumbling with sutures, or repeatedly adjusting position are signs of inefficiency and should lower the score.
                   - Each motion should have clear intent and contribute to progress.
                
                3. **Holistic Impact:**
                   - If sutures are placed but tissue handling was traumatic (excessive force, repeated grasping), mark "Gentle tissue handling" as low and explicitly mention "patient trauma" or "tissue damage" in feedback.
                
                CALIBRATION DIRECTIVE: DISTINGUISHING "CLUMSY" FROM "UNSAFE"
                
                You are evaluating a *novice resident*, not an expert surgeon. You must distinguish between "inefficient/clumsy" (which is acceptable for a pass) and "dangerous/traumatic" (which is a fail).
                
                1. **The "Good Enough" Standard:**
                   - If the student achieves the clinical goal (e.g., places sutures correctly, closes wound) but takes 2-3 extra attempts or looks stiff/hesitant, mark the step as **"Pass"** (score 3-4 for likert, "Yes" for binary) but note the inefficiency in the feedback.
                   - Only mark a step as **"Fail"** (score 1-2 for likert, "No" for binary) if the action was *ineffective* (sutures don't hold, wound doesn't close) or *dangerous* (visible tissue damage, excessive bleeding from technique).
                
                2. **Evaluating "Clumsiness" vs. "Trauma":**
                   - Multiple attempts to grasp tissue or place a suture is inefficient but not automatically a failure unless it causes visible tissue damage or is excessive (>5-6 attempts for the same action).
                   - If they fumble but eventually place sutures correctly without causing harm, score as **"Pass"** but downgrade "Economy of Motion" and "Gentle tissue handling" scores.
                
                3. **Holistic Proficiency:**
                   - A student can be "Proficient" (score 3-4) even with poor economy of motion, provided they are safe and achieve the clinical goal. Do not fail the entire procedure solely for slowness, stiffness, or minor inefficiencies.
                
                """
            elif "Patient Encounter" in rubric_title or "SP" in rubric_title:
                special_instructions = """
                
                CRITICAL ASSESSMENT DIRECTIVE: PATIENT EXPERIENCE & COMMUNICATION
                
                You must evaluate not just *if* communication occurred, but *how* it impacted the patient experience.
                
                1. **Empathy & Validation:**
                   - Look for genuine acknowledgment of patient emotions, not just perfunctory responses.
                   - Watch for non-verbal cues that show the practitioner is truly listening and responding to patient concerns.
                
                2. **Communication Efficiency:**
                   - Do not rate highly just because questions were asked quickly.
                   - Look for *purposeful* communication that builds rapport and gathers necessary information without causing patient distress.
                   - Repetitive questioning or asking the same thing multiple ways indicates poor communication skills.
                
                3. **Holistic Impact:**
                   - If communication occurred but the patient appeared uncomfortable, anxious, or confused, mark relevant items lower and explicitly mention "patient distress" or "communication breakdown" in feedback.
                
                """
            else:
                # Generic patient-focused instructions for other procedures
                special_instructions = """
                
                CRITICAL ASSESSMENT DIRECTIVE: PATIENT IMPACT & FINESSE
                
                You must evaluate not just *if* steps were completed, but *how* they were performed, with a specific focus on patient safety, comfort, and tissue trauma.
                
                1. **Technique Finesse:**
                   - Watch for signs of excessive force, repetitive unnecessary motions, or fumbling that could cause patient discomfort or trauma.
                   - Multiple attempts to complete the same step indicate poor technique and should lower scores.
                
                2. **Economy of Motion:**
                   - Do not rate "Economy of Motion" highly just because the student is moving quickly.
                   - Look for *purposeful* movement. Dropping instruments, fumbling, or repeatedly adjusting position are signs of inefficiency and should lower the score.
                
                3. **Holistic Impact:**
                   - If steps are technically completed but the technique was traumatic or inefficient, mark relevant items lower and explicitly mention "patient trauma," "excessive force," or "inefficient technique" in feedback.
                
                CALIBRATION DIRECTIVE: DISTINGUISHING "CLUMSY" FROM "UNSAFE"
                
                You are evaluating a *novice resident*, not an expert surgeon. You must distinguish between "inefficient/clumsy" (which is acceptable for a pass) and "dangerous/traumatic" (which is a fail).
                
                1. **The "Good Enough" Standard:**
                   - If the student achieves the clinical goal but takes 2-3 extra attempts or looks stiff/hesitant, mark the step as **"Pass"** (score 3-4 for likert, "Yes" for binary) but note the inefficiency in the feedback.
                   - Only mark a step as **"Fail"** (score 1-2 for likert, "No" for binary) if the action was *ineffective* (didn't achieve the goal) or *dangerous* (risked patient harm).
                
                2. **Evaluating Inefficiency vs. Danger:**
                   - Multiple attempts or fumbling is inefficient but not automatically a failure unless it causes harm or is excessive (>5-6 attempts for the same action).
                   - If they eventually complete the step safely and effectively, score as **"Pass"** but downgrade efficiency-related scores.
                
                3. **Holistic Proficiency:**
                   - A student can be "Proficient" (score 3-4) even with poor economy of motion, provided they are safe and achieve the clinical goal. Do not fail the entire procedure solely for slowness, stiffness, or minor inefficiencies.
                
                """
            
            prompt = f"""
            You are an expert medical evaluator. Watch the attached video and assess the performance based strictly on the following rubric.
            
            Your goal is to provide feedback that a student can verify. If you claim they 'pecked' during dissection, tell them exactly when it happened so they can watch the video and see it themselves.
            
            RUBRIC DEFINITION:
            
            {rubric_text}
            
            {special_instructions}
            
            INSTRUCTIONS:
            
            1. Provide a score for each item.
               - For 'likert' type: Score 1 (Novice) to 5 (Expert).
               - For 'binary' type: Score 1 (Yes/Done) or 0 (No/Not Done).
               - **CRITICAL:** Evaluate not just whether steps were completed, but HOW they were performed. Consider patient trauma, pain, and tissue damage in your scoring.
               - **CALIBRATION:** Remember you are evaluating a novice resident. Distinguish between "inefficient/clumsy" (acceptable for pass, score 3-4) and "dangerous/traumatic" (fail, score 1-2). If the clinical goal is achieved safely, even with inefficiency, mark as Pass but note inefficiency in feedback.
            
            2. **GENERAL SAFETY DIRECTIVE: INSTRUMENT HYGIENE & SAFETY**
               - Regardless of the specific procedure, you must continuously monitor for 'Instrument Hygiene' violations. If any of the following occur, you must flag them immediately in the commentary and potentially fail the relevant step or the entire proficiency rating if the action is dangerous.
               
               a. **Inappropriate Dual-Use:**
                  - Instruments must only be used for their intended purpose.
                  - **CRITICAL FAIL:** Using an instrument to dissect, cut, or spread tissue while it is *simultaneously* holding another object (e.g., a tube, a needle, or gauze). This blunts the instrument, crushes the object, and risks uncontrolled trauma.
                  - **Example:** Dissecting with a Kelly clamp while it is gripping a chest tube.
               
               b. **Uncontrolled Sharps:**
                  - Watch for needles or scalpels being waved in the air, left on the patient drape, or handled with fingers instead of instruments (unless appropriate).
                  - **Flag:** Ideally, sharps should be "parked" safely or handed off immediately after use.
               c. **Loss of Tension/Control:**
                  - Watch for instruments slipping, requiring repeated re-grasping, or being used with a loose grip that allows the tip to wander.
                  - **Comment:** Note any "fumbling" or "resetting" of the grip as an efficiency issue.
               
               **If a Critical Fail (Rule 2a - Inappropriate Dual-Use) is observed:**
                  - Mark the relevant step (e.g., "Grasps tube" or "Dissects") as **"No"**.
                  - Mark "Proficiency" (if present) as **"No"**.
                  - In the feedback, use the phrase: **"CRITICAL SAFETY VIOLATION: Instrument Hygiene."**
            
            3. Provide 'actionable_advice' for every single item based on visual evidence.
               - **MANDATORY:** If you observe signs of patient trauma, excessive force, repetitive unnecessary motions, or inefficiency, you MUST explicitly mention these in your advice.
               - **CALIBRATION:** When noting inefficiency (multiple attempts, fumbling), distinguish between "needs improvement" (for clumsy but safe technique) and "critical error" (for dangerous technique). Provide constructive feedback that helps the resident improve.
               - Focus on specific techniques that would reduce patient discomfort and improve outcomes.
            
            4. Provide a 'summative_comment' for the whole procedure.
               - Include an assessment of overall patient impact and technique finesse.
               - **CALIBRATION:** Acknowledge that novice residents may be slow or clumsy but still proficient if they are safe and achieve the clinical goal. Only fail if there are safety concerns or the procedure was ineffective.
               - Highlight any concerns about patient trauma or inefficient technique, but frame them appropriately for a learning context.
            
            5. **MANDATORY TIMESTAMP REQUIREMENT:**
               - For any criterion where the score indicates poor performance (e.g., 'No' for binary, or <=3 for Likert), you MUST provide a specific timestamp (MM:SS format) in the 'advice' field citing exactly where the error or inefficient behavior occurred.
               - Example format: "[01:15] The student fumbled the needle driver..."
               - Example format: "[02:32] You performed 5 small spreading motions here instead of one decisive spread..."
               - If multiple issues occur at different times, include multiple timestamps: "[01:15] First issue... [02:30] Second issue..."
               - This makes feedback verifiable and actionable. A student can watch the video at that timestamp and see exactly what you're referring to.
               - Note: Scores of 4-5 (Likert) or 'Yes' (binary) do not require timestamps unless there are specific improvement suggestions.
            
            OUTPUT FORMAT:
            
            Return ONLY valid JSON. Do not use Markdown code blocks. The JSON must match this structure:
            
            {{
                "assessments": [
                    {{ "name": "Criterion Name", "score": 3, "advice": "[01:15] Observation and advice with timestamp..." }},
                    ...
                ],
                "summative_comment": "Overall feedback..."
            }}
            
            **CRITICAL:** Every 'advice' field for scores indicating poor performance (binary 'No' or Likert <=3) MUST include at least one timestamp in [MM:SS] format. This is mandatory for verifiable feedback.
            """

            # 4. Generate Content
            try:
                model = genai.GenerativeModel(model_name=model_name)
                response = model.generate_content(
                    [video_file, prompt],
                    request_options={"timeout": 600}
                )
            except Exception as e:
                error_str = str(e)
                # Cleanup uploaded file before returning error
                try:
                    genai.delete_file(video_file.name)
                except:
                    pass
                
                # Determine if fatal
                is_fatal = False
                if "404" in error_str or "not found" in error_str.lower():
                    is_fatal = True
                elif "403" in error_str or "permission" in error_str.lower():
                    is_fatal = True
                elif "401" in error_str or "invalid" in error_str.lower():
                    is_fatal = True
                
                error_msg = ErrorHandler.format_error(
                    "AI Analysis Failed",
                    error_str,
                    is_fatal=is_fatal
                )
                return {"error": error_msg, "fatal": is_fatal}
            
            # 5. Cleanup
            try:
                genai.delete_file(video_file.name)
            except Exception as e:
                print(f"Warning: Could not delete uploaded file: {e}")
            
            progress_callback("Analysis Complete.", 1.0)
            
            # Parse JSON (Strip markdown if present)
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Try to extract JSON if there's extra content
            try:
                # First try parsing directly
                return json.loads(text)
            except json.JSONDecodeError as e:
                # If there's extra data, try to extract just the JSON object
                if "Extra data" in str(e) or e.pos:
                    # Find the first complete JSON object
                    try:
                        # Try to find JSON object boundaries
                        start_idx = text.find('{')
                        if start_idx != -1:
                            # Find matching closing brace
                            brace_count = 0
                            end_idx = start_idx
                            for i in range(start_idx, len(text)):
                                if text[i] == '{':
                                    brace_count += 1
                                elif text[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i + 1
                                        break
                            
                            if end_idx > start_idx:
                                json_text = text[start_idx:end_idx]
                                return json.loads(json_text)
                    except:
                        pass
                
                # If all else fails, return error with helpful message
                error_msg = ErrorHandler.format_error(
                    "AI Response Parsing Error",
                    f"The AI returned a response that couldn't be parsed as JSON. This is usually a temporary issue. Error: {str(e)}",
                    is_fatal=False
                )
                return {"error": error_msg, "fatal": False}
        except Exception as e:
            error_msg = ErrorHandler.format_error(
                "Unexpected Analysis Error",
                f"An unexpected error occurred during video analysis: {str(e)}",
                is_fatal=True
            )
            return {"error": error_msg, "fatal": True}
    
    @staticmethod
    def _detect_suturing_pattern(video_file, model_name, api_key=None):
        """
        Detect which suturing pattern is being used in the video.
        Returns: "Simple Interrupted", "Vertical Mattress", "Subcuticular", or None
        """
        try:
            if api_key:
                genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name=model_name)
            
            detection_prompt = """
            Watch this surgical video and identify which suturing technique is being used.
            
            Possible techniques:
            1. Simple Interrupted - Individual separate stitches, each tied independently
            2. Vertical Mattress - Deep and superficial bites creating a vertical pattern, often with visible eversion
            3. Subcuticular - Continuous running suture beneath the skin surface, minimal visible suture material
            
            Respond with ONLY one of these exact strings:
            - "Simple Interrupted"
            - "Vertical Mattress"  
            - "Subcuticular"
            - "Unknown" (if you cannot determine)
            
            Do not provide any explanation, just the technique name.
            """
            
            response = model.generate_content(
                [video_file, detection_prompt],
                request_options={"timeout": 60}
            )
            
            detected = response.text.strip()
            # Clean up any markdown or extra text
            detected = detected.replace("```", "").strip()
            
            valid_patterns = ["Simple Interrupted", "Vertical Mattress", "Subcuticular"]
            for pattern in valid_patterns:
                if pattern.lower() in detected.lower():
                    return pattern
            
            return None
        except Exception as e:
            print(f"[Pattern Detection] Error: {e}")
            return None

class AssessmentPanel(ctk.CTkScrollableFrame):
    """
    The right-hand panel that displays the form.
    """
    def __init__(self, parent):
        super().__init__(parent, label_text="Assessment Results")
        self.vars = {}
        self.comments = {}
        self.rubric_structure = []

    def build_form(self, rubric_data):
        # Clear old widgets
        for widget in self.winfo_children():
            widget.destroy()
        self.vars = {}
        self.comments = {}
        self.rubric_structure = rubric_data['items']
        
        for i, item in enumerate(self.rubric_structure):
            # Container
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.pack(fill="x", pady=10)
            
            # Header
            header = ctk.CTkLabel(frame, text=f"{i+1}. {item['name']}", font=("Arial", 14, "bold"), anchor="w")
            header.pack(fill="x")
            
            desc = ctk.CTkLabel(frame, text=item.get('desc', ''), font=("Arial", 11), text_color="gray", anchor="w")
            desc.pack(fill="x")
            
            # Controls
            if item['type'] == 'binary':
                var = ctk.StringVar(value="No")
                seg = ctk.CTkSegmentedButton(frame, values=["Yes", "No"], variable=var)
                seg.pack(fill="x", pady=5)
                self.vars[item['name']] = var
            else:
                var = ctk.IntVar(value=3)
                slider_row = ctk.CTkFrame(frame, fg_color="transparent")
                slider_row.pack(fill="x")
                
                lbl_score = ctk.CTkLabel(slider_row, text="Score: 3/5", width=60)
                lbl_score.pack(side="right")
                
                def update_lbl(val, l=lbl_score):
                    l.configure(text=f"Score: {int(val)}/5")
                
                slider = ctk.CTkSlider(slider_row, from_=1, to=5, number_of_steps=4, variable=var, command=update_lbl)
                slider.pack(side="left", fill="x", expand=True)
                self.vars[item['name']] = var
            
            # AI Feedback Box
            fb = ctk.CTkTextbox(frame, height=60, text_color="#DCE4EE")
            fb.pack(fill="x", pady=(5,0))
            self.comments[item['name']] = fb
        
        # Summative
        ctk.CTkLabel(self, text="Holistic Summative Comment", font=("Arial", 16, "bold")).pack(pady=(20,5), anchor="w")
        self.summative_box = ctk.CTkTextbox(self, height=120)
        self.summative_box.pack(fill="x", pady=5)

    def populate_from_ai(self, ai_data):
        if "error" in ai_data:
            # Error messages are already formatted by ErrorHandler
            # Don't show another dialog here - let finish_analysis handle it
            return
        
        # Map list to dict for easy lookup
        ai_map = {item['name']: item for item in ai_data.get('assessments', [])}
        
        for item in self.rubric_structure:
            name = item['name']
            if name in ai_map:
                # Set Score
                if item['type'] == 'binary':
                    val = "Yes" if ai_map[name]['score'] >= 1 else "No"
                    self.vars[name].set(val)
                else:
                    self.vars[name].set(ai_map[name]['score'])
                
                # Set Comment
                self.comments[name].delete("0.0", "end")
                self.comments[name].insert("0.0", ai_map[name].get('advice', ''))
        
        # Set Summative
        self.summative_box.delete("0.0", "end")
        self.summative_box.insert("0.0", ai_data.get('summative_comment', ''))

    def get_data(self):
        results = []
        for item in self.rubric_structure:
            name = item['name']
            results.append({
                "Criterion": name,
                "Score": self.vars[name].get(),
                "Feedback": self.comments[name].get("0.0", "end-1c")
            })
        return results, self.summative_box.get("0.0", "end-1c")

class MedVATApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MedVAT - AI Surgical Assessment")
        self.geometry("1100x800")
        self.selected_video_path = None
        self.rubrics = RubricManager.get_rubrics()
        self.rubrics_by_category = RubricManager.get_rubrics_by_category()
        self.current_rubric_key = list(self.rubrics.keys())[0]
        self.selected_model = None  # Will be set after model discovery
        self.available_models = []  # Will be populated dynamically
        self.detected_suturing_pattern = None  # For auto-detection
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="MedVAT", font=("Arial", 28, "bold")).pack(pady=30)
        
        # API Key Input
        ctk.CTkLabel(self.sidebar, text="Gemini API Key:", anchor="w").pack(padx=20, pady=(0,5), anchor="w")
        self.entry_api_key = ctk.CTkEntry(self.sidebar, placeholder_text="Paste key here...", show="*")
        self.entry_api_key.pack(padx=20, fill="x")
        self.entry_api_key.bind("<KeyRelease>", self.on_api_key_change)
        
        # Model Selection
        ctk.CTkLabel(self.sidebar, text="Model:", anchor="w").pack(padx=20, pady=(20,5), anchor="w")
        model_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        model_frame.pack(padx=20, fill="x")
        
        # Initialize with empty list, will be populated dynamically
        self.model_menu = ctk.CTkOptionMenu(
            model_frame, 
            values=["Loading models..."],
            command=self.change_model,
            state="disabled"
        )
        self.model_menu.pack(side="left", fill="x", expand=True)
        
        # Model Status Indicator
        self.model_status_label = ctk.CTkLabel(
            model_frame, 
            text="●", 
            font=("Arial", 16),
            text_color="gray",
            width=20
        )
        self.model_status_label.pack(side="right", padx=(5, 0))
        
        # Model Status Text
        self.model_status_text = ctk.CTkLabel(
            self.sidebar,
            text="Not checked",
            text_color="gray",
            font=("Arial", 10),
            wraplength=200
        )
        self.model_status_text.pack(padx=20, pady=(2, 0), anchor="w")
        
        # Rubric Selection - Category
        ctk.CTkLabel(self.sidebar, text="Category:", anchor="w").pack(padx=20, pady=(20,5), anchor="w")
        categories = list(self.rubrics_by_category.keys())
        self.category_menu = ctk.CTkOptionMenu(
            self.sidebar, 
            values=categories,
            command=self.change_category
        )
        self.category_menu.set(categories[0] if categories else "")
        self.category_menu.pack(padx=20, fill="x")
        
        # Rubric Selection - Subcategory
        ctk.CTkLabel(self.sidebar, text="Procedure:", anchor="w").pack(padx=20, pady=(20,5), anchor="w")
        self.subcategory_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=[],
            command=self.change_rubric
        )
        self.subcategory_menu.pack(padx=20, fill="x")
        
        # Initialize subcategory dropdown
        self.update_subcategory_menu()
        
        # File Selection
        ctk.CTkLabel(self.sidebar, text="Video File:", anchor="w").pack(padx=20, pady=(20,5), anchor="w")
        file_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        file_frame.pack(padx=20, fill="x")
        
        self.btn_file = ctk.CTkButton(file_frame, text="Select Video", command=self.select_file, fg_color="#3B8ED0", width=100)
        self.btn_file.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_batch = ctk.CTkButton(file_frame, text="Batch", command=self.select_batch_files, fg_color="#8B5CF6", width=80)
        self.btn_batch.pack(side="right")
        
        self.lbl_file = ctk.CTkLabel(self.sidebar, text="No file selected", text_color="gray", wraplength=200)
        self.lbl_file.pack(padx=20, pady=5)
        
        # Batch Status (hidden initially)
        self.batch_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.batch_frame.pack(padx=20, pady=(10, 0), fill="x")
        
        # Batch progress header
        self.lbl_batch_header = ctk.CTkLabel(
            self.batch_frame, 
            text="", 
            text_color="blue", 
            font=("Arial", 11, "bold")
        )
        self.lbl_batch_header.pack(anchor="w")
        
        # Current video being processed
        self.lbl_batch_status = ctk.CTkLabel(
            self.batch_frame, 
            text="", 
            text_color="gray", 
            font=("Arial", 9),
            wraplength=200
        )
        self.lbl_batch_status.pack(anchor="w", pady=(2, 0))
        
        # Progress bar
        self.batch_progress = ctk.CTkProgressBar(self.batch_frame)
        self.batch_progress.pack(fill="x", pady=(5, 0))
        
        # Completed/Successful/Failed counts
        self.lbl_batch_counts = ctk.CTkLabel(
            self.batch_frame,
            text="",
            text_color="green",
            font=("Arial", 9)
        )
        self.lbl_batch_counts.pack(anchor="w", pady=(3, 0))
        
        self.batch_frame.pack_forget()  # Hide initially
        
        # Analyze Button
        self.btn_analyze = ctk.CTkButton(self.sidebar, text="RUN AI ANALYSIS", command=self.start_analysis, 
                                       fg_color="green", height=50, font=("Arial", 14, "bold"), state="disabled")
        self.btn_analyze.pack(padx=20, pady=30, fill="x")
        
        # Batch processing variables
        self.batch_videos = []
        self.batch_processing = False
        
        # Progress
        self.progress = ctk.CTkProgressBar(self.sidebar)
        self.progress.pack(padx=20, fill="x")
        self.progress.set(0)
        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Ready")
        self.lbl_status.pack(pady=5)
        
        # --- Main Content (Results) ---
        self.main_panel = ctk.CTkFrame(self, corner_radius=0)
        self.main_panel.grid(row=0, column=1, sticky="nsew")
        
        self.assessment_form = AssessmentPanel(self.main_panel)
        self.assessment_form.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.btn_export = ctk.CTkButton(self.main_panel, text="Export PDF Report", command=self.generate_pdf, fg_color="#3B8ED0")
        self.btn_export.pack(pady=20, padx=20, side="bottom", anchor="e")
        
        # Load saved API key
        self.load_config()
        
        # Initial Load - set up first category and subcategory
        if categories:
            self.category_menu.set(categories[0])
            self.update_subcategory_menu()
            # Get the first rubric key from the selected category
            if categories[0] in self.rubrics_by_category:
                first_rubric_key, _ = self.rubrics_by_category[categories[0]][0]
                self.current_rubric_key = first_rubric_key
                # Get display name for the dropdown
                first_rubric = self.rubrics[first_rubric_key]
                display_name = first_rubric.get("subcategory", first_rubric.get("title", first_rubric_key))
                self.change_rubric(display_name)

    def update_subcategory_menu(self):
        """Update subcategory dropdown based on selected category."""
        selected_category = self.category_menu.get()
        if selected_category in self.rubrics_by_category:
            subcategories = []
            display_names = []
            for key, rubric in self.rubrics_by_category[selected_category]:
                subcategory = rubric.get("subcategory", key)
                # Create display name
                if subcategory:
                    display_name = subcategory
                else:
                    # Use title or key as fallback
                    display_name = rubric.get("title", key)
                subcategories.append(key)
                display_names.append(display_name)
            
            # Use display names for the dropdown, but store keys
            self.subcategory_menu.configure(values=display_names)
            if display_names:
                self.subcategory_menu.set(display_names[0])
                # Update current_rubric_key to match
                self.current_rubric_key = subcategories[0]
        else:
            self.subcategory_menu.configure(values=[])
    
    def change_category(self, category):
        """Handle category selection change."""
        self.update_subcategory_menu()
        if self.subcategory_menu.cget("values"):
            first_subcategory = self.subcategory_menu.cget("values")[0]
            self.change_rubric(first_subcategory)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv")])
        if path:
            self.selected_video_path = path
            self.lbl_file.configure(text=os.path.basename(path))
            self.btn_analyze.configure(state="normal")
            # Hide batch frame if visible
            self.batch_frame.pack_forget()
            self.batch_videos = []
    
    def select_batch_files(self):
        """Select multiple video files for batch processing."""
        paths = filedialog.askopenfilenames(
            title="Select Videos for Batch Processing",
            filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv")]
        )
        if paths:
            self.batch_videos = list(paths)
            self.lbl_file.configure(text=f"{len(self.batch_videos)} videos selected")
            # Show batch status frame
            self.batch_frame.pack(padx=20, pady=(10, 0), fill="x", before=self.btn_analyze)
            total = len(self.batch_videos)
            self.lbl_batch_header.configure(text=f"Batch: {total} video{'s' if total != 1 else ''}")
            self.lbl_batch_status.configure(text="Ready to start processing")
            self.lbl_batch_counts.configure(text=f"Completed: 0 / Total: {total} | Successful: 0 | Failed: 0")
            self.batch_progress.set(0)
            self.btn_analyze.configure(state="normal", text="START BATCH PROCESSING")
            self.selected_video_path = None  # Clear single file selection

    def load_config(self):
        """Load API key from config file."""
        config = ConfigManager.load_config()
        if "api_key" in config:
            self.entry_api_key.delete(0, "end")
            self.entry_api_key.insert(0, config["api_key"])
            # Auto-discover models and check availability after loading
            self.after(500, self.discover_models)
    
    def save_config(self):
        """Save API key to config file."""
        api_key = self.entry_api_key.get()
        if api_key:
            ConfigManager.save_config({"api_key": api_key})
    
    def on_api_key_change(self, event=None):
        """Called when API key is modified."""
        # Debounce: discover models after user stops typing
        if hasattr(self, '_discover_timer'):
            self.after_cancel(self._discover_timer)
        self._discover_timer = self.after(1000, self.discover_models)
        # Save config when API key changes
        self.save_config()
    
    def discover_models(self):
        """Discover available models from the API and update dropdown."""
        api_key = self.entry_api_key.get()
        
        if not api_key:
            # No API key, disable model selection
            self.model_menu.configure(values=["Enter API key first"], state="disabled")
            self.model_status_label.configure(text="●", text_color="gray")
            self.model_status_text.configure(text="No API key", text_color="gray")
            return
        
        # Show loading state
        self.model_menu.configure(values=["Discovering models..."], state="disabled")
        self.model_status_label.configure(text="●", text_color="yellow")
        self.model_status_text.configure(text="Discovering models...", text_color="yellow")
        
        # Run discovery in thread to avoid blocking UI
        thread = threading.Thread(target=self._discover_models_thread, args=(api_key,))
        thread.start()
    
    def _discover_models_thread(self, api_key):
        """Thread function to discover available models."""
        models, error_msg = GeminiClient.fetch_available_models(api_key)
        
        # Update UI on main thread
        self.after(0, lambda: self._update_model_list(models, error_msg))
    
    def _update_model_list(self, models, error_msg):
        """Update model dropdown with discovered models."""
        self.available_models = models
        
        if models:
            # Update dropdown with discovered models
            self.model_menu.configure(values=models, state="normal")
            
            # Set default model if current selection is invalid or not set
            # Prefer gemini-2.5-flash if available, otherwise use first model
            if not self.selected_model or self.selected_model not in models:
                if "gemini-2.5-flash" in models:
                    self.selected_model = "gemini-2.5-flash"
                else:
                    self.selected_model = models[0]
                self.model_menu.set(self.selected_model)
            elif self.selected_model in models:
                # Keep current selection if it's still valid
                self.model_menu.set(self.selected_model)
            
            # Check availability of selected model
            self.check_model_availability()
            
            if error_msg:
                print(f"[Model Discovery] Warning: {error_msg}")
        else:
            # Fallback: use default models
            fallback = ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
            self.model_menu.configure(values=fallback, state="normal")
            self.model_menu.set(fallback[0])
            self.selected_model = fallback[0]
            self.model_status_label.configure(text="●", text_color="orange")
            self.model_status_text.configure(
                text=f"Using fallback models ({error_msg or 'API unavailable'})",
                text_color="orange"
            )
    
    def check_model_availability(self):
        """Check if the selected model is available with current API key."""
        api_key = self.entry_api_key.get()
        if not api_key:
            self.model_status_label.configure(text="●", text_color="gray")
            self.model_status_text.configure(text="No API key", text_color="gray")
            return
        
        # Show checking status
        self.model_status_label.configure(text="●", text_color="yellow")
        self.model_status_text.configure(text="Checking...", text_color="yellow")
        
        # Run check in thread to avoid blocking UI
        thread = threading.Thread(target=self._check_model_thread, args=(api_key,))
        thread.start()
    
    def _check_model_thread(self, api_key):
        """Thread function to check model availability."""
        is_available, error_msg = GeminiClient.check_model_availability(api_key, self.selected_model)
        
        # Update UI on main thread
        if is_available:
            self.after(0, lambda: self._update_model_status(True, None))
        else:
            self.after(0, lambda: self._update_model_status(False, error_msg))
    
    def _update_model_status(self, is_available, error_msg):
        """Update model status indicator on main thread."""
        if is_available:
            self.model_status_label.configure(text="●", text_color="green")
            self.model_status_text.configure(
                text=f"{self.selected_model} ✓ Available",
                text_color="green"
            )
        else:
            self.model_status_label.configure(text="●", text_color="red")
            status_text = error_msg if error_msg else "Not available"
            self.model_status_text.configure(
                text=status_text[:50] + ("..." if len(status_text) > 50 else ""),
                text_color="red"
            )
    
    def change_model(self, choice):
        self.selected_model = choice
        # Check availability when model changes
        self.check_model_availability()

    def change_rubric(self, display_name):
        """Handle rubric selection change."""
        # Find the actual rubric key from display name
        selected_category = self.category_menu.get()
        rubric_key = None
        
        if selected_category in self.rubrics_by_category:
            for key, rubric in self.rubrics_by_category[selected_category]:
                subcategory = rubric.get("subcategory", key)
                rubric_title = rubric.get("title", key)
                if display_name == subcategory or display_name == rubric_title or display_name == key:
                    rubric_key = key
                    break
        
        if not rubric_key or rubric_key not in self.rubrics:
            return
        
        self.current_rubric_key = rubric_key
        rubric = self.rubrics[rubric_key]
        
        # Check if this is an auto-detect rubric
        if rubric.get("auto_detect", False):
            # Show a note that pattern will be auto-detected
            self.lbl_status.configure(text="Pattern will be auto-detected from video")
        else:
            self.lbl_status.configure(text="Ready")
        
        self.assessment_form.build_form(rubric)

    def start_analysis(self):
        api_key = self.entry_api_key.get()
        if not api_key:
            messagebox.showwarning("Missing Key", "Please enter a Gemini API Key.")
            return
        
        # Check if batch mode
        if self.batch_videos:
            self.start_batch_processing(api_key)
        else:
            if not self.selected_video_path:
                messagebox.showwarning("No Video", "Please select a video file first.")
                return
            
            self.btn_analyze.configure(state="disabled", fg_color="gray", text="RUN AI ANALYSIS")
            self.progress.set(0)
            
            # Run in thread to keep UI responsive
            thread = threading.Thread(target=self.run_ai_thread, args=(api_key,))
            thread.start()
    
    def start_batch_processing(self, api_key):
        """Start batch processing of multiple videos."""
        if not self.batch_videos:
            return
        
        self.batch_processing = True
        self.btn_analyze.configure(state="disabled", fg_color="gray", text="PROCESSING BATCH...")
        self.btn_file.configure(state="disabled")
        self.btn_batch.configure(state="disabled")
        self.batch_progress.set(0)
        
        # Run batch processing in thread
        thread = threading.Thread(target=self.run_batch_thread, args=(api_key,))
        thread.start()
    
    def run_batch_thread(self, api_key):
        """Process multiple videos in batch."""
        client = GeminiClient(api_key)
        rubric = self.rubrics[self.current_rubric_key]
        auto_detect = rubric.get("auto_detect", False)
        total_videos = len(self.batch_videos)
        successful = 0
        failed = []
        
        for idx, video_path in enumerate(self.batch_videos):
            video_name = os.path.basename(video_path)
            try:
                # Update batch status - starting video
                completed_before = idx
                self.after(0, lambda vn=video_name, i=idx, t=total_videos, c=completed_before: 
                    self.update_batch_status_starting(vn, i, t, c))
                
                # Process video
                def update_prog(msg, val, vn=video_name):
                    self.after(0, lambda m=msg: self.lbl_status.configure(text=m))
                    self.after(0, lambda v=val: self.progress.set(v))
                
                result = client.analyze_video(
                    video_path,
                    rubric,
                    update_prog,
                    self.selected_model,
                    auto_detect_pattern=auto_detect,
                    api_key=api_key
                )
                
                # Generate PDF automatically
                if "error" not in result:
                    pdf_path = self.generate_pdf_for_video(video_path, result)
                    if pdf_path:
                        successful += 1
                    else:
                        failed.append((video_name, "PDF generation failed - check file permissions"))
                else:
                    error_msg = result.get("error", "Analysis failed")
                    is_fatal = result.get("fatal", False)
                    # Extract just the error type for summary
                    if "FATAL ERROR" in error_msg:
                        error_summary = error_msg.split("\n\n")[0]  # Get first line
                    else:
                        error_summary = error_msg.split("\n")[0] if "\n" in error_msg else error_msg[:50]
                    failed.append((video_name, error_summary))
                
                # Update batch status - video completed
                completed_after = idx + 1
                self.after(0, lambda vn=video_name, c=completed_after, t=total_videos, s=successful, f=len(failed): 
                    self.update_batch_status_completed(vn, c, t, s, f))
                    
            except FileNotFoundError:
                failed.append((video_name, "Video file not found - may have been moved"))
                completed_after = idx + 1
                self.after(0, lambda c=completed_after, t=total_videos, s=successful, f=len(failed): 
                    self.update_batch_status_error(c, t, s, f))
            except PermissionError:
                failed.append((video_name, "Permission denied - check file access"))
                completed_after = idx + 1
                self.after(0, lambda c=completed_after, t=total_videos, s=successful, f=len(failed): 
                    self.update_batch_status_error(c, t, s, f))
            except Exception as e:
                error_msg = ErrorHandler.format_error(
                    "Unexpected Batch Processing Error",
                    f"An unexpected error occurred: {str(e)}",
                    is_fatal=False
                )
                # Extract summary for batch display
                error_summary = error_msg.split("\n")[0] if "\n" in error_msg else str(e)[:50]
                failed.append((video_name, error_summary))
                # Update counts after exception
                completed_after = idx + 1
                self.after(0, lambda c=completed_after, t=total_videos, s=successful, f=len(failed): 
                    self.update_batch_status_error(c, t, s, f))
        
        # Final status update
        self.after(0, lambda: self.finish_batch_processing(successful, failed, total_videos))
    
    def update_batch_status_starting(self, video_name, idx, total, completed):
        """Update batch status when starting a video."""
        display_name = video_name[:40] + "..." if len(video_name) > 40 else video_name
        self.lbl_batch_status.configure(text=f"Processing video {idx+1}/{total}: {display_name}")
        self.batch_progress.set(completed / total)
        self.lbl_batch_counts.configure(
            text=f"Completed: {completed} / Total: {total} | Processing..."
        )
    
    def update_batch_status_completed(self, video_name, completed, total, successful, failed):
        """Update batch status when a video completes."""
        display_name = video_name[:40] + "..." if len(video_name) > 40 else video_name
        self.lbl_batch_status.configure(text=f"Completed: {display_name}")
        self.batch_progress.set(completed / total)
        self.lbl_batch_counts.configure(
            text=f"Completed: {completed} / Total: {total} | Successful: {successful} | Failed: {failed}"
        )
    
    def update_batch_status_error(self, completed, total, successful, failed):
        """Update batch status after an error."""
        self.lbl_batch_status.configure(text="Error occurred, continuing...")
        self.batch_progress.set(completed / total)
        self.lbl_batch_counts.configure(
            text=f"Completed: {completed} / Total: {total} | Successful: {successful} | Failed: {failed}"
        )
    
    def finish_batch_processing(self, successful, failed, total):
        """Finish batch processing and show results."""
        self.batch_processing = False
        self.btn_analyze.configure(state="normal", fg_color="green", text="RUN AI ANALYSIS")
        self.btn_file.configure(state="normal")
        self.btn_batch.configure(state="normal")
        
        # Show completion message with actionable information
        message = f"Batch processing complete!\n\n✅ Successful: {successful}/{total}"
        if failed:
            message += f"\n\n❌ Failed ({len(failed)}):"
            for video_name, error in failed[:5]:  # Show first 5 failures
                # Truncate long video names
                display_name = video_name[:40] + "..." if len(video_name) > 40 else video_name
                message += f"\n  • {display_name}\n    Error: {error}"
            if len(failed) > 5:
                message += f"\n  ... and {len(failed) - 5} more failures"
            
            message += "\n\n💡 TIP: Failed videos can be processed individually. Check error messages for specific issues."
        
        if successful == total:
            messagebox.showinfo("✅ Batch Processing Complete", message)
        elif successful > 0:
            messagebox.showwarning("⚠️ Batch Processing Complete (Partial Success)", message)
        else:
            messagebox.showerror("❌ Batch Processing Failed", 
                message + "\n\nAll videos failed. Please check:\n" +
                "1. Your API key is valid\n" +
                "2. Video files are accessible\n" +
                "3. Internet connection is stable\n" +
                "4. Try processing one video individually to diagnose the issue")
        
        # Reset UI
        self.batch_videos = []
        self.batch_frame.pack_forget()
        self.lbl_file.configure(text="No file selected")
        self.btn_analyze.configure(state="disabled")
        self.lbl_status.configure(text="Ready")
        self.progress.set(0)
    
    def generate_pdf_for_video(self, video_path, assessment_result):
        """Generate PDF for a video without user interaction."""
        try:
            # Populate form with results
            self.assessment_form.populate_from_ai(assessment_result)
            
            # Get assessment data
            items, summary = self.assessment_form.get_data()
            
            # Generate filename automatically from video file
            video_dir = os.path.dirname(video_path)
            video_basename = os.path.basename(video_path)
            video_name_without_ext = os.path.splitext(video_basename)[0]
            
            # Generate PDF filename with auto-incrementing number if needed
            base_pdf_name = video_name_without_ext
            pdf_filename = os.path.join(video_dir, f"{base_pdf_name}.pdf")
            
            # Check if file exists and find next available number
            if os.path.exists(pdf_filename):
                import re
                match = re.search(r'_(\d+)$', base_pdf_name)
                if match:
                    existing_number = int(match.group(1))
                    base_name = base_pdf_name[:match.start()]
                    counter = existing_number + 1
                else:
                    base_name = base_pdf_name
                    counter = 1
                
                while os.path.exists(pdf_filename):
                    pdf_filename = os.path.join(video_dir, f"{base_name}_{counter}.pdf")
                    counter += 1
            
            # Generate PDF
            doc = SimpleDocTemplate(pdf_filename, pagesize=LETTER)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            elements.append(Paragraph(f"<b>{self.rubrics[self.current_rubric_key]['title']}</b>", styles['Title']))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            elements.append(Paragraph(f"File: {video_basename}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Table
            data = [["Criterion", "Score", "AI Assessment & Advice"]]
            for item in items:
                data.append([
                    Paragraph(item['Criterion'], styles['Normal']),
                    str(item['Score']),
                    Paragraph(item['Feedback'], styles['Normal'])
                ])
            
            t = Table(data, colWidths=[150, 50, 300])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))
            
            # Summative
            elements.append(Paragraph("<b>Holistic Summative Comment:</b>", styles['Heading2']))
            elements.append(Paragraph(summary, styles['Normal']))
            
            doc.build(elements)
            return pdf_filename
            
        except Exception as e:
            print(f"Error generating PDF for {video_path}: {e}")
            return None

    def run_ai_thread(self, api_key):
        client = GeminiClient(api_key)
        
        def update_prog(msg, val):
            self.lbl_status.configure(text=msg)
            self.progress.set(val)
        
        rubric = self.rubrics[self.current_rubric_key]
        # Check if auto-detection is needed
        auto_detect = rubric.get("auto_detect", False)
        result = client.analyze_video(
            self.selected_video_path, 
            rubric, 
            update_prog, 
            self.selected_model,
            auto_detect_pattern=auto_detect,
            api_key=api_key
        )
        
        # Update UI on main thread
        self.after(0, lambda: self.finish_analysis(result))

    def finish_analysis(self, result):
        if "error" in result:
            # Show user-friendly error message
            error_msg = result["error"]
            is_fatal = result.get("fatal", False)
            
            if is_fatal:
                messagebox.showerror("Fatal Error - Assessment Abandoned", error_msg)
                self.lbl_status.configure(text="Assessment Failed - See Error Message")
            else:
                # Non-fatal error - show warning but allow retry
                response = messagebox.askyesno(
                    "Analysis Error - Recoverable",
                    error_msg + "\n\nWould you like to try again?"
                )
                if not response:
                    self.lbl_status.configure(text="Analysis Failed - User Cancelled")
                else:
                    # User wants to retry - don't reset button state
                    return
            
            self.btn_analyze.configure(state="normal", fg_color="green")
        else:
            self.assessment_form.populate_from_ai(result)
            self.btn_analyze.configure(state="normal", fg_color="green")
            self.lbl_status.configure(text="Analysis Complete")

    def generate_pdf(self):
        items, summary = self.assessment_form.get_data()
        
        # Generate filename automatically from video file
        if not self.selected_video_path:
            messagebox.showwarning("No Video", "Please select a video file first.")
            return
        
        # Get video directory and base name
        video_dir = os.path.dirname(self.selected_video_path)
        video_basename = os.path.basename(self.selected_video_path)
        # Remove extension
        video_name_without_ext = os.path.splitext(video_basename)[0]
        
        # Start with the video name as the PDF name
        base_pdf_name = video_name_without_ext
        pdf_filename = os.path.join(video_dir, f"{base_pdf_name}.pdf")
        
        # If file exists, append/increment number
        if os.path.exists(pdf_filename):
            import re
            # Check if base name already ends with a number pattern
            match = re.search(r'_(\d+)$', base_pdf_name)
            if match:
                # Extract the existing number and base name
                existing_number = int(match.group(1))
                base_name = base_pdf_name[:match.start()]
                counter = existing_number + 1
            else:
                # No existing number, start from _1
                base_name = base_pdf_name
                counter = 1
            
            # Find next available filename
            pdf_filename = os.path.join(video_dir, f"{base_name}_{counter}.pdf")
            while os.path.exists(pdf_filename):
                counter += 1
                pdf_filename = os.path.join(video_dir, f"{base_name}_{counter}.pdf")
        
        filename = pdf_filename
        
        doc = SimpleDocTemplate(filename, pagesize=LETTER)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        elements.append(Paragraph(f"<b>{self.rubrics[self.current_rubric_key]['title']}</b>", styles['Title']))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        if self.selected_video_path:
            elements.append(Paragraph(f"File: {os.path.basename(self.selected_video_path)}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Table
        data = [["Criterion", "Score", "AI Assessment & Advice"]]
        for item in items:
            data.append([
                Paragraph(item['Criterion'], styles['Normal']),
                str(item['Score']),
                Paragraph(item['Feedback'], styles['Normal'])
            ])
        
        t = Table(data, colWidths=[150, 50, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # Summative
        elements.append(Paragraph("<b>Holistic Summative Comment:</b>", styles['Heading2']))
        elements.append(Paragraph(summary, styles['Normal']))
        
        try:
            doc.build(elements)
            messagebox.showinfo("Success", "PDF generated successfully.")
        except PermissionError as e:
            error_msg = ErrorHandler.format_error(
                "PDF Save Permission Denied",
                f"Cannot save PDF file: {str(e)}\n\nCheck that you have write permissions for the directory.",
                is_fatal=False
            )
            messagebox.showerror("PDF Generation Error", error_msg)
        except Exception as e:
            error_msg = ErrorHandler.format_error(
                "PDF Generation Error",
                f"An error occurred while generating the PDF: {str(e)}",
                is_fatal=False
            )
            messagebox.showerror("PDF Generation Error", error_msg)

if __name__ == "__main__":
    app = MedVATApp()
    app.mainloop()


