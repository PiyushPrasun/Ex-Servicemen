# army_job_fetcher_custom_format.py

import google.generativeai as genai
import json
import re
import os
from pathlib import Path

# Get the current directory where the script is located
CURRENT_DIR = Path(__file__).parent
OUTPUT_FILE = CURRENT_DIR / "custom_army_jobs.json"

# Your Gemini API key
API_KEY = "AIzaSyDm-IoMwcpkJ6fpXfoEeBuFPywFJoClBDk"

# Gemini setup
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# Custom structured prompt
prompt = """
You are an assistant that extracts Indian army/defence jobs from online job sites.

Sources:
1. https://www.naukri.com/army-jobs
2. https://www.indeed.com/q-army-jobs.html

Return 5 army-related jobs **based in India** from each site.

Respond strictly in this JSON format per job:

{
  "title": "...",
  "category": "Government",
  "location": "Location:...",
  "posted_date": "...",
  "Deadline_date": "...",
  "view_url": "...",
  "description": "...",
  "apply_link": "..."
}

Output as a list of such JSON job objects — no markdown, no text, no headings. JSON only.
"""

def clean_and_parse_json(text):
    text = re.sub(r"```json|```", "", text).strip()
    try:
        parsed = json.loads(text)
        return parsed
    except json.JSONDecodeError as e:
        print("ERROR: Could not parse JSON:", e)
        print("Raw output:\n", text)
        return None

def fetch_and_save_jobs():
    print("Fetching army/defence jobs in India...")

    try:
        response = model.generate_content(prompt)
        raw_text = response.text

        job_list = clean_and_parse_json(raw_text)
        if not job_list or not isinstance(job_list, list):
            print("ERROR: Expected a list of job objects.")
            return

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(job_list, f, indent=2, ensure_ascii=False)

        print(f"SUCCESS: Saved {len(job_list)} jobs to '{OUTPUT_FILE}'")

    except Exception as e:
        print("ERROR during fetch:", e)

if __name__ == "__main__":
    fetch_and_save_jobs()
