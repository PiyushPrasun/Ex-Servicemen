import streamlit as st
import pandas as pd
import json
import subprocess
import sys
import os
from datetime import datetime
import time
import threading
from pathlib import Path
import re

# Configure page
# st.set_page_config(  # Removed to prevent conflict with main_app.py
#     page_title="Military Job Scraper Dashboard",
#     page_icon="🎖️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main app background - pure black */
    .stApp {
        background: #000000;
        color: #ffffff;
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
        font-size: 3rem;
        color: #ffffff;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .scraper-card {
        background: #000000;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 10px 0;
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(255,255,255,0.1);
    }
    
    /* Job cards - BLACK background with WHITE text for readability */
    .job-card {
        background: #000000;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333333;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(255,255,255,0.1);
        color: #ffffff;
        transition: transform 0.2s ease;
    }
    
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255,255,255,0.2);
    }
    
    .job-card h4 {
        color: #ffffff;
        margin-bottom: 15px;
        font-weight: 600;
    }
    
    .job-card p {
        color: #ffffff;
        margin-bottom: 8px;
        line-height: 1.5;
    }
    
    .apply-button {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white !important;
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        text-decoration: none !important;
        display: inline-block;
        margin: 4px 2px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        text-align: center;
        min-width: 100px;
    }
    
    .apply-button:hover {
        background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        text-decoration: none !important;
    }
    
    /* View button with different color */
    .view-button {
        background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
        color: white !important;
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        text-decoration: none !important;
        display: inline-block;
        margin: 4px 2px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        text-align: center;
        min-width: 100px;
    }
    
    .view-button:hover {
        background: linear-gradient(135deg, #1e7e34 0%, #155724 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        text-decoration: none !important;
    }
    
    .status-success {
        color: #4CAF50;
        font-weight: bold;
    }
    
    .status-error {
        color: #f44336;
        font-weight: bold;
    }
    
    .status-running {
        color: #ff9800;
        font-weight: bold;
    }
    
    /* Metrics styling - black theme */
    .css-1r6slb0 {
        background: #000000;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #333333;
        color: #ffffff;
    }
    
    /* Button styling */
    .stButton > button {
        background: #333333;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: #555555;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(255,255,255,0.1);
    }
    
    /* Expander styling - black theme */
    .streamlit-expanderHeader {
        background-color: #000000;
        color: #ffffff;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Text areas and content - keep white text for main content */
    .stMarkdown {
        color: #ffffff;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    
    /* Sidebar text */
    .css-1d391kg .stSelectbox label {
        color: #ffffff;
    }
    
    /* Warning and info boxes */
    .stAlert {
        border-radius: 8px;
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

class JobScraperApp:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.scrapers = {
            "Army Jobs (Custom)": {
                "script": "jobScrap/realscrap.py",
                "output": "jobScrap/custom_army_jobs.json",
                "description": "Scrapes Army/Defence jobs using AI-powered extraction from Naukri and Indeed"
            },
            "CG Resettlement Jobs": {
                "script": "military_1/job_scraper.py",
                "output": "military_1/jobs_with_dates.json",
                "description": "Scrapes ex-servicemen jobs from CGResettlement.com"
            },
            "Servicemen Jobs": {
                "script": "military_2/job_scraper.py",
                "output": "military_2/servicemen_jobs.json",
                "description": "Scrapes servicemen jobs from LinkingSky.com"
            },
            "Ex-Servicemen Jobs (20govt)": {
                "script": "EX-Serviceman No govt/EX-Serviceman No govt/python.py",
                "output": "EX-Serviceman No govt/EX-Serviceman No govt/ex_servicemen_jobs_2025-08-12.json",
                "description": "Scrapes ex-servicemen civilian job opportunities from 20govt.com"
            }
        }
        
        # Initialize session state
        if 'scraping_status' not in st.session_state:
            st.session_state.scraping_status = {}
        if 'job_data' not in st.session_state:
            st.session_state.job_data = {}
        if 'filtered_jobs_count' not in st.session_state:
            st.session_state.filtered_jobs_count = {}
        if 'military_jobs' not in st.session_state:
            st.session_state.military_jobs = {}
            
        # Comprehensive Military/Army job filter patterns (jobs to exclude for civilian focus)
        self.military_patterns = {
            # Direct military terms
            r'\b(army|military|armed\s+forces|defence|defense)\b',
            r'\b(soldier|officer|lieutenant|captain|major|colonel|general)\b',
            r'\b(navy|naval|sailor|seaman|petty\s+officer)\b',
            r'\b(air\s*force|airman|pilot|squadron|wing\s+commander)\b',
            r'\b(coast\s+guard|border\s+security\s+force|bsf|crpf|cisf)\b',
            
            # Military organizations
            r'\bindian\s+(army|navy|air\s*force|coast\s*guard)\b',
            r'\b(territorial\s+army|rashtriya\s+rifles)\b',
            r'\b(national\s+cadet\s+corps|ncc)\b',
            r'\b(para\s*military|paramilitary|central\s+armed\s+police)\b',
            
            # Military ranks and positions
            r'\b(jco|junior\s+commissioned\s+officer)\b',
            r'\b(sepoy|lance\s+naik|naik|havildar|sergeant)\b',
            r'\b(sub\s+inspector|assistant\s+sub\s+inspector)\b',
            r'\b(commandant|deputy\s+commandant|assistant\s+commandant)\b',
            
            # Military recruitment terms
            r'\b(military\s+recruitment|army\s+recruitment|defence\s+recruitment)\b',
            r'\b(cantt|cantonment|military\s+station)\b',
            r'\b(regimental|battalion|brigade|division)\b',
            
            # Military technical terms
            r'\b(ordnance|artillery|armoured|infantry|signals)\b',
            r'\b(logistics|quartermaster|military\s+engineering)\b',
            r'\b(military\s+police|military\s+intelligence)\b',
            
            # Specific military schemes (but NOT Agniveer - we want to include those)
            r'\b(territorial\s+army\s+officer|tao)\b',
            r'\b(short\s+service\s+commission|ssc)\b',
            r'\b(permanent\s+commission|pc)\b',
            r'\b(national\s+defence\s+academy|nda)\b',
            r'\b(indian\s+military\s+academy|ima)\b',
            r'\b(officers\s+training\s+academy|ota)\b',
            r'\b(air\s+force\s+academy|afa)\b',
            r'\b(indian\s+naval\s+academy|ina)\b',
            
            # Combat and operational terms
            r'\b(combat|warfare|operations|tactical|strategic)\b.*\b(army|military|defence)\b',
            r'\b(security\s+guard|armed\s+guard)\b.*\b(military|defence)\b',
            
            # Exclude specific military job titles
            r'\b(rifle\s*man|gunner|driver\s+operator|cook\s+military)\b',
            r'\b(storeman|nursing\s+assistant).*\b(army|military)\b',
        }

    def is_military_job(self, job_data):
        """
        Comprehensive function to detect if a job posting is military/army related
        
        Args:
            job_data (dict): Job data dictionary with various fields
            
        Returns:
            bool: True if job is military-related, False otherwise (civilian job)
        """
        # Combine all text fields for comprehensive search
        text_fields = []
        
        # Get all possible text fields from job data
        possible_fields = [
            'title', 'job_title', 'description', 'category', 'location',
            'company', 'employer', 'qualification', 'requirements',
            'vacancy_details', 'post_details', 'notification_title',
            'exam_name', 'recruitment_board', 'organization'
        ]
        
        for field in possible_fields:
            value = job_data.get(field, '')
            if value and isinstance(value, str):
                text_fields.append(value)
        
        # Combine all text and convert to lowercase for case-insensitive matching
        combined_text = ' '.join(text_fields).lower()
        
        # Remove extra spaces and normalize
        combined_text = re.sub(r'\s+', ' ', combined_text).strip()
        
        # FIRST: Check if this is an Agniveer job - if so, treat as civilian opportunity
        if 'agniveer' in combined_text:
            return False  # Agniveer jobs are civilian opportunities
        
        # THEN: Check against all military patterns
        for pattern in self.military_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return True
        
        # Additional contextual checks for military jobs
        military_indicators = [
            # Military service related
            (r'\b(commission|enlistment|service)\b', r'\b(army|navy|air\s*force|military)\b'),
            (r'\b(recruitment|bharti|exam)\b', r'\b(defence|military|armed\s*forces)\b'),
            
            # Military training and academy
            (r'\b(training|academy|college)\b', r'\b(military|defence|army|navy)\b'),
            (r'\b(cadet|trainee)\b', r'\b(military|defence|officer)\b'),
            
            # Security forces (excluding civilian security)
            (r'\b(constable|head\s+constable|asi|si)\b', r'\b(police|force|security)\b'),
            
            # Military medical and technical
            (r'\b(medical|doctor|nurse)\b', r'\b(military|army|defence|cantonment)\b'),
            (r'\b(engineer|technician)\b', r'\b(military|defence|ordnance)\b'),
        ]
        
        for primary_pattern, secondary_pattern in military_indicators:
            if (re.search(primary_pattern, combined_text, re.IGNORECASE) and 
                re.search(secondary_pattern, combined_text, re.IGNORECASE)):
                return True
        
        return False

    def filter_civilian_jobs(self, jobs_list, scraper_name):
        """
        Filter out military jobs to show only civilian opportunities (including Agniveer)
        
        Args:
            jobs_list (list): List of job dictionaries
            scraper_name (str): Name of the scraper source
            
        Returns:
            tuple: (civilian_jobs_list, military_jobs_list, stats)
        """
        if not jobs_list:
            return [], [], {"total": 0, "civilian": 0, "military": 0}
        
        civilian_jobs = []
        military_jobs = []
        
        for job in jobs_list:
            if self.is_military_job(job):
                military_jobs.append(job)
            else:
                civilian_jobs.append(job)
        
        # Store stats
        stats = {
            "total": len(jobs_list),
            "civilian": len(civilian_jobs),
            "military": len(military_jobs)
        }
        
        # Update session state
        st.session_state.filtered_jobs_count[scraper_name] = stats
        st.session_state.military_jobs[scraper_name] = military_jobs
        
        return civilian_jobs, military_jobs, stats

    def run_scraper(self, scraper_name, script_path):
        """Run a scraper script"""
        try:
            st.session_state.scraping_status[scraper_name] = "running"
            
            # Get the full path
            full_script_path = self.base_path / script_path
            
            # Change to the script directory and run
            script_dir = full_script_path.parent
            script_name = full_script_path.name
            
            # Set environment variable to handle Unicode properly
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Run the script
            result = subprocess.run(
                [sys.executable, script_name],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                st.session_state.scraping_status[scraper_name] = "success"
                return True, "Scraping completed successfully!"
            else:
                st.session_state.scraping_status[scraper_name] = "error"
                return False, f"Error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            st.session_state.scraping_status[scraper_name] = "error"
            return False, "Script timed out after 5 minutes"
        except Exception as e:
            st.session_state.scraping_status[scraper_name] = "error"
            return False, f"Error: {str(e)}"
            return False, f"Error: {str(e)}"

    def load_job_data(self, output_path, scraper_name=None, apply_filter=True):
        """Load job data from JSON file with optional Agniveer filtering"""
        try:
            # Handle dynamic file names for Ex-Servicemen scraper (date-based filenames)
            if scraper_name == "Ex-Servicemen Jobs (20govt)" and "ex_servicemen_jobs_" in output_path:
                # Find the most recent JSON file in the directory
                folder_path = self.base_path / "EX-Serviceman No govt" / "EX-Serviceman No govt"
                if folder_path.exists():
                    json_files = list(folder_path.glob("ex_servicemen_jobs_*.json"))
                    if json_files:
                        # Get the most recent file
                        full_path = max(json_files, key=lambda f: f.stat().st_mtime)
                    else:
                        return []
                else:
                    return []
            else:
                full_path = self.base_path / output_path
            
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    raw_jobs = json.load(f)
                
                if apply_filter and scraper_name:
                    # Apply civilian jobs filtering (exclude military jobs, include Agniveer)
                    filtered_jobs, military_jobs, stats = self.filter_civilian_jobs(raw_jobs, scraper_name)
                    return filtered_jobs
                else:
                    return raw_jobs
            return []
        except Exception as e:
            st.error(f"Error loading data from {output_path}: {str(e)}")
            return []

    def display_jobs_table(self, jobs_data, scraper_name):
        """Display jobs in a formatted table with apply buttons"""
        if not jobs_data:
            st.warning("No jobs found.")
            return

        # Convert to DataFrame for better display
        df_data = []
        
        for i, job in enumerate(jobs_data):
            # Normalize job data structure (different scrapers have different formats)
            if scraper_name == "Army Jobs (Custom)":
                job_row = {
                    "Title": job.get("title", "N/A"),
                    "Category": job.get("category", "N/A"),
                    "Location": job.get("location", "N/A"),
                    "Posted Date": job.get("posted_date", "N/A"),
                    "Deadline": job.get("Deadline_date", "N/A"),
                    "Description": job.get("description", "N/A")[:200] + "..." if len(job.get("description", "")) > 200 else job.get("description", "N/A"),
                    "Apply Link": job.get("apply_link", "N/A"),
                    "View URL": job.get("view_url", "N/A")
                }
            elif scraper_name == "CG Resettlement Jobs":
                job_row = {
                    "Title": job.get("title", "N/A"),
                    "Category": job.get("category", "N/A"),
                    "Location": "N/A",
                    "Posted Date": job.get("posted_date", "N/A"),
                    "Deadline": job.get("deadline", "N/A"),
                    "Description": job.get("description", "N/A")[:200] + "..." if len(job.get("description", "")) > 200 else job.get("description", "N/A"),
                    "Apply Link": job.get("apply_link", "N/A"),
                    "View URL": job.get("view_url", "N/A")
                }
            elif scraper_name == "Servicemen Jobs":
                job_row = {
                    "Title": job.get("job_title", "N/A"),
                    "Category": "Government",
                    "Location": "N/A",
                    "Posted Date": job.get("post_date", "N/A"),
                    "Deadline": job.get("last_date", "N/A"),
                    "Description": "N/A",
                    "Apply Link": job.get("apply_link", "N/A"),
                    "View URL": job.get("view_url", "N/A")
                }
            elif scraper_name == "Ex-Servicemen Jobs (20govt)":
                job_row = {
                    "Title": job.get("title", "N/A"),
                    "Category": job.get("jobType", "Ex-Servicemen"),
                    "Location": "N/A",
                    "Posted Date": job.get("postDate", "N/A"),
                    "Deadline": job.get("lastDate", "N/A"),
                    "Description": job.get("description", "N/A")[:200] + "..." if len(job.get("description", "")) > 200 else job.get("description", "N/A"),
                    "Apply Link": job.get("applicationUrl", "N/A"),
                    "View URL": job.get("jobUrl", "N/A")
                }
            
            df_data.append(job_row)

        # Create DataFrame
        df = pd.DataFrame(df_data)
        
        # Display job cards instead of table for better formatting
        for i, job in enumerate(df_data):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h4>{job['Title']}</h4>
                    <p><strong>Category:</strong> {job['Category']}</p>
                    <p><strong>Location:</strong> {job['Location']}</p>
                    <p><strong>Posted:</strong> {job['Posted Date']} | <strong>Deadline:</strong> {job['Deadline']}</p>
                    <p><strong>Description:</strong> {job['Description']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Apply and View URL buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if job['Apply Link'] and job['Apply Link'] != "N/A":
                        st.markdown(f"""
                        <a href="{job['Apply Link']}" target="_blank" class="apply-button">
                            🔗 Apply Now
                        </a>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("Apply link not available")
                
                with col2:
                    if job['View URL'] and job['View URL'] != "N/A":
                        st.markdown(f"""
                        <a href="{job['View URL']}" target="_blank" class="view-button">
                            👁️ View Details
                        </a>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("View link not available")
                
                st.markdown("---")

    def main(self):
        # Header
        st.markdown('<h1 class="main-header">🎖️ Military Job Scraper Dashboard</h1>', unsafe_allow_html=True)
        
        # Sidebar
        st.sidebar.title("Navigation")
        
        # Initialize page in session state if not exists
        if 'page' not in st.session_state:
            st.session_state.page = "Dashboard"
            
        page = st.sidebar.selectbox(
            "Choose a section", 
            ["Dashboard", "Individual Scrapers", "All Jobs View"],
            index=["Dashboard", "Individual Scrapers", "All Jobs View"].index(st.session_state.page)
        )
        st.session_state.page = page
        
        if page == "Dashboard":
            self.dashboard_page()
        elif page == "Individual Scrapers":
            self.individual_scrapers_page()
        else:
            self.all_jobs_page()

    def dashboard_page(self):
        st.header("📊 Dashboard Overview")
        st.info("🎯 **Focus**: Showing civilian job opportunities (including Agniveer) - Military/Army jobs filtered out")
        
        # Quick stats - simplified without filtering information
        col1, col2, col3 = st.columns(3)
        
        total_civilian_jobs = 0
        
        for scraper_name, scraper_info in self.scrapers.items():
            jobs = self.load_job_data(scraper_info["output"], scraper_name, apply_filter=True)
            total_civilian_jobs += len(jobs)
        
        with col1:
            st.metric("Civilian Jobs Available", total_civilian_jobs)
        
        with col2:
            st.metric("Active Scrapers", len(self.scrapers))
        
        with col3:
            st.metric("Last Updated", datetime.now().strftime("%H:%M"))
        
        # Scrape All Button - simplified
        st.markdown("### 🚀 Run All Scrapers")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Scrape All Jobs", type="primary", use_container_width=True):
                self.run_all_scrapers()
        with col2:
            if st.button("📋 View All Jobs", type="secondary", use_container_width=True):
                st.session_state.page = "All Jobs View"
                st.rerun()
        
        # Display scraper statuses - simplified
        st.markdown("### 📈 Scraper Status")
        for scraper_name, scraper_info in self.scrapers.items():
            status = st.session_state.scraping_status.get(scraper_name, "idle")
            
            if status == "running":
                st.markdown(f"**{scraper_name}:** <span class='status-running'>🔄 Running...</span>", unsafe_allow_html=True)
            elif status == "success":
                jobs = self.load_job_data(scraper_info["output"], scraper_name, apply_filter=True)
                st.markdown(f"**{scraper_name}:** <span class='status-success'>✅ Success ({len(jobs)} civilian jobs found)</span>", unsafe_allow_html=True)
            elif status == "error":
                st.markdown(f"**{scraper_name}:** <span class='status-error'>❌ Error</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{scraper_name}:** ⏸️ Idle")
        
        # Show recent jobs preview if any scraper was successful
        successful_scrapers = [name for name, status in st.session_state.scraping_status.items() if status == "success"]
        if successful_scrapers:
            st.markdown("### 🎯 Recent Civilian Jobs Preview")
            st.info("💡 Click on 'All Jobs View' in the sidebar to see all civilian jobs with apply buttons!")
            st.success("✅ Agniveer jobs are included | ❌ Traditional Army/Military jobs are filtered out")
            
            # Show a few jobs from each successful scraper
            for scraper_name in successful_scrapers[:2]:  # Show max 2 scrapers on dashboard
                scraper_info = self.scrapers[scraper_name]
                jobs = self.load_job_data(scraper_info["output"], scraper_name, apply_filter=True)
                if jobs:
                    st.markdown(f"**{scraper_name}** - Showing 3 of {len(jobs)} civilian jobs:")
                    for job in jobs[:3]:  # Show first 3 jobs
                        with st.container():
                            if scraper_name == "Army Jobs (Custom)":
                                title = job.get("title", "N/A")
                                location = job.get("location", "N/A")
                                apply_link = job.get("apply_link", "N/A")
                                view_url = job.get("view_url", "N/A")
                            elif scraper_name == "CG Resettlement Jobs":
                                title = job.get("title", "N/A")
                                location = "N/A"
                                apply_link = job.get("apply_link", "N/A")
                                view_url = job.get("view_url", "N/A")
                            elif scraper_name == "Servicemen Jobs":
                                title = job.get("job_title", "N/A")
                                location = "N/A"
                                apply_link = job.get("apply_link", "N/A")
                                view_url = job.get("view_url", "N/A")
                            elif scraper_name == "Ex-Servicemen Jobs (20govt)":
                                title = job.get("title", "N/A")
                                location = "N/A"
                                apply_link = job.get("applicationUrl", "N/A")
                                view_url = job.get("jobUrl", "N/A")
                            
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**{title}**")
                                if location != "N/A":
                                    st.write(f"📍 {location}")
                            with col2:
                                if apply_link and apply_link != "N/A":
                                    st.markdown(f"""
                                    <a href="{apply_link}" target="_blank" class="apply-button">
                                        🔗 Apply
                                    </a>
                                    """, unsafe_allow_html=True)
                            with col3:
                                if view_url and view_url != "N/A":
                                    st.markdown(f"""
                                    <a href="{view_url}" target="_blank" class="view-button">
                                        👁️ View
                                    </a>
                                    """, unsafe_allow_html=True)
                            st.markdown("---")
                    
                    st.markdown(f"[View all {len(jobs)} civilian jobs from {scraper_name} →](javascript:void(0))")
                    st.markdown("")

    def individual_scrapers_page(self):
        st.header("🔧 Individual Scrapers")
        st.info("🎯 **Filter Applied**: Results show only civilian opportunities (Agniveer included, Army/Military excluded)")
        
        for scraper_name, scraper_info in self.scrapers.items():
            with st.expander(f"📋 {scraper_name}", expanded=False):
                st.markdown(f"""
                <div class="scraper-card">
                    <h4>{scraper_name}</h4>
                    <p>{scraper_info['description']}</p>
                    <p><strong>Script:</strong> {scraper_info['script']}</p>
                    <p><strong>Output:</strong> {scraper_info['output']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button(f"🚀 Run {scraper_name}", key=f"run_{scraper_name}"):
                        with st.spinner(f"Running {scraper_name}..."):
                            success, message = self.run_scraper(scraper_name, scraper_info["script"])
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                
                with col2:
                    if st.button(f"📊 View Civilian Jobs", key=f"view_{scraper_name}"):
                        jobs = self.load_job_data(scraper_info["output"], scraper_name, apply_filter=True)
                        st.write(f"Found {len(jobs)} civilian jobs (military jobs filtered out):")
                        self.display_jobs_table(jobs, scraper_name)

    def all_jobs_page(self):
        st.header("📋 All Civilian Jobs View")
        st.info("🎯 **Filter Applied**: Showing only civilian opportunities (including Agniveer) - Army/Military jobs excluded")
        
        # Load and combine all job data with filtering
        all_jobs = {}
        total_civilian_jobs = 0
        
        for scraper_name, scraper_info in self.scrapers.items():
            jobs = self.load_job_data(scraper_info["output"], scraper_name, apply_filter=True)
            if jobs:
                all_jobs[scraper_name] = jobs
                total_civilian_jobs += len(jobs)
        
        if not all_jobs:
            st.warning("No civilian job data found. Please run the scrapers first.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Run All Scrapers Now", type="primary"):
                    st.session_state.page = "Dashboard"
                    st.rerun()
            with col2:
                if st.button("🔧 Individual Scrapers", type="secondary"):
                    st.session_state.page = "Individual Scrapers"
                    st.rerun()
            return
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Civilian Jobs", total_civilian_jobs)
        with col2:
            st.metric("Sources", len(all_jobs))
        with col3:
            st.metric("Updated", datetime.now().strftime("%H:%M"))
        
        st.markdown("---")
        
        # Display jobs by scraper
        for scraper_name, jobs in all_jobs.items():
            with st.expander(f"🎯 {scraper_name} ({len(jobs)} civilian jobs)", expanded=True):
                self.display_jobs_table(jobs, scraper_name)

    def run_all_scrapers(self):
        """Run all scrapers sequentially"""
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        
        total_scrapers = len(self.scrapers)
        
        for i, (scraper_name, scraper_info) in enumerate(self.scrapers.items()):
            status_placeholder.write(f"Running {scraper_name}...")
            
            success, message = self.run_scraper(scraper_name, scraper_info["script"])
            
            if success:
                st.success(f"✅ {scraper_name} completed successfully!")
            else:
                st.error(f"❌ {scraper_name} failed: {message}")
            
            progress_bar.progress((i + 1) / total_scrapers)
        
        status_placeholder.write("All scrapers completed!")
        st.balloons()

# Run the app
if __name__ == "__main__":
    app = JobScraperApp()
    app.main()
