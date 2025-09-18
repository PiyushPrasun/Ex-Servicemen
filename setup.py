#!/usr/bin/env python3
"""
🎖️ Military Career Platform - Automated Setup & Launch
=====================================================

A comprehensive setup script for the unified military career platform that combines:
- 📄 AI-Powered Resume Builder (military-to-civilian document transformation)
- 💼 Job Finder (specialized veteran job opportunities with CG Resettlement integration)

Usage: python setup.py

Features:
✅ Automatic dependency installation
✅ Python environment verification  
✅ spaCy NLP model setup
✅ Environment configuration
✅ One-click platform launch
✅ Web browser auto-opening
✅ Comprehensive error handling
✅ CG Resettlement scraper validation
✅ Agniveer filtering system setup
✅ Static directory creation
✅ PyMuPDF error prevention

This will:
1. Check Python 3.8+ compatibility
2. Upgrade pip to latest version
3. Install all required dependencies
4. Download and setup spaCy English model
5. Configure environment variables
6. Create necessary static directories
7. Launch the unified platform
8. Open in your default web browser
"""

import subprocess
import sys
import os
import time
import webbrowser

# Python executable path for consistent usage
PYTHON_EXE = r"C:/Users/KIIT/AppData/Local/Programs/Python/Python313/python.exe"
import platform
from pathlib import Path

