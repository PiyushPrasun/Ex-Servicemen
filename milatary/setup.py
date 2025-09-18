#!/usr/bin/env python3
"""
Military Job Scraper Setup Script
This script sets up the environment and launches the Streamlit app.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    requirements = [
        "streamlit>=1.28.0",
        "pandas>=1.5.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",
        "google-generativeai>=0.3.0"
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            return False
    return True

def launch_app():
    """Launch the Streamlit app"""
    try:
        print("\n🚀 Launching Military Job Scraper Dashboard...")
        print("The app will open in your default web browser.")
        print("Press Ctrl+C to stop the app when you're done.\n")
        
        # Change to the script directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Launch streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down the app. Goodbye!")
    except Exception as e:
        print(f"❌ Error launching app: {e}")

def main():
    """Main setup function"""
    print("🎖️ Military Job Scraper Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        sys.exit(1)
    
    print(f"✓ Python {sys.version} detected")
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install some packages. Please check your internet connection.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")
    print("\n" + "="*40)
    
    # Launch the app
    launch_app()

if __name__ == "__main__":
    main()
