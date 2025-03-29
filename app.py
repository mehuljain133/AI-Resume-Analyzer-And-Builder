"""
Smart Resume AI - Main Application
"""
import streamlit as st

# Set page config at the very beginning
st.set_page_config(
    page_title="Smart Resume AI",
    page_icon="🚀",
    layout="wide"
)

import json
import pandas as pd
import plotly.express as px
import traceback
from utils.resume_analyzer import ResumeAnalyzer
from utils.resume_builder import ResumeBuilder
from config.database import (
    get_database_connection, save_resume_data, save_analysis_data, 
    init_database, verify_admin, log_admin_action
)
from config.job_roles import JOB_ROLES
from config.courses import COURSES_BY_CATEGORY, RESUME_VIDEOS, INTERVIEW_VIDEOS, get_courses_for_role, get_category_for_role
from dashboard.dashboard import DashboardManager
import requests
from streamlit_lottie import st_lottie
import plotly.graph_objects as go
import base64
import io
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from feedback.feedback import FeedbackManager
from ui_components import (
    apply_modern_styles, hero_section, feature_card, about_section, 
    page_header, render_analytics_section, render_activity_section, 
    render_suggestions_section
)
from datetime import datetime
from jobs.job_search import render_job_search
from PIL import Image

class ResumeApp:
    def __init__(self):
        """Initialize the application"""
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'personal_info': {
                    'full_name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': '',
                    'portfolio': ''
                },
                'summary': '',
                'experiences': [],
                'education': [],
                'projects': [],
                'skills_categories': {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': []
                }
            }
        
        # Initialize navigation state
        if 'page' not in st.session_state:
            st.session_state.page = 'home'
            
        # Initialize admin state
        if 'is_admin' not in st.session_state:
            st.session_state.is_admin = False
        
        self.pages = {
            "🏠 HOME": self.render_home,
            "🔍 RESUME ANALYZER": self.render_analyzer,
            "📝 RESUME BUILDER": self.render_builder,
            "📊 DASHBOARD": self.render_dashboard,
            "🎯 JOB SEARCH": self.render_job_search,
            "💬 FEEDBACK": self.render_feedback_page,
            "ℹ️ ABOUT": self.render_about
        }
        
        # Initialize dashboard manager
        self.dashboard_manager = DashboardManager()
        
        self.analyzer = ResumeAnalyzer()
        self.builder = ResumeBuilder()
        self.job_roles = JOB_ROLES
        
        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'
        if 'selected_role' not in st.session_state:
            st.session_state.selected_role = None
        
        # Initialize database
        init_database()
        
        # Load external CSS
        with open('style/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        
        # Load Google Fonts
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL"""
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    def apply_global_styles(self):
        st.markdown("""
        <style>
/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #222; /* Better contrast for dark mode */
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #4CAF50;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #45a049;
}

/* Global Styles */
.main-header {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    text-align: center;
    position: relative;
    overflow: hidden;
    will-change: transform, opacity;
}

.main-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%);
    z-index: 1;
}

.main-header h1 {
    color: white;
    font-size: 2.5rem;
    font-weight: 600;
    margin: 0;
    position: relative;
    z-index: 2;
}

/* Template Card Styles */
.template-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 2rem;
    padding: 1rem;
}

.template-card {
    background: rgba(45, 45, 45, 0.9);
    border-radius: 20px;
    padding: 2rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.1);
    transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.4s;
    will-change: transform, box-shadow;
}

.template-card:hover {
    transform: translate3d(0, -10px, 0);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    border-color: #4CAF50;
}

.template-icon {
    font-size: 3rem;
    color: #4CAF50;
    margin-bottom: 1.5rem;
    position: relative;
    z-index: 2;
}

.template-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: white;
    margin-bottom: 1rem;
    position: relative;
    z-index: 2;
}

.template-description {
    color: #aaa;
    margin-bottom: 1.5rem;
    position: relative;
    z-index: 2;
    line-height: 1.6;
}

/* Button Styles */
.action-button {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    color: white;
    padding: 1rem 2rem;
    border-radius: 50px;
    border: none;
    font-weight: 500;
    cursor: pointer;
    width: 100%;
    text-align: center;
    position: relative;
    overflow: hidden;
    z-index: 2;
    transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.4s;
    will-change: transform, box-shadow;
}

.action-button:hover {
    transform: translate3d(0, -2px, 0);
    box-shadow: 0 10px 20px rgba(76,175,80,0.3);
}