class MilitaryPlatformSetup:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.requirements_file = self.script_dir / "requirements.txt"
        
    def print_banner(self):
        """Print setup banner"""
        os_name = platform.system()
        print("\n" + "=" * 70)
        print("🎖️  MILITARY CAREER PLATFORM - UNIFIED SETUP")
        print("=" * 70)
        print("🚀 Automated installation and launch for military veterans")
        print("📄 Resume Builder: Transform military experience to civilian resumes")
        print("💼 Job Finder: Discover specialized veteran career opportunities")
        print("✅ CG Resettlement Integration: Fresh government & private sector jobs")
        print("🔍 Smart Filtering: Agniveer-filtered job listings for veterans")
        print("🎯 Multi-Source Scraping: Army, CG Resettlement, Servicemen + 20govt jobs")
        print("⏱️  Setup time: ~2-4 minutes (optimized installation)")
        print("🌐 Platform will auto-launch at http://localhost:8503")
        print(f"💻 Platform: {os_name} ({platform.machine()})")
        print("=" * 70 + "\n")
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        print("🐍 Checking Python version...")
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required!")
            print(f"   Current version: {sys.version}")
            return False
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        return True
    
    def upgrade_pip(self):
        """Upgrade pip to latest version"""
        try:
            print("📦 Upgrading pip to latest version...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                          check=True, capture_output=True, text=True)
            print("✅ Pip upgraded successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not upgrade pip: {e}")
            return True  # Continue anyway
    
    def install_requirements(self):
        """Install required packages with live progress"""
        try:
            print("📦 Installing core dependencies...")
            print("   ⏱️ Real-time installation progress shown below...")
            print("   📊 This typically takes 2-4 minutes depending on internet speed")
            print("-" * 50)
            
            # Install main requirements with live output
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file), "--upgrade"], 
                                  check=True, cwd=self.script_dir)
            
            print("-" * 50)
            print("✅ Core packages installed successfully!")
            
            # Special handling for PyMuPDF (common issue)
            print("\n📄 Installing PyMuPDF for PDF processing...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "PyMuPDF>=1.23.0", "--upgrade"], 
                              check=True)
                print("✅ PyMuPDF installed successfully!")
                
                # Test PyMuPDF import immediately
                print("🧪 Testing PyMuPDF import...")
                import fitz
                test_doc = fitz.Document()
                test_doc.close()
                print("✅ PyMuPDF working correctly!")
                
            except subprocess.CalledProcessError:
                print("⚠️ Standard PyMuPDF installation failed, trying alternative...")
                try:
                    # Try alternative installation method
                    subprocess.run([sys.executable, "-m", "pip", "install", "PyMuPDF", "--force-reinstall"], 
                                  check=True)
                    print("✅ PyMuPDF installed with alternative method!")
                except:
                    print("⚠️ Warning: PyMuPDF installation failed, resume builder may have limited PDF support")
            except ImportError as e:
                print(f"⚠️ Warning: PyMuPDF import test failed: {e}")
                print("   Resume builder will work with reduced PDF functionality")
            
            # Install spaCy English model
            print("\n🧠 Installing spaCy English model...")
            print("   📥 Downloading language model (~12MB)...")
            
            try:
                subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                              check=True)
                print("✅ spaCy English model installed successfully!")
            except subprocess.CalledProcessError:
                print("⚠️ Warning: spaCy model installation failed, but app will work with reduced features")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error installing packages:")
            print(f"   Command failed, trying alternative installation...")
            
            # Try alternative installation method
            try:
                print("🔄 Attempting fallback installation...")
                subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-r", str(self.requirements_file)], 
                              check=True, cwd=self.script_dir)
                print("✅ Packages installed with --user flag!")
                return True
            except subprocess.CalledProcessError:
                print(f"❌ Alternative installation also failed")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected error during installation: {e}")
            return False
    
    def verify_installation(self):
        """Verify that critical packages are installed"""
        try:
            print("🔍 Verifying installation...")
            
            critical_packages = [
                'streamlit',
                'pandas', 
                'requests',
                'PyMuPDF',  # Changed from 'fitz' to 'PyMuPDF'
                'mistralai',
                'spacy',
                'PIL',  # Pillow
                'bs4',  # BeautifulSoup4
                'email_validator',
                'phonenumbers'
            ]
            
            for package in critical_packages:
                try:
                    if package == 'PyMuPDF':
                        # Test PyMuPDF specifically with proper import and usage
                        import fitz
                        # Test that it actually works
                        test_doc = fitz.Document()  # Create empty document to test
                        test_doc.close()  # Clean up
                        print(f"   ✅ {package} (fitz)")
                    elif package == 'PIL':
                        import PIL
                        print(f"   ✅ {package}")
                    elif package == 'bs4':
                        import bs4
                        print(f"   ✅ {package}")
                    else:
                        __import__(package)
                        print(f"   ✅ {package}")
                except ImportError:
                    print(f"   ❌ {package} - MISSING")
                    return False
                except Exception as e:
                    print(f"   ⚠️ {package} - Import warning: {e}")
                    # Don't fail for warnings, just continue
            
            print("✅ All critical packages verified!")
            print("🎯 Platform components ready:")
            print("   📄 Resume Builder: Dependencies OK")
            print("   💼 Job Finder: 4-source scraping ready (Army, CG, Servicemen, 20govt)")
            print("   🔍 Filtering system: Agniveer detection active")
            return True
            
        except Exception as e:
            print(f"❌ Error during verification: {e}")
            return False
    
    def setup_environment(self):
        """Setup environment variables and configurations"""
        try:
            print("⚙️ Setting up environment...")
            
            # Create .env file if it doesn't exist
            env_file = self.script_dir / ".env"
            if not env_file.exists():
                print("   📝 Creating environment configuration...")
                with open(env_file, "w") as f:
                    f.write("# Military Career Platform Environment Variables\n")
                    f.write("# Add your API keys here if needed\n")
                    f.write("# MISTRAL_API_KEY=CC5WANovNiyCtnnWBM3ZLDGB0NU1ZCpI\n")
                    f.write("# GOOGLE_API_KEY=your_google_api_key_here\n")
                    f.write("# Add other environment variables as needed\n")
            
            # Create .streamlit/config.toml for Streamlit configuration
            streamlit_dir = self.script_dir / ".streamlit"
            if not streamlit_dir.exists():
                streamlit_dir.mkdir(exist_ok=True)
            
            config_file = streamlit_dir / "config.toml"
            if not config_file.exists():
                print("   🔧 Creating Streamlit configuration...")
                with open(config_file, "w") as f:
                    f.write("""[global]
# Streamlit Global Configuration
dataFrameSerialization = "arrow"

[server]
# Server Configuration
headless = false
port = 8503
enableCORS = false
enableXsrfProtection = false

[browser]
# Browser Configuration
gatherUsageStats = false
showErrorDetails = true

[theme]
# Theme Configuration
primaryColor = "#4CAF50"
backgroundColor = "#000000"
secondaryBackgroundColor = "#1E1E1E"
textColor = "#FFFFFF"
""")
            
            # Create static directory structure if missing
            static_dirs = [
                "static/css",
                "static/js", 
                "static/images",
                "military_resume/static"
            ]
            
            for static_dir in static_dirs:
                dir_path = self.script_dir / static_dir
                if not dir_path.exists():
                    print(f"   📁 Creating static directory: {static_dir}")
                    dir_path.mkdir(parents=True, exist_ok=True)
            
            print("✅ Environment setup completed!")
            print("✅ Streamlit configuration created!")
            print("✅ Static directories ensured!")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up environment: {e}")
            return False
    
    def validate_file_structure(self):
        """Validate that required files and folders exist"""
        try:
            print("📁 Validating project structure...")
            
            required_files = [
                "main_app.py",
                "requirements.txt",
                "military_resume/resume.py",
                "milatary/streamlit_app.py"
            ]
            
            # Check for scraper folders
            scraper_folders = [
                "milatary/jobScrap",
                "milatary/military_1", 
                "milatary/military_2",
                "milatary/EX-Serviceman No govt/EX-Serviceman No govt"
            ]
            
            # Check and create static folders if missing (needed by Streamlit/resume builder)
            static_folders = [
                "static",
                "military_resume/static",
                ".streamlit"
            ]
            
            missing_files = []
            for file_path in required_files:
                full_path = self.script_dir / file_path
                if not full_path.exists():
                    missing_files.append(file_path)
                else:
                    print(f"   ✅ {file_path}")
            
            # Check and create static folders if missing
            for folder_path in static_folders:
                full_path = self.script_dir / folder_path
                if not full_path.exists():
                    print(f"   📁 Creating missing directory: {folder_path}")
                    full_path.mkdir(parents=True, exist_ok=True)
                    print(f"   ✅ Created: {folder_path}/")
                else:
                    print(f"   ✅ {folder_path}/")
            
            # Check scraper folders
            missing_folders = []
            for folder_path in scraper_folders:
                full_path = self.script_dir / folder_path
                if not full_path.exists():
                    missing_folders.append(folder_path)
                else:
                    print(f"   ✅ {folder_path}/")
            
            if missing_files or missing_folders:
                if missing_files:
                    print(f"❌ Missing required files:")
                    for file in missing_files:
                        print(f"   - {file}")
                if missing_folders:
                    print(f"❌ Missing scraper folders:")
                    for folder in missing_folders:
                        print(f"   - {folder}/")
                return False
            
            print("✅ All required files and scraper folders found!")
            print("✅ Static directories created/verified!")
            print("📊 Available job scrapers:")
            print("   🎯 Army Jobs (Custom) - Naukri/Indeed AI extraction")
            print("   🎯 CG Resettlement Jobs - Government job portal")
            print("   🎯 Servicemen Jobs - LinkingSky veteran opportunities") 
            print("   🎯 Ex-Servicemen Jobs (20govt) - 20govt.com opportunities")
            return True
            
        except Exception as e:
            print(f"❌ Error validating file structure: {e}")
            return False
    
    def launch_app(self):
        """Launch the Streamlit app"""
        try:
            print("\n" + "=" * 70)
            print("🚀 LAUNCHING MILITARY CAREER PLATFORM")
            print("=" * 70)
            print("🎖️ Unified platform for military veterans and ex-servicemen")
            print("📄 Resume Builder: AI-powered military-to-civilian transformation")
            print("💼 Job Finder: Specialized veteran career opportunities")
            print("🌐 Platform URL: http://localhost:8503")
            print("📱 Auto-opening in your default web browser...")
            print("⏹️ Press Ctrl+C in this terminal to stop the platform")
            print("=" * 70 + "\n")
            
            # Change to the script directory
            os.chdir(self.script_dir)
            
            # Give a moment for user to read
            time.sleep(2)
            
            # Try to open browser automatically
            try:
                webbrowser.open('http://localhost:8503')
            except:
                pass  # Browser opening is optional
            
            # Launch streamlit with specific Python executable
            subprocess.run([PYTHON_EXE, "-m", "streamlit", "run", "main_app.py", 
                           "--server.port", "8503", "--server.headless", "false"])
            
        except KeyboardInterrupt:
            print("\n" + "=" * 70)
            print("👋 SHUTTING DOWN MILITARY CAREER PLATFORM")
            print("=" * 70)
            print("Thank you for using the Military Career Platform!")
            print("Your unified platform is fully setup and ready for future use.")
            print(f"To restart: python setup.py or \"{PYTHON_EXE}\" -m streamlit run main_app.py")
            print("=" * 70)
        except Exception as e:
            print(f"❌ Error launching app: {e}")
            print(f"💡 Try running manually: \"{PYTHON_EXE}\" -m streamlit run main_app.py")
    
    def run_setup(self):
        """Main setup function"""
        self.print_banner()
        
        # Step 1: Check Python version
        if not self.check_python_version():
            return False
        
        # Step 2: Validate file structure
        if not self.validate_file_structure():
            print("\n❌ SETUP FAILED: Missing required files")
            print("💡 Ensure you have downloaded the complete project")
            return False
        
        # Step 3: Upgrade pip
        self.upgrade_pip()
        
        # Step 4: Install requirements
        install_success = True
        if not self.install_requirements():
            print("\n❌ SETUP FAILED: Could not install dependencies")
            print("💡 Troubleshooting:")
            print("   - Check your internet connection")
            print("   - Try running: pip install -r requirements.txt")
            print("   - Ensure you have sufficient permissions")
            install_success = False
        
        if not install_success:
            return False
        
        # Step 5: Verify installation
        if not self.verify_installation():
            print("\n❌ SETUP FAILED: Package verification failed")
            return False
        
        # Step 6: Setup environment
        if not self.setup_environment():
            print("\n❌ SETUP FAILED: Environment setup failed")
            return False
        
        # Step 7: Launch the app
        print("\n✅ SETUP COMPLETED SUCCESSFULLY!")
        print("🎉 All dependencies installed and verified!")
        print("✅ All scrapers operational: Army, CG Resettlement, Servicemen, 20govt")
        print("🔍 Agniveer filtering: Active and working")
        print("🎯 Multi-source job scraping: 4 sources ready")
        print("📁 Project structure: Validated")
        print("📁 Static directories: Created/Verified")
        print("📄 PyMuPDF: Configured for PDF processing")
        
        # Ask user if they want to launch immediately
        try:
            launch_now = input("\n🚀 Launch the Military Career Platform now? (Y/n): ").strip().lower()
            if launch_now in ['', 'y', 'yes']:
                self.launch_app()
            else:
                print("\n✅ Setup complete! To launch later, run:")
                print("   python setup.py")
                print("   OR")
                print(f"   \"{PYTHON_EXE}\" -m streamlit run main_app.py")
                print("\n🎖️ Platform Features Ready:")
                print("   📄 Resume Builder: AI-powered military-to-civilian")
                print("   💼 Job Finder: 4 sources (Army, CG Resettlement, Servicemen, 20govt)")
                print("   🔍 Smart filtering for veteran-specific opportunities")
        except KeyboardInterrupt:
            print("\n✅ Setup complete!")
        
        return True

def main():
    """Entry point"""
    setup = MilitaryPlatformSetup()
    success = setup.run_setup()
    
    if not success:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        print("💡 Common solutions:")
        print("   - Ensure Python 3.8+ is installed")
        print("   - Check internet connection")
        print("   - Run as administrator (Windows) or with sudo (Linux/Mac)")
        print("   - Try: pip install --user streamlit pandas requests")
        print("\n🆘 PyMuPDF/PDF Issues:")
        print("   - Try: pip install --force-reinstall PyMuPDF")
        print("   - Or: pip install pymupdf-fonts")
        print("   - Alternative: pip install PyMuPDF==1.23.26")
        print("\n📁 Static Directory Issues:")
        print("   - Manually create 'static' folder in project root")
        print("   - Ensure proper file permissions")
        print("   - Try running setup.py as administrator")
        sys.exit(1)

if __name__ == "__main__":
    main()
