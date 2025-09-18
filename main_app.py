import streamlit as st
import sys
import os
import importlib.util
from pathlib import Path

# Add the military resume and job scraper directories to Python path
current_dir = Path(__file__).parent
resume_path = current_dir / "military_resume"
scraper_path = current_dir / "milatary"

sys.path.insert(0, str(resume_path))
sys.path.insert(0, str(scraper_path))

# Configure page
st.set_page_config(
    page_title="Military Career Platform",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main app background with larger base font */
    .stApp {
        background: #000000;
        color: #ffffff;
        font-size: 18px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Main content area - black background */
    .main .block-container {
        background-color: #000000;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem;
        color: #ffffff;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .main-header {
        font-size: 6rem;
        color: #ffffff;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    /* Service cards with larger text */
    .service-card {
        background: #000000;
        padding: 2.5rem;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        margin: 1.5rem 0;
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(255,255,255,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
    }
    
    .service-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255,255,255,0.2);
    }
    
    .service-card h3 {
        color: #4ecdc4;
        margin-bottom: 1.5rem;
        font-size: 2.5rem;
        text-align: center;
        font-weight: bold;
    }
    
    .service-card p {
        color: #ffffff;
        line-height: 1.8;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 1.3rem;
    }
    
    .service-card .features {
        list-style: none;
        padding: 0;
        margin: 1rem 0;
    }
    
    .service-card .features li {
        padding: 0.3rem 0;
        color: #e0e0e0;
    }
    
    .service-card .features li:before {
        content: "✓ ";
        color: #4ecdc4;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    /* Large buttons with blue color */
    .stButton > button {
        background: #1f77b4 !important;
        color: white !important;
        border: none;
        border-radius: 15px;
        padding: 1.5rem 3rem;
        font-weight: 700;
        font-size: 1.6rem;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 1.5rem;
        min-height: 4rem;
    }
    
    .stButton > button:hover {
        background: #0d5aa7 !important;
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(31, 119, 180, 0.3);
    }
    
    /* Welcome section */
    .welcome-section {
        background: #000000;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 2px 8px rgba(255,255,255,0.1);
        border: 1px solid #333333;
    }
    
    .welcome-section h2 {
        color: #4ecdc4;
        margin-bottom: 1.5rem;
        font-size: 3.5rem;
        font-weight: bold;
    }
    
    .welcome-section p {
        color: #ffffff;
        font-size: 2rem;
        line-height: 1.8;
        font-weight: 600;
    }
    
    /* Larger text everywhere */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-size: 1.8rem !important;
    }
    
    .stMarkdown {
        color: #ffffff;
        font-size: 1.2rem;
    }
    
    /* Sidebar with larger text */
    .css-1d391kg {
        background-color: #000000;
        color: #ffffff;
        font-size: 1.2rem;
    }
    
    /* Radio buttons much larger */
    .stRadio > label {
        font-size: 2rem !important;
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* Radio button container */
    .stRadio > div {
        font-size: 2rem !important;
    }
    
    /* Radio button text specifically */
    .stRadio > div > label > div:nth-child(2) {
        font-size: 2rem !important;
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* Sidebar title larger */
    .css-1d391kg h1 {
        font-size: 2.5rem !important;
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* Sidebar radio text */
    .css-1d391kg .stRadio {
        font-size: 2rem !important;
    }
    
    /* Radio option text */
    .css-1d391kg .stRadio label {
        font-size: 2rem !important;
        color: #ffffff !important;
        font-weight: 700;
        padding: 0.8rem 0;
    }
    
    /* Expander styling - black theme */
    .streamlit-expanderHeader {
        background-color: #000000;
        color: #ffffff;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Metrics styling - black theme */
    .css-1r6slb0 {
        background: #000000;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #333333;
        color: #ffffff;
    }
    
    /* Metric values */
    [data-testid="metric-container"] {
        background-color: #000000;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #333333;
    }
    
    [data-testid="metric-container"] > div {
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🎖️ Military Career Platform</h1>', unsafe_allow_html=True)
    
    # Welcome section
    st.markdown("""
    <div class="welcome-section">
        <h2>🚀 Empowering Military Veterans</h2>
        <p>Transform military experience into civilian career success</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎯 Navigation")
    st.sidebar.markdown("---")
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Home"
    
    # Service selection in sidebar
    service_choice = st.sidebar.radio(
        "Choose a Service:",
        ["🏠 Home", "📄 Resume Builder", "💼 Job Finder"],
        index=["🏠 Home", "📄 Resume Builder", "💼 Job Finder"].index(st.session_state.current_page)
    )
    
    # Update current page
    st.session_state.current_page = service_choice
    
    # Main content based on selection
    if service_choice == "🏠 Home":
        show_home_page()
    elif service_choice == "📄 Resume Builder":
        show_resume_builder()
    elif service_choice == "💼 Job Finder":
        show_job_finder()

def show_home_page():
    """Display the home page with service options"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="service-card">
            <h3>📄 Resume Builder</h3>
            <p>Transform your military experience into professional civilian resumes using AI technology.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Launch Resume Builder", key="resume_builder_btn"):
            st.session_state.current_page = "📄 Resume Builder"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="service-card">
            <h3>💼 Job Finder</h3>
            <p>Find career opportunities specifically designed for military veterans and ex-servicemen.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Launch Job Finder", key="job_finder_btn"):
            st.session_state.current_page = "💼 Job Finder"
            st.rerun()
def show_resume_builder():
    """Launch the resume builder application"""
    st.info("🚀 Launching Resume Builder...")
    
    try:
        # Load the resume module using importlib
        resume_file = current_dir / "military_resume" / "resume.py"
        
        if not resume_file.exists():
            st.error(f"❌ Resume file not found at: {resume_file}")
            return
        
        spec = importlib.util.spec_from_file_location("resume", resume_file)
        resume_module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules so it can be imported by other modules
        sys.modules["resume"] = resume_module
        spec.loader.exec_module(resume_module)
        
        # Run the main function
        if hasattr(resume_module, 'main'):
            resume_module.main()
        else:
            st.error("❌ Resume module not properly configured")
            
    except Exception as e:
        st.error(f"❌ Error launching resume builder: {str(e)}")

def show_job_finder():
    """Launch the job finder application"""
    st.info("🚀 Launching Job Finder...")
    
    try:
        # Load the streamlit_app module using importlib
        scraper_file = current_dir / "milatary" / "streamlit_app.py"
        
        if not scraper_file.exists():
            st.error(f"❌ Job scraper file not found at: {scraper_file}")
            return
        
        spec = importlib.util.spec_from_file_location("streamlit_app", scraper_file)
        scraper_module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules so it can be imported by other modules
        sys.modules["streamlit_app"] = scraper_module
        spec.loader.exec_module(scraper_module)
        
        # Create and run the app
        if hasattr(scraper_module, 'JobScraperApp'):
            app = scraper_module.JobScraperApp()
            app.main()
        else:
            st.error("❌ No JobScraperApp class found in streamlit_app module")
            
    except ImportError as e:
        st.error(f"❌ Error importing job scraper module: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error launching job finder: {str(e)}")

if __name__ == "__main__":
    main()