.action-button:focus-visible {
    outline: 3px solid rgba(76,175,80,0.6);
    outline-offset: 3px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .template-container {
        grid-template-columns: 1fr;
    }

    .main-header {
        padding: 1.5rem;
    }

    .main-header h1 {
        font-size: 2rem;
    }

    .template-card {
        padding: 1.5rem;
    }

    .action-button {
        padding: 0.8rem 1.6rem;
    }
}
</style>

        """, unsafe_allow_html=True)

    def load_image(self, image_name):
        """Load image from static directory"""
        try:
            image_path = f"c:/Users/shree/Downloads/smart-resume-ai/{image_name}"
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            encoded = base64.b64encode(image_bytes).decode()
            return f"data:image/png;base64,{encoded}"
        except Exception as e:
            print(f"Error loading image {image_name}: {e}")
            return None

    def export_to_excel(self):
        """Export resume data to Excel"""
        conn = get_database_connection()
        
        # Get resume data with analysis
        query = """
            SELECT 
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """
        
        try:
            # Read data into DataFrame
            df = pd.read_sql_query(query, conn)
            
            # Create Excel writer object
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Resume Data')
            
            return output.getvalue()
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
            return None
        finally:
            conn.close()

    def render_dashboard(self):
        """Render the dashboard page"""
        self.dashboard_manager.render_dashboard()

    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return f"""
            <div style='text-align: center; padding: 2rem; color: #666;'>
                <i class='{icon}' style='font-size: 2rem; margin-bottom: 1rem; color: #00bfa5;'></i>
                <p style='margin: 0;'>{message}</p>
            </div>
        """

    def analyze_resume(self, resume_text):
        """Analyze resume and store results"""
        analytics = self.analyzer.analyze_resume(resume_text)
        st.session_state.analytics_data = analytics
        return analytics

    def handle_resume_upload(self):
        """Handle resume upload and analysis"""
        uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'docx'])
        
        if uploaded_file is not None:
            try:
                # Extract text from resume
                if uploaded_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(uploaded_file)
                else:
                    resume_text = extract_text_from_docx(uploaded_file)
                
                # Store resume data
                st.session_state.resume_data = {
                    'filename': uploaded_file.name,
                    'content': resume_text,
                    'upload_time': datetime.now().isoformat()
                }
                
                # Analyze resume
                analytics = self.analyze_resume(resume_text)
                
                return True
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
                return False
        return False

    def render_builder(self):
        st.title("Resume Builder 📝")
        st.write("Create your professional resume")
        
        # Template selection
        template_options = ["Modern", "Professional", "Minimal", "Creative"]
        selected_template = st.selectbox("Select Resume Template", template_options)
        st.success(f"🎨 Currently using: {selected_template} Template")

        # Personal Information
        st.subheader("Personal Information")
        
        col1, col2 = st.columns(2)
        with col1:
            # Get existing values from session state
            existing_name = st.session_state.form_data['personal_info']['full_name']
            existing_email = st.session_state.form_data['personal_info']['email']
            existing_phone = st.session_state.form_data['personal_info']['phone']
            
            # Input fields with existing values
            full_name = st.text_input("Full Name", value=existing_name)
            email = st.text_input("Email", value=existing_email, key="email_input")
            phone = st.text_input("Phone", value=existing_phone)

            # Immediately update session state after email input
            if 'email_input' in st.session_state:
                st.session_state.form_data['personal_info']['email'] = st.session_state.email_input
        
        with col2:
            # Get existing values from session state
            existing_location = st.session_state.form_data['personal_info']['location']
            existing_linkedin = st.session_state.form_data['personal_info']['linkedin']
            existing_portfolio = st.session_state.form_data['personal_info']['portfolio']
            
            # Input fields with existing values
            location = st.text_input("Location", value=existing_location)
            linkedin = st.text_input("LinkedIn URL", value=existing_linkedin)
            portfolio = st.text_input("Portfolio Website", value=existing_portfolio)

        # Update personal info in session state
        st.session_state.form_data['personal_info'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'location': location,
            'linkedin': linkedin,
            'portfolio': portfolio
        }

        # Professional Summary
        st.subheader("Professional Summary")
        summary = st.text_area("Professional Summary", value=st.session_state.form_data.get('summary', ''), height=150,
                             help="Write a brief summary highlighting your key skills and experience")
        
        # Experience Section
        st.subheader("Work Experience")
        if 'experiences' not in st.session_state.form_data:
            st.session_state.form_data['experiences'] = []
            
        if st.button("Add Experience"):
            st.session_state.form_data['experiences'].append({
                'company': '',
                'position': '',
                'start_date': '',
                'end_date': '',
                'description': '',
                'responsibilities': [],
                'achievements': []
            })
        
        for idx, exp in enumerate(st.session_state.form_data['experiences']):
            with st.expander(f"Experience {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    exp['company'] = st.text_input("Company Name", key=f"company_{idx}", value=exp.get('company', ''))
                    exp['position'] = st.text_input("Position", key=f"position_{idx}", value=exp.get('position', ''))
                with col2:
                    exp['start_date'] = st.text_input("Start Date", key=f"start_date_{idx}", value=exp.get('start_date', ''))
                    exp['end_date'] = st.text_input("End Date", key=f"end_date_{idx}", value=exp.get('end_date', ''))
                
                exp['description'] = st.text_area("Role Overview", key=f"desc_{idx}", 
                                                value=exp.get('description', ''),
                                                help="Brief overview of your role and impact")
                
                # Responsibilities
                st.markdown("##### Key Responsibilities")
                resp_text = st.text_area("Enter responsibilities (one per line)", 
                                       key=f"resp_{idx}",
                                       value='\n'.join(exp.get('responsibilities', [])),
                                       height=100,
                                       help="List your main responsibilities, one per line")
                exp['responsibilities'] = [r.strip() for r in resp_text.split('\n') if r.strip()]
                
                # Achievements
                st.markdown("##### Key Achievements")
                achv_text = st.text_area("Enter achievements (one per line)", 
                                       key=f"achv_{idx}",
                                       value='\n'.join(exp.get('achievements', [])),
                                       height=100,
                                       help="List your notable achievements, one per line")
                exp['achievements'] = [a.strip() for a in achv_text.split('\n') if a.strip()]
                
                if st.button("Remove Experience", key=f"remove_exp_{idx}"):
                    st.session_state.form_data['experiences'].pop(idx)
                    st.rerun()
        
        # Projects Section
        st.subheader("Projects")
        if 'projects' not in st.session_state.form_data:
            st.session_state.form_data['projects'] = []
            
        if st.button("Add Project"):
            st.session_state.form_data['projects'].append({
                'name': '',
                'technologies': '',
                'description': '',
                'responsibilities': [],
                'achievements': [],
                'link': ''
            })
        
        for idx, proj in enumerate(st.session_state.form_data['projects']):
            with st.expander(f"Project {idx + 1}", expanded=True):
                proj['name'] = st.text_input("Project Name", key=f"proj_name_{idx}", value=proj.get('name', ''))
                proj['technologies'] = st.text_input("Technologies Used", key=f"proj_tech_{idx}", 
                                                   value=proj.get('technologies', ''),
                                                   help="List the main technologies, frameworks, and tools used")
                
                proj['description'] = st.text_area("Project Overview", key=f"proj_desc_{idx}", 
                                                 value=proj.get('description', ''),
                                                 help="Brief overview of the project and its goals")
                
                # Project Responsibilities
                st.markdown("##### Key Responsibilities")
                proj_resp_text = st.text_area("Enter responsibilities (one per line)", 
                                            key=f"proj_resp_{idx}",
                                            value='\n'.join(proj.get('responsibilities', [])),
                                            height=100,
                                            help="List your main responsibilities in the project")
                proj['responsibilities'] = [r.strip() for r in proj_resp_text.split('\n') if r.strip()]
                
                # Project Achievements
                st.markdown("##### Key Achievements")
                proj_achv_text = st.text_area("Enter achievements (one per line)", 
                                            key=f"proj_achv_{idx}",
                                            value='\n'.join(proj.get('achievements', [])),
                                            height=100,
                                            help="List the project's key achievements and your contributions")
                proj['achievements'] = [a.strip() for a in proj_achv_text.split('\n') if a.strip()]
                
                proj['link'] = st.text_input("Project Link (optional)", key=f"proj_link_{idx}", 
                                           value=proj.get('link', ''),
                                           help="Link to the project repository, demo, or documentation")
                
                if st.button("Remove Project", key=f"remove_proj_{idx}"):
                    st.session_state.form_data['projects'].pop(idx)
                    st.rerun()
        
        # Education Section
        st.subheader("Education")
        if 'education' not in st.session_state.form_data:
            st.session_state.form_data['education'] = []
            
        if st.button("Add Education"):
            st.session_state.form_data['education'].append({
                'school': '',
                'degree': '',
                'field': '',
                'graduation_date': '',
                'gpa': '',
                'achievements': []
            })
        
        for idx, edu in enumerate(st.session_state.form_data['education']):
            with st.expander(f"Education {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    edu['school'] = st.text_input("School/University", key=f"school_{idx}", value=edu.get('school', ''))
                    edu['degree'] = st.text_input("Degree", key=f"degree_{idx}", value=edu.get('degree', ''))
                with col2:
                    edu['field'] = st.text_input("Field of Study", key=f"field_{idx}", value=edu.get('field', ''))
                    edu['graduation_date'] = st.text_input("Graduation Date", key=f"grad_date_{idx}", 
                                                         value=edu.get('graduation_date', ''))
                
                edu['gpa'] = st.text_input("GPA (optional)", key=f"gpa_{idx}", value=edu.get('gpa', ''))
                
                # Educational Achievements
                st.markdown("##### Achievements & Activities")
                edu_achv_text = st.text_area("Enter achievements (one per line)", 
                                           key=f"edu_achv_{idx}",
                                           value='\n'.join(edu.get('achievements', [])),
                                           height=100,
                                           help="List academic achievements, relevant coursework, or activities")
                edu['achievements'] = [a.strip() for a in edu_achv_text.split('\n') if a.strip()]
                
                if st.button("Remove Education", key=f"remove_edu_{idx}"):
                    st.session_state.form_data['education'].pop(idx)
                    st.rerun()
        
        # Skills Section
        st.subheader("Skills")
        if 'skills_categories' not in st.session_state.form_data:
            st.session_state.form_data['skills_categories'] = {
                'technical': [],
                'soft': [],
                'languages': [],
                'tools': []
            }
        
        col1, col2 = st.columns(2)
        with col1:
            tech_skills = st.text_area("Technical Skills (one per line)", 
                                     value='\n'.join(st.session_state.form_data['skills_categories']['technical']),
                                     height=150,
                                     help="Programming languages, frameworks, databases, etc.")
            st.session_state.form_data['skills_categories']['technical'] = [s.strip() for s in tech_skills.split('\n') if s.strip()]
            
            soft_skills = st.text_area("Soft Skills (one per line)", 
                                     value='\n'.join(st.session_state.form_data['skills_categories']['soft']),
                                     height=150,
                                     help="Leadership, communication, problem-solving, etc.")
            st.session_state.form_data['skills_categories']['soft'] = [s.strip() for s in soft_skills.split('\n') if s.strip()]
        
        with col2:
            languages = st.text_area("Languages (one per line)", 
                                   value='\n'.join(st.session_state.form_data['skills_categories']['languages']),
                                   height=150,
                                   help="Programming or human languages with proficiency level")
            st.session_state.form_data['skills_categories']['languages'] = [l.strip() for l in languages.split('\n') if l.strip()]
            
            tools = st.text_area("Tools & Technologies (one per line)", 
                               value='\n'.join(st.session_state.form_data['skills_categories']['tools']),
                               height=150,
                               help="Development tools, software, platforms, etc.")
            st.session_state.form_data['skills_categories']['tools'] = [t.strip() for t in tools.split('\n') if t.strip()]
        
        # Update form data in session state
        st.session_state.form_data.update({
            'summary': summary
        })
        
        # Generate Resume button
        if st.button("Generate Resume 📄", type="primary"):
            print("Validating form data...")
            print(f"Session state form data: {st.session_state.form_data}")
            print(f"Email input value: {st.session_state.get('email_input', '')}")
            
            # Get the current values from form
            current_name = st.session_state.form_data['personal_info']['full_name'].strip()
            current_email = st.session_state.email_input if 'email_input' in st.session_state else ''
            
            print(f"Current name: {current_name}")
            print(f"Current email: {current_email}")
            
            # Validate required fields
            if not current_name:
                st.error("⚠️ Please enter your full name.")
                return
            
            if not current_email:
                st.error("⚠️ Please enter your email address.")
                return
                
            # Update email in form data one final time
            st.session_state.form_data['personal_info']['email'] = current_email
            
            try:
                print("Preparing resume data...")
                # Prepare resume data with current form values
                resume_data = {
                    "personal_info": st.session_state.form_data['personal_info'],
                    "summary": st.session_state.form_data.get('summary', '').strip(),
                    "experience": st.session_state.form_data.get('experiences', []),
                    "education": st.session_state.form_data.get('education', []),
                    "projects": st.session_state.form_data.get('projects', []),
                    "skills": st.session_state.form_data.get('skills_categories', {
                        'technical': [],
                        'soft': [],
                        'languages': [],
                        'tools': []
                    }),
                    "template": selected_template
                }
                
                print(f"Resume data prepared: {resume_data}")
                
                try:
                    # Generate resume
                    resume_buffer = self.builder.generate_resume(resume_data)
                    if resume_buffer:
                        try:
                            # Save resume data to database
                            save_resume_data(resume_data)
                            
                            # Offer the resume for download
                            st.success("✅ Resume generated successfully!")
                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        except Exception as db_error:
                            print(f"Warning: Failed to save to database: {str(db_error)}")
                            # Still allow download even if database save fails
                            st.warning("⚠️ Resume generated but couldn't be saved to database")
                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    else:
                        st.error("❌ Failed to generate resume. Please try again.")
                        print("Resume buffer was None")
                except Exception as gen_error:
                    print(f"Error during resume generation: {str(gen_error)}")
                    print(f"Full traceback: {traceback.format_exc()}")
                    st.error(f"❌ Error generating resume: {str(gen_error)}")
                        
            except Exception as e:
                print(f"Error preparing resume data: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"❌ Error preparing resume data: {str(e)}")
    
    def render_about(self):
        """Render the about page"""
        # Apply modern styles
        from ui_components import apply_modern_styles
        import base64
        import os
        
        # Function to load image as base64
        def get_image_as_base64(file_path):
            try:
                with open(file_path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode()
                    return f"data:image/jpeg;base64,{encoded}"
            except:
                return None
        
        # Get image path and convert to base64
        image_path = os.path.join(os.path.dirname(__file__), "assets", "124852522.jpeg")
        image_base64 = get_image_as_base64(image_path)
        
        apply_modern_styles()
        
        # Add Font Awesome icons and custom CSS
        st.markdown("""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
/* Section Styling */
.profile-section, .vision-section, .feature-card {
    text-align: center;
    padding: 2rem;
    background: rgba(45, 45, 45, 0.9);
    border-radius: 20px;
    margin: 2rem auto;
    max-width: 800px;
    backdrop-filter: blur(10px);
}

/* Profile Image */
.profile-image {
    width: 200px;
    height: 200px;
    border-radius: 50%;
    margin: 0 auto 1.5rem;
    display: block;
    object-fit: cover;
    border: 4px solid #4CAF50;
}

/* Profile Name & Title */
.profile-name {
    font-size: 2.5rem;
    color: white;
    margin-bottom: 0.5rem;
}

.profile-title {
    font-size: 1.2rem;
    color: #4CAF50;
    margin-bottom: 1.5rem;
}

/* Social Media Links */
.social-links {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin: 2rem 0;
}

.social-link {
    font-size: 2rem;
    color: #4CAF50;
    transition: transform 0.3s ease, background 0.3s ease, box-shadow 0.3s ease;
    padding: 0.5rem;
    border-radius: 50%;
    background: rgba(76, 175, 80, 0.1);
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    will-change: transform, box-shadow;
}

.social-link:hover, .social-link:focus-visible {
    transform: translate3d(0, -5px, 0);
    background: #4CAF50;
    color: white;
    box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
    outline: none;
}

/* Bio & Vision Text */
.bio-text, .vision-text {
    color: #ddd;
    line-height: 1.8;
    font-size: 1.1rem;
    margin-top: 2rem;
    text-align: left;
}

.vision-text {
    font-style: italic;
    margin: 1.5rem 0;
}

/* Icons & Titles */
.vision-icon, .feature-icon {
    font-size: 2.5rem;
    color: #4CAF50;
    margin-bottom: 1rem;
}

.vision-title, .feature-title {
    font-size: 2rem;
    color: white;
    margin-bottom: 1rem;
}

/* Feature Section */
.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin: 2rem auto;
    max-width: 1200px;
}

.feature-card {
    padding: 2rem;
    margin: 0;
}

.feature-description {
    color: #ddd;
    line-height: 1.6;
}

/* Responsive Design */
@media (max-width: 768px) {
    .profile-section, .vision-section {
        max-width: 90%;
    }

    .profile-name {
        font-size: 2rem;
    }

    .profile-image {
        width: 150px;
        height: 150px;
    }

    .features-grid {
        grid-template-columns: 1fr;
    }
}
</style>
        """, unsafe_allow_html=True)
        
        # Hero Section
        st.markdown("""
            <div class="hero-section">
                <h1 class="hero-title">About Smart Resume AI</h1>
                <p class="hero-subtitle">A powerful AI-driven platform for optimizing your resume</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Profile Section
        st.markdown(f"""
            <div class="profile-section">
                <img src="{image_base64 if image_base64 else 'https://avatars.githubusercontent.com/Hunterdii'}" 
                     alt="Mehul Jain" 
                     class="profile-image"
                     onerror="this.onerror=null; this.src='https://avatars.githubusercontent.com/Hunterdii';">
                <h2 class="profile-name">Mehul Jain</h2>
                <p class="profile-title">AI/ML Enthusiast</p>
                            </div>
        """, unsafe_allow_html=True)
        
        # Vision Section
        st.markdown("""
            <div class="vision-section">
                <i class="fas fa-lightbulb vision-icon"></i>
                <h2 class="vision-title">Our Vision</h2>
                <p class="vision-text">
                    "Smart Resume AI represents my vision of democratizing career advancement through technology. 
                    By combining cutting-edge AI with intuitive design, this platform empowers job seekers at 
                    every career stage to showcase their true potential and stand out in today's competitive job market."
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Features Section
        st.markdown("""
            <div class="features-grid">
                <div class="feature-card">
                    <i class="fas fa-robot feature-icon"></i>
                    <h3 class="feature-title">AI-Powered Analysis</h3>
                    <p class="feature-description">
                        Advanced AI algorithms provide detailed insights and suggestions to optimize your resume for maximum impact.
                    </p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-chart-line feature-icon"></i>
                    <h3 class="feature-title">Data-Driven Insights</h3>
                    <p class="feature-description">
                        Make informed decisions with our analytics-based recommendations and industry insights.
                    </p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-shield-alt feature-icon"></i>
                    <h3 class="feature-title">Privacy First</h3>
                    <p class="feature-description">
                        Your data security is our priority. We ensure your information is always protected and private.
                    </p>
                </div>
            </div>
            <div style="text-align: center; margin: 3rem 0;">
                <a href="?page=analyzer" class="cta-button">
                    Start Your Journey
                    <i class="fas fa-arrow-right" style="margin-left: 10px;"></i>
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    def render_analyzer(self):
        """Render the resume analyzer page"""
        apply_modern_styles()
        
        # Page Header
        page_header(
            "Resume Analyzer",
            "Get instant AI-powered feedback to optimize your resume"
        )
        
        # Job Role Selection
        categories = list(self.job_roles.keys())
        selected_category = st.selectbox("Job Category", categories)
        
        roles = list(self.job_roles[selected_category].keys())
        selected_role = st.selectbox("Specific Role", roles)
        
        role_info = self.job_roles[selected_category][selected_role]
        
        # Display role information
        st.markdown(f"""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
            <h3>{selected_role}</h3>
            <p>{role_info['description']}</p>
            <h4>Required Skills:</h4>
            <p>{', '.join(role_info['required_skills'])}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # File Upload
        uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'docx'])
        
        st.markdown(
            self.render_empty_state(
            "fas fa-cloud-upload-alt",
            "Upload your resume to get started with AI-powered analysis"
            ),
            unsafe_allow_html=True
        )
        if uploaded_file:
            with st.spinner("Analyzing your document..."):
                # Get file content
                text = ""
                try:
                    if uploaded_file.type == "application/pdf":
                        text = self.analyzer.extract_text_from_pdf(uploaded_file)
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        text = self.analyzer.extract_text_from_docx(uploaded_file)
                    else:
                        text = uploaded_file.getvalue().decode()
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    return

                
                # Analyze the document
                analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
                
                # Save resume data to database
                resume_data = {
                    'personal_info': {
                        'name': analysis.get('name', ''),
                        'email': analysis.get('email', ''),
                        'phone': analysis.get('phone', ''),
                        'linkedin': analysis.get('linkedin', ''),
                        'github': analysis.get('github', ''),
                        'portfolio': analysis.get('portfolio', '')
                    },
                    'summary': analysis.get('summary', ''),
                    'target_role': selected_role,
                    'target_category': selected_category,
                    'education': analysis.get('education', []),
                    'experience': analysis.get('experience', []),
                    'projects': analysis.get('projects', []),
                    'skills': analysis.get('skills', []),
                    'template': ''
                }
                
                # Save to database
                try:
                    resume_id = save_resume_data(resume_data)
                    
                    # Save analysis data
                    analysis_data = {
                        'resume_id': resume_id,
                        'ats_score': analysis['ats_score'],
                        'keyword_match_score': analysis['keyword_match']['score'],
                        'format_score': analysis['format_score'],
                        'section_score': analysis['section_score'],
                        'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                        'recommendations': ','.join(analysis['suggestions'])
                    }
                    save_analysis_data(resume_id, analysis_data)
                    st.success("Resume data saved successfully!")
                except Exception as e:
                    st.error(f"Error saving to database: {str(e)}")
                    print(f"Database error: {e}")
                
                # Show results based on document type
                if analysis.get('document_type') != 'resume':
                    st.error(f"⚠️ This appears to be a {analysis['document_type']} document, not a resume!")
                    st.warning("Please upload a proper resume for ATS analysis.")
                    return                
                # Display results in a modern card layout
                col1, col2 = st.columns(2)
                
                with col1:
                    # ATS Score Card with circular progress
                    st.markdown("""
                    <div class="feature-card">
                        <h2>ATS Score</h2>
                        <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                            <div style="
                                position: absolute;
                                width: 150px;
                                height: 150px;
                                border-radius: 50%;
                                background: conic-gradient(
                                    #4CAF50 0% {score}%,
                                    #2c2c2c {score}% 100%
                                );
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            ">
                                <div style="
                                    width: 120px;
                                    height: 120px;
                                    background: #1a1a1a;
                                    border-radius: 50%;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-size: 24px;
                                    font-weight: bold;
                                    color: {color};
                                ">
                                    {score}
                                </div>
                            </div>
                        </div>
                        <div style="text-align: center; margin-top: 10px;">
                            <span style="
                                font-size: 1.2em;
                                color: {color};
                                font-weight: bold;
                            ">
                                {status}
                            </span>
                        </div>
                    """.format(
                        score=analysis['ats_score'],
                        color='#4CAF50' if analysis['ats_score'] >= 80 else '#FFA500' if analysis['ats_score'] >= 60 else '#FF4444',
                        status='Excellent' if analysis['ats_score'] >= 80 else 'Good' if analysis['ats_score'] >= 60 else 'Needs Improvement'
                    ), unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                                        
                    # self.display_analysis_results(analysis_results)

                    # Skills Match Card
                    st.markdown("""
                    <div class="feature-card">
                        <h2>Skills Match</h2>
                    """, unsafe_allow_html=True)
                    
                    st.metric("Keyword Match", f"{int(analysis.get('keyword_match', {}).get('score', 0))}%")
                    
                    if analysis['keyword_match']['missing_skills']:
                        st.markdown("#### Missing Skills:")
                        for skill in analysis['keyword_match']['missing_skills']:
                            st.markdown(f"- {skill}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    # Format Score Card
                    st.markdown("""
                    <div class="feature-card">
                        <h2>Format Analysis</h2>
                    """, unsafe_allow_html=True)
                    
                    st.metric("Format Score", f"{int(analysis.get('format_score', 0))}%")
                    st.metric("Section Score", f"{int(analysis.get('section_score', 0))}%")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Suggestions Card with improved UI
                    st.markdown("""
                    <div class="feature-card">
                        <h2>📋 Resume Improvement Suggestions</h2>
                    """, unsafe_allow_html=True)
                    
                    # Contact Section
                    if analysis.get('contact_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📞 Contact Information</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('contact_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Summary Section
                    if analysis.get('summary_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📝 Professional Summary</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('summary_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Skills Section
                    if analysis.get('skills_suggestions') or analysis['keyword_match']['missing_skills']:
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎯 Skills</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('skills_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        if analysis['keyword_match']['missing_skills']:
                            st.markdown("<li style='margin-bottom: 8px;'>✓ Consider adding these relevant skills:</li>", unsafe_allow_html=True)
                            for skill in analysis['keyword_match']['missing_skills']:
                                st.markdown(f"<li style='margin-left: 20px; margin-bottom: 4px;'>• {skill}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Experience Section
                    if analysis.get('experience_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>💼 Work Experience</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('experience_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Education Section
                    if analysis.get('education_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎓 Education</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('education_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # General Formatting Suggestions
                    if analysis.get('format_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📄 Formatting</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('format_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                

                
                # Course Recommendations
                st.markdown("""
                <div class="feature-card">
                    <h2>📚 Recommended Courses</h2>
                """, unsafe_allow_html=True)
                
                # Get courses based on role and category
                courses = get_courses_for_role(selected_role)
                if not courses:
                    category = get_category_for_role(selected_role)
                    courses = COURSES_BY_CATEGORY.get(category, {}).get(selected_role, [])
                
                # Display courses in a grid
                cols = st.columns(2)
                for i, course in enumerate(courses[:6]):  # Show top 6 courses
                    with cols[i % 2]:
                        st.markdown(f"""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h4>{course[0]}</h4>
                            <a href='{course[1]}' target='_blank'>View Course</a>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Learning Resources
                st.markdown("""
                <div class="feature-card">
                    <h2>📺 Helpful Videos</h2>
                """, unsafe_allow_html=True)
                
                tab1, tab2 = st.tabs(["Resume Tips", "Interview Tips"])
                
                with tab1:
                    # Resume Videos
                    for category, videos in RESUME_VIDEOS.items():
                        st.subheader(category)
                        cols = st.columns(2)
                        for i, video in enumerate(videos):
                            with cols[i % 2]:
                                st.video(video[1])
                
                with tab2:
                    # Interview Videos
                    for category, videos in INTERVIEW_VIDEOS.items():
                        st.subheader(category)
                        cols = st.columns(2)
                        for i, video in enumerate(videos):
                            with cols[i % 2]:
                                st.video(video[1])
                
                st.markdown("</div>", unsafe_allow_html=True)
                
        # Close the page container
        st.markdown('</div>', unsafe_allow_html=True)

    def render_job_search(self):
        """Render the job search page"""
        render_job_search()

    def render_feedback_page(self):
        """Render the feedback page"""
        st.markdown("""
            <style>
            .feedback-header {
                text-align: center;
                padding: 20px;
                background: linear-gradient(90deg, rgba(76, 175, 80, 0.1), rgba(33, 150, 243, 0.1));
                border-radius: 10px;
                margin-bottom: 30px;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="feedback-header">
                <h1>📣 Your Voice Matters!</h1>
                <p>Help us improve Smart Resume AI with your valuable feedback</p>
            </div>
        """, unsafe_allow_html=True)

        # Initialize feedback manager
        feedback_manager = FeedbackManager()
        
        # Create tabs for form and statistics
        form_tab, stats_tab = st.tabs(["Share Feedback", "Feedback Overview"])
        
        with form_tab:
            feedback_manager.render_feedback_form()
            
        with stats_tab:
            feedback_manager.render_feedback_stats()

    def render_home(self):
        apply_modern_styles()
        
        # Hero Section
        hero_section(
            "Smart Resume AI",
            "Transform your career with AI-powered resume analysis and building. Get personalized insights and create professional resumes that stand out."
        )
        
        # Features Section
        st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
        
        feature_card(
            "fas fa-robot",
            "AI-Powered Analysis",
            "Get instant feedback on your resume with advanced AI analysis that identifies strengths and areas for improvement."
        )
        
        feature_card(
            "fas fa-magic",
            "Smart Resume Builder",
            "Create professional resumes with our intelligent builder that suggests optimal content and formatting."
        )
        
        feature_card(
            "fas fa-chart-line",
            "Career Insights",
            "Access detailed analytics and personalized recommendations to enhance your career prospects."
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Call-to-Action with Streamlit navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Get Started", key="get_started_btn", 
                        help="Click to start analyzing your resume",
                        type="primary",
                        use_container_width=True):
                cleaned_name = "🔍 RESUME ANALYZER".lower().replace(" ", "_").replace("🔍", "").strip()
                st.session_state.page = cleaned_name
                st.rerun()

    def main(self):
        """Main application entry point"""
        self.apply_global_styles()
        
        # Admin login/logout in sidebar
        with st.sidebar:
            st_lottie(self.load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_xyadoh9h.json"), height=200, key="sidebar_animation")
            st.title("Smart Resume AI")
            st.markdown("---")
            
            # Navigation buttons
            for page_name in self.pages.keys():
                if st.button(page_name, use_container_width=True):
                    cleaned_name = page_name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip()
                    st.session_state.page = cleaned_name
                    st.rerun()

            # Add some space before admin login
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Admin Login/Logout section at bottom
            if st.session_state.get('is_admin', False):
                st.success(f"Logged in as: {st.session_state.get('current_admin_email')}")
                if st.button("Logout", key="logout_button"):
                    try:
                        log_admin_action(st.session_state.get('current_admin_email'), "logout")
                        st.session_state.is_admin = False
                        st.session_state.current_admin_email = None
                        st.success("Logged out successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during logout: {str(e)}")
            else:
                with st.expander("👤 Admin Login"):
                    admin_email_input = st.text_input("Email", key="admin_email_input")
                    admin_password = st.text_input("Password", type="password", key="admin_password_input")
                    if st.button("Login", key="login_button"):
                            try:
                                if verify_admin(admin_email_input, admin_password):
                                    st.session_state.is_admin = True
                                    st.session_state.current_admin_email = admin_email_input
                                    log_admin_action(admin_email_input, "login")
                                    st.success("Logged in successfully!")
                                    st.rerun()
                                else:
                                    st.error("Invalid credentials")
                            except Exception as e:
                                st.error(f"Error during login: {str(e)}")
        
        # Force home page on first load
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'home'
            st.rerun()
        
        # Get current page and render it
        current_page = st.session_state.get('page', 'home')
        
        # Create a mapping of cleaned page names to original names
        page_mapping = {name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip(): name 
                       for name in self.pages.keys()}
        
        # Render the appropriate page
        if current_page in page_mapping:
            self.pages[page_mapping[current_page]]()
        else:
            # Default to home page if invalid page
            self.render_home()
    
if __name__ == "__main__":
    app = ResumeApp()
    app.main()


# import time
# import numpy as np
# import pandas as pd
# import streamlit as st
# from streamlit_option_menu import option_menu
# from streamlit_extras.add_vertical_space import add_vertical_space
# from PyPDF2 import PdfReader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.vectorstores import FAISS
# from langchain.chat_models import ChatOpenAI
# from langchain.chains.question_answering import load_qa_chain
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.common.exceptions import NoSuchElementException
# import warnings
# warnings.filterwarnings('ignore')


# def streamlit_config():

#     # page configuration
#     st.set_page_config(page_title='Resume Analyzer AI', layout="wide")

#     # page header transparent color
#     page_background_color = """
#     <style>

#     [data-testid="stHeader"] 
#     {
#     background: rgba(0,0,0,0);
#     }

#     </style>
#     """
#     st.markdown(page_background_color, unsafe_allow_html=True)

#     # title and position
#     st.markdown(f'<h1 style="text-align: center;">Resume Analyzer AI</h1>',
#                 unsafe_allow_html=True)


# class resume_analyzer:

#     def pdf_to_chunks(pdf):
#         # read pdf and it returns memory address
#         pdf_reader = PdfReader(pdf)

#         # extrat text from each page separately
#         text = ""
#         for page in pdf_reader.pages:
#             text += page.extract_text()

#         # Split the long text into small chunks.
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=700,
#             chunk_overlap=200,
#             length_function=len)

#         chunks = text_splitter.split_text(text=text)
#         return chunks


#     def openai(openai_api_key, chunks, analyze):

#         # Using OpenAI service for embedding
#         embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

#         # Facebook AI Similarity Serach library help us to convert text data to numerical vector
#         vectorstores = FAISS.from_texts(chunks, embedding=embeddings)

#         # compares the query and chunks, enabling the selection of the top 'K' most similar chunks based on their similarity scores.
#         docs = vectorstores.similarity_search(query=analyze, k=3)

#         # creates an OpenAI object, using the ChatGPT 3.5 Turbo model
#         llm = ChatOpenAI(model='gpt-3.5-turbo', api_key=openai_api_key)

#         # question-answering (QA) pipeline, making use of the load_qa_chain function
#         chain = load_qa_chain(llm=llm, chain_type='stuff')

#         response = chain.run(input_documents=docs, question=analyze)
#         return response


#     def summary_prompt(query_with_chunks):

#         query = f''' need to detailed summarization of below resume and finally conclude them

#                     """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#                     {query_with_chunks}
#                     """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#                     '''
#         return query


#     def resume_summary():

#         with st.form(key='Summary'):

#             # User Upload the Resume
#             add_vertical_space(1)
#             pdf = st.file_uploader(label='Upload Your Resume', type='pdf')
#             add_vertical_space(1)

#             # Enter OpenAI API Key
#             col1,col2 = st.columns([0.6,0.4])
#             with col1:
#                 openai_api_key = st.text_input(label='Enter OpenAI API Key', type='password')
#             add_vertical_space(2)

#             # Click on Submit Button
#             submit = st.form_submit_button(label='Submit')
#             add_vertical_space(1)
        
#         add_vertical_space(3)
#         if submit:
#             if pdf is not None and openai_api_key != '':
#                 try:
#                     with st.spinner('Processing...'):

#                         pdf_chunks = resume_analyzer.pdf_to_chunks(pdf)

#                         summary_prompt = resume_analyzer.summary_prompt(query_with_chunks=pdf_chunks)

#                         summary = resume_analyzer.openai(openai_api_key=openai_api_key, chunks=pdf_chunks, analyze=summary_prompt)

#                     st.markdown(f'<h4 style="color: orange;">Summary:</h4>', unsafe_allow_html=True)
#                     st.write(summary)

#                 except Exception as e:
#                     st.markdown(f'<h5 style="text-align: center;color: orange;">{e}</h5>', unsafe_allow_html=True)

#             elif pdf is None:
#                 st.markdown(f'<h5 style="text-align: center;color: orange;">Please Upload Your Resume</h5>', unsafe_allow_html=True)
            
#             elif openai_api_key == '':
#                 st.markdown(f'<h5 style="text-align: center;color: orange;">Please Enter OpenAI API Key</h5>', unsafe_allow_html=True)


#     def strength_prompt(query_with_chunks):
#         query = f'''need to detailed analysis and explain of the strength of below resume and finally conclude them
#                     """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#                     {query_with_chunks}
#                     """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#                     '''
#         return query


#     def resume_strength():

#         with st.form(key='Strength'):

#             # User Upload the Resume
#             add_vertical_space(1)
#             pdf = st.file_uploader(label='Upload Your Resume', type='pdf')
#             add_vertical_space(1)

#             # Enter OpenAI API Key
#             col1,col2 = st.columns([0.6,0.4])
#             with col1:
#                 openai_api_key = st.text_input(label='Enter OpenAI API Key', type='password')
#             add_vertical_space(2)

#             # Click on Submit Button
#             submit = st.form_submit_button(label='Submit')
#             add_vertical_space(1)

#         add_vertical_space(3)
#         if submit:
#             if pdf is not None and openai_api_key != '':
#                 try:
#                     with st.spinner('Processing...'):
                    
#                         pdf_chunks = resume_analyzer.pdf_to_chunks(pdf)

#                         summary_prompt = resume_analyzer.summary_prompt(query_with_chunks=pdf_chunks)

#                         summary = resume_analyzer.openai(openai_api_key=openai_api_key, chunks=pdf_chunks, analyze=summary_prompt)
                        
#                         strength_prompt = resume_analyzer.strength_prompt(query_with_chunks=summary)

#                         strength = resume_analyzer.openai(openai_api_key=openai_api_key, chunks=pdf_chunks, analyze=strength_prompt)

#                     st.markdown(f'<h4 style="color: orange;">Strength:</h4>', unsafe_allow_html=True)
#                     st.write(strength)

#                 except Exception as e:
#                     st.markdown(f'<h5 style="text-align: center;color: orange;">{e}</h5>', unsafe_allow_html=True)

#             elif pdf is None:
#                 st.markdown(f'<h5 style="text-align: center;color: orange;">Please Upload Your Resume</h5>', unsafe_allow_html=True)
            
#             elif openai_api_key == '':
#                 st.markdown(f'<h5 style="text-align: center;color: orange;">Please Enter OpenAI API Key</h5>', unsafe_allow_html=True)


#     def weakness_prompt(query_with_chunks):
#         query = f'''need to detailed analysis and explain of the weakness of below resume and how to improve make a better resume.

#                     """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#                     {query_with_chunks}
#                     """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#                     '''
#         return query


#     def resume_weakness():

#         with st.form(key='Weakness'):

#             # User Upload the Resume
#             add_vertical_space(1)
#             pdf = st.file_uploader(label='Upload Your Resume', type='pdf')
#             add_vertical_space(1)

#             # Enter OpenAI API Key
#             col1,col2 = st.columns([0.6,0.4])
#             with col1:
#                 openai_api_key = st.text_input(label='Enter OpenAI API Key', type='password')
#             add_vertical_space(2)

#             # Click on Submit Button
#             submit = st.form_submit_button(label='Submit')
#             add_vertical_space(1)
        
#         add_vertical_space(3)
#         if submit:
#             if pdf is not None and openai_api_key != '':
#                 try:
#                     with st.spinner('Processing...'):
                    
#                         pdf_chunks = resume_analyzer.pdf_to_chunks(pdf)

#                         summary_prompt = resume_analyzer.summary_prompt(query_with_chunks=pdf_chunks)

#                         summary = resume_analyzer.openai(openai_api_key=openai_api_key, chunks=pdf_chunks, analyze=summary_prompt)

#                         weakness_prompt = resume_analyzer.weakness_prompt(query_with_chunks=summary)

#                         weakness = resume_analyzer.openai(openai_api_key=openai_api_key, chunks=pdf_chunks, analyze=weakness_prompt)

#                     st.markdown(f'<h4 style="color: orange;">Weakness and Suggestions:</h4>', unsafe_allow_html=True)
#                     st.write(weakness)

#                 except Exception as e:
#                     st.markdown(f'<h5 style="text-align: center;color: orange;">{e}</h5>', unsafe_allow_html=True)

#             elif pdf is None:
#                 st.markdown(f'<h5 style="text-align: center;color: orange;">Please Upload Your Resume</h5>', unsafe_allow_html=True)
            
#             elif openai_api_key == '':
#                 st.markdown(f'<h5 style="text-align: center;color: orange;">Please Enter OpenAI API Key</h5>', unsafe_allow_html=True)


#     def job_title_prompt(query_with_chunks):

#         query = f''' what are the job roles i apply to likedin based on below?
                    
#                     """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#                     {query_with_chunks}
#                     """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#                     '''
#         return query


#     def job_title_suggestion():

#         with st.form(key='Job Titles'):

#             # User Upload the Resume
#             add_vertical_space(1)
#             pdf = st.file_uploader(label='Upload Your Resume', type='pdf')
#             add_vertical_space(1)

#             # Enter OpenAI API Key
#             col1,col2 = st.columns([0.6,0.4])
#             with col1:
#                 openai_api_key = st.text_input(label='Enter OpenAI API Key', type='password')
#             add_vertical_space(2)

#             # Click on Submit Button
#             submit = st.form_submit_button(label='Submit')
#             add_vertical_space(1)

#         add_vertical_space(3)
#         if submit:
#             if pdf is not None and openai_api_key != '':
#                 try:
#                     with st.spinner('Processing...'):
                    
#                         pdf_chunks = resume_analyzer.pdf_to_chunks(pdf)

#                         summary_prompt = resume_analyzer.summary_prompt(query_with_chunks=pdf_chunks)

#                         summary = resume_analyzer.openai(openai_api_key=openai_api_key, chunks=pdf_chunks, analyze=summary_prompt)

#                         job_title_prompt = resume_analyzer.job_title_prompt(query_with_chunks=summary)

#                         job_title = resume_analyzer.openai(openai_api_key=openai_api_key, chunks=pdf_chunks, analyze=job_title_prompt)

#                     st.markdown(f'<h4 style="color: orange;">Job Titles:</h4>', unsafe_allow_html=True)
#                     st.write(job_title)

#                 except Exception as e:
#                     st.markdown(f'<h5 style="text-align: center;color: orange;">{e}</h5>', unsafe_allow_html=True)

#             elif pdf is None:
#                 st.markdown(f'<h5 style="text-align: center;color: orange;">Please Upload Your Resume</h5>', unsafe_allow_html=True)
            
#             elif openai_api_key == '':
#                 st.markdown(f'<h5 style="text-align: center;color: orange;">Please Enter OpenAI API Key</h5>', unsafe_allow_html=True)



# class linkedin_scraper:

#     def webdriver_setup():
            
#         options = webdriver.ChromeOptions()
#         options.add_argument('--headless')
#         options.add_argument('--no-sandbox')
#         options.add_argument('--disable-dev-shm-usage')

#         driver = webdriver.Chrome(options=options)
#         driver.maximize_window()
#         return driver


#     def get_userinput():

#         add_vertical_space(2)
#         with st.form(key='linkedin_scarp'):

#             add_vertical_space(1)
#             col1,col2,col3 = st.columns([0.5,0.3,0.2], gap='medium')
#             with col1:
#                 job_title_input = st.text_input(label='Job Title')
#                 job_title_input = job_title_input.split(',')
#             with col2:
#                 job_location = st.text_input(label='Job Location', value='India')
#             with col3:
#                 job_count = st.number_input(label='Job Count', min_value=1, value=1, step=1)

#             # Submit Button
#             add_vertical_space(1)
#             submit = st.form_submit_button(label='Submit')
#             add_vertical_space(1)
        
#         return job_title_input, job_location, job_count, submit


#     def build_url(job_title, job_location):

#         b = []
#         for i in job_title:
#             x = i.split()
#             y = '%20'.join(x)
#             b.append(y)

#         job_title = '%2C%20'.join(b)
#         link = f"https://in.linkedin.com/jobs/search?keywords={job_title}&location={job_location}&locationId=&geoId=102713980&f_TPR=r604800&position=1&pageNum=0"

#         return link
    

#     def open_link(driver, link):

#         while True:
#             # Break the Loop if the Element is Found, Indicating the Page Loaded Correctly
#             try:
#                 driver.get(link)
#                 driver.implicitly_wait(5)
#                 time.sleep(3)
#                 driver.find_element(by=By.CSS_SELECTOR, value='span.switcher-tabs__placeholder-text.m-auto')
#                 return
            
#             # Retry Loading the Page
#             except NoSuchElementException:
#                 continue


#     def link_open_scrolldown(driver, link, job_count):
        
#         # Open the Link in LinkedIn
#         linkedin_scraper.open_link(driver, link)

#         # Scroll Down the Page
#         for i in range(0,job_count):

#             # Simulate clicking the Page Up button
#             body = driver.find_element(by=By.TAG_NAME, value='body')
#             body.send_keys(Keys.PAGE_UP)

#             # Locate the sign-in modal dialog 
#             try:
#                 driver.find_element(by=By.CSS_SELECTOR, 
#                                 value="button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']>icon>svg").click()
#             except:
#                 pass

#             # Scoll down the Page to End
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#             driver.implicitly_wait(2)

#             # Click on See More Jobs Button if Present
#             try:
#                 x = driver.find_element(by=By.CSS_SELECTOR, value="button[aria-label='See more jobs']").click()
#                 driver.implicitly_wait(5)
#             except:
#                 pass


#     def job_title_filter(scrap_job_title, user_job_title_input):
        
#         # User Job Title Convert into Lower Case
#         user_input = [i.lower().strip() for i in user_job_title_input]

#         # scraped Job Title Convert into Lower Case
#         scrap_title = [i.lower().strip() for i in [scrap_job_title]]

#         # Verify Any User Job Title in the scraped Job Title
#         confirmation_count = 0
#         for i in user_input:
#             if all(j in scrap_title[0] for j in i.split()):
#                 confirmation_count += 1

#         # Return Job Title if confirmation_count greater than 0 else return NaN
#         if confirmation_count > 0:
#             return scrap_job_title
#         else:
#             return np.nan


#     def scrap_company_data(driver, job_title_input, job_location):

#         # scraping the Company Data
#         company = driver.find_elements(by=By.CSS_SELECTOR, value='h4[class="base-search-card__subtitle"]')
#         company_name = [i.text for i in company]

#         location = driver.find_elements(by=By.CSS_SELECTOR, value='span[class="job-search-card__location"]')
#         company_location = [i.text for i in location]

#         title = driver.find_elements(by=By.CSS_SELECTOR, value='h3[class="base-search-card__title"]')
#         job_title = [i.text for i in title]

#         url = driver.find_elements(by=By.XPATH, value='//a[contains(@href, "/jobs/")]')
#         website_url = [i.get_attribute('href') for i in url]

#         # combine the all data to single dataframe
#         df = pd.DataFrame(company_name, columns=['Company Name'])
#         df['Job Title'] = pd.DataFrame(job_title)
#         df['Location'] = pd.DataFrame(company_location)
#         df['Website URL'] = pd.DataFrame(website_url)

#         # Return Job Title if there are more than 1 matched word else return NaN
#         df['Job Title'] = df['Job Title'].apply(lambda x: linkedin_scraper.job_title_filter(x, job_title_input))

#         # Return Location if User Job Location in Scraped Location else return NaN
#         df['Location'] = df['Location'].apply(lambda x: x if job_location.lower() in x.lower() else np.nan)
        
#         # Drop Null Values and Reset Index
#         df = df.dropna()
#         df.reset_index(drop=True, inplace=True)

#         return df 
        

#     def scrap_job_description(driver, df, job_count):
        
#         # Get URL into List
#         website_url = df['Website URL'].tolist()
        
#         # Scrap the Job Description
#         job_description = []
#         description_count = 0

#         for i in range(0, len(website_url)):
#             try:
#                 # Open the Link in LinkedIn
#                 linkedin_scraper.open_link(driver, website_url[i])

#                 # Click on Show More Button
#                 driver.find_element(by=By.CSS_SELECTOR, value='button[data-tracking-control-name="public_jobs_show-more-html-btn"]').click()
#                 driver.implicitly_wait(5)
#                 time.sleep(1)

#                 # Get Job Description
#                 description = driver.find_elements(by=By.CSS_SELECTOR, value='div[class="show-more-less-html__markup relative overflow-hidden"]')
#                 data = [i.text for i in description][0]
                
#                 # Check Description length and Duplicate
#                 if len(data.strip()) > 0 and data not in job_description:
#                     job_description.append(data)
#                     description_count += 1
#                 else:
#                     job_description.append('Description Not Available')
            
#             # If any unexpected issue 
#             except:
#                 job_description.append('Description Not Available')
            
#             # Check Description Count reach User Job Count
#             if description_count == job_count:
#                 break

#         # Filter the Job Description
#         df = df.iloc[:len(job_description), :]

#         # Add Job Description in Dataframe
#         df['Job Description'] = pd.DataFrame(job_description, columns=['Description'])
#         df['Job Description'] = df['Job Description'].apply(lambda x: np.nan if x=='Description Not Available' else x)
#         df = df.dropna()
#         df.reset_index(drop=True, inplace=True)
#         return df


#     def display_data_userinterface(df_final):

#         # Display the Data in User Interface
#         add_vertical_space(1)
#         if len(df_final) > 0:
#             for i in range(0, len(df_final)):
                
#                 st.markdown(f'<h3 style="color: orange;">Job Posting Details : {i+1}</h3>', unsafe_allow_html=True)
#                 st.write(f"Company Name : {df_final.iloc[i,0]}")
#                 st.write(f"Job Title    : {df_final.iloc[i,1]}")
#                 st.write(f"Location     : {df_final.iloc[i,2]}")
#                 st.write(f"Website URL  : {df_final.iloc[i,3]}")

#                 with st.expander(label='Job Desription'):
#                     st.write(df_final.iloc[i, 4])
#                 add_vertical_space(3)
        
#         else:
#             st.markdown(f'<h5 style="text-align: center;color: orange;">No Matching Jobs Found</h5>', 
#                                 unsafe_allow_html=True)


#     def main():
        
#         # Initially set driver to None
#         driver = None
        
#         try:
#             job_title_input, job_location, job_count, submit = linkedin_scraper.get_userinput()
#             add_vertical_space(2)
            
#             if submit:
#                 if job_title_input != [] and job_location != '':
                    
#                     with st.spinner('Chrome Webdriver Setup Initializing...'):
#                         driver = linkedin_scraper.webdriver_setup()
                                       
#                     with st.spinner('Loading More Job Listings...'):

#                         # build URL based on User Job Title Input
#                         link = linkedin_scraper.build_url(job_title_input, job_location)

#                         # Open the Link in LinkedIn and Scroll Down the Page
#                         linkedin_scraper.link_open_scrolldown(driver, link, job_count)

#                     with st.spinner('scraping Job Details...'):

#                         # Scraping the Company Name, Location, Job Title and URL Data
#                         df = linkedin_scraper.scrap_company_data(driver, job_title_input, job_location)

#                         # Scraping the Job Descriptin Data
#                         df_final = linkedin_scraper. scrap_job_description(driver, df, job_count)
                    
#                     # Display the Data in User Interface
#                     linkedin_scraper.display_data_userinterface(df_final)

                
#                 # If User Click Submit Button and Job Title is Empty
#                 elif job_title_input == []:
#                     st.markdown(f'<h5 style="text-align: center;color: orange;">Job Title is Empty</h5>', 
#                                 unsafe_allow_html=True)
                
#                 elif job_location == '':
#                     st.markdown(f'<h5 style="text-align: center;color: orange;">Job Location is Empty</h5>', 
#                                 unsafe_allow_html=True)

#         except Exception as e:
#             add_vertical_space(2)
#             st.markdown(f'<h5 style="text-align: center;color: orange;">{e}</h5>', unsafe_allow_html=True)
        
#         finally:
#             if driver:
#                 driver.quit()



# # Streamlit Configuration Setup
# streamlit_config()
# add_vertical_space(2)



# with st.sidebar:

#     add_vertical_space(4)

#     option = option_menu(menu_title='', options=['Summary', 'Strength', 'Weakness', 'Job Titles', 'Linkedin Jobs'],
#                          icons=['house-fill', 'database-fill', 'pass-fill', 'list-ul', 'linkedin'])



# if option == 'Summary':

#     resume_analyzer.resume_summary()



# elif option == 'Strength':

#     resume_analyzer.resume_strength()



# elif option == 'Weakness':

#     resume_analyzer.resume_weakness()



# elif option == 'Job Titles':

#     resume_analyzer.job_title_suggestion()



# elif option == 'Linkedin Jobs':
    
#     linkedin_scraper.main()

