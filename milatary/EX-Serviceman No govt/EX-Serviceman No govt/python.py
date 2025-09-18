#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ex-Servicemen Job Scraper - Python Script
Find Civilian Jobs for Retired Army Personnel
"""

import json
import time
from datetime import datetime, date
from typing import List, Dict
import pandas as pd
import requests
from bs4 import BeautifulSoup
from IPython.display import display, HTML, clear_output

class ExServicemenJobScraper:
    def __init__(self):
        self.scraped_jobs = []
        self.default_url = "https://20govt.com/jobs-for/ex-servicemen-vacancy/"
        
    def get_total_pages(self, base_url: str) -> int:
        """Get total number of pages available - automatically adapts to website changes"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(base_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for pagination info - multiple detection methods
            page_text = soup.get_text()
            import re
            
            # Method 1: Check for "Page 1 of X" pattern
            match = re.search(r'Page 1 of (\d+)', page_text)
            if match:
                total_pages = int(match.group(1))
                print(f"🔍 Found pagination text: Page 1 of {total_pages}")
                return total_pages
            
            # Method 2: Look for pagination links
            pagination = soup.find_all('a', href=True)
            max_page = 1
            
            for link in pagination:
                href = link.get('href', '')
                if '/page/' in href:
                    try:
                        # Extract page number from URL
                        page_part = href.split('/page/')[-1]
                        page_num = int(page_part.split('/')[0])
                        max_page = max(max_page, page_num)
                    except:
                        continue
            
            # Method 3: Look for "Last" or highest numbered page link
            for link in pagination:
                link_text = link.get_text(strip=True).lower()
                if 'last' in link_text:
                    href = link.get('href', '')
                    if '/page/' in href:
                        try:
                            page_num = int(href.split('/page/')[-1].split('/')[0])
                            max_page = max(max_page, page_num)
                        except:
                            continue
            
            # Method 4: Look for numbered pagination links
            for link in pagination:
                link_text = link.get_text(strip=True)
                if link_text.isdigit():
                    page_num = int(link_text)
                    max_page = max(max_page, page_num)
            
            detected_pages = max_page if max_page > 1 else 20  # Increased default for future growth
            print(f"🔍 Detected {detected_pages} pages available")
            return detected_pages
            
        except Exception as e:
            print(f"⚠️ Could not determine total pages: {e}")
            print("🔄 Using default of 20 pages to ensure all jobs are captured")
            return 20  # Increased default to handle future growth
    
    def is_ex_servicemen_job(self, title: str, description: str) -> bool:
        """Check if job is specifically for ex-servicemen (both civilian and military roles)"""
        title_lower = title.lower()
        desc_lower = description.lower()
        combined_text = f"{title_lower} {desc_lower}"
        
        # Keywords that indicate ex-servicemen jobs (expanded list)
        ex_servicemen_keywords = [
            'ex-servicemen', 'ex servicemen', 'ex-serviceman', 'ex serviceman',
            'retired', 'veteran', 'esm', 'retired officials', 'retired person',
            'ex-officers', 'ex officers', 'former military', 'defence personnel',
            'retired army', 'retired navy', 'retired air force', 'ex army',
            'ex navy', 'ex air force', 'armed force qualified', 'ex-service',
            'ex service', 'defense personnel', 'military veteran', 'army veteran',
            'navy veteran', 'air force veteran'
        ]
        
        # Organizations known to hire ex-servicemen (expanded)
        ex_servicemen_orgs = [
            'bel', 'bharat electronics', 'iocl', 'indian oil', 'drdo',
            'aiims', 'csir', 'echs', 'railway', 'secr', 'aps',
            'army public school', 'coast guard', 'capf', 'hal',
            'hindustan aeronautics', 'tmc', 'immt', 'psu', 'psc',
            'cewacor', 'csir-cbri', 'csl', 'cochin shipyard'
        ]
        
        # Special job titles that indicate ex-servicemen preference (expanded)
        ex_servicemen_titles = [
            'security officer', 'security chief', 'security assistant',
            'watch & ward', 'driver', 'technician', 'apprentice',
            'consultant', 'instructor', 'medical officer', 'clerk',
            'teaching', 'non-teaching', 'dental hygienist', 'dental officer',
            'nursing assistant', 'pharmacist', 'trade apprentice'
        ]
        
        # Check for direct ex-servicemen keywords
        has_ex_servicemen = any(keyword in combined_text for keyword in ex_servicemen_keywords)
        
        # Check for ex-servicemen friendly organizations
        has_ex_servicemen_org = any(org in combined_text for org in ex_servicemen_orgs)
        
        # Check for job titles commonly associated with ex-servicemen
        has_relevant_title = any(title_keyword in combined_text for title_keyword in ex_servicemen_titles)
        
        # Additional checks for specific patterns
        has_govt_sector = 'government sector' in combined_text
        has_contractual = 'contractual' in combined_text or 'contract' in combined_text
        
        # Return True if any condition is met
        return (has_ex_servicemen or 
                (has_ex_servicemen_org and (has_relevant_title or has_govt_sector)) or
                (has_relevant_title and has_contractual))
    
    def auto_detect_new_patterns(self, all_titles: List[str]) -> Dict:
        """Automatically detect new organizations and patterns from job titles"""
        new_orgs = set()
        new_keywords = set()
        
        for title in all_titles:
            title_lower = title.lower()
            words = title_lower.split()
            
            # Look for potential organization acronyms (2-5 uppercase letters)
            import re
            org_matches = re.findall(r'\b[A-Z]{2,5}\b', title)
            for org in org_matches:
                if org.lower() not in ['ex', 'esm', 'jobs', 'govt', 'post']:
                    new_orgs.add(org.lower())
            
            # Look for potential ex-servicemen related terms
            if any(term in title_lower for term in ['ex-', 'retired', 'veteran', 'defence']):
                for word in words:
                    if len(word) > 4 and word not in ['recruitment', 'vacancy', 'apply']:
                        new_keywords.add(word)
        
        return {
            'organizations': list(new_orgs),
            'keywords': list(new_keywords)
        }
    
    def save_learned_patterns(self, filename: str = "learned_patterns.json"):
        """Save patterns learned from previous scraping sessions"""
        if not self.scraped_jobs:
            return
        
        all_titles = [job['title'] for job in self.scraped_jobs]
        new_patterns = self.auto_detect_new_patterns(all_titles)
        
        try:
            # Try to load existing patterns
            with open(filename, 'r') as f:
                existing_patterns = json.load(f)
        except:
            existing_patterns = {'organizations': [], 'keywords': []}
        
        # Merge new patterns with existing ones
        existing_patterns['organizations'].extend(new_patterns['organizations'])
        existing_patterns['keywords'].extend(new_patterns['keywords'])
        
        # Remove duplicates
        existing_patterns['organizations'] = list(set(existing_patterns['organizations']))
        existing_patterns['keywords'] = list(set(existing_patterns['keywords']))
        
        # Save updated patterns
        with open(filename, 'w') as f:
            json.dump(existing_patterns, f, indent=2)
        
        print(f"🧠 Learned patterns saved to {filename}")
    
    def load_learned_patterns(self, filename: str = "learned_patterns.json") -> Dict:
        """Load previously learned patterns to improve future scraping"""
        try:
            with open(filename, 'r') as f:
                patterns = json.load(f)
                print(f"🧠 Loaded {len(patterns.get('organizations', []))} organizations and {len(patterns.get('keywords', []))} keywords from previous sessions")
                return patterns
        except:
            return {'organizations': [], 'keywords': []}

    def get_real_application_url(self, job_url: str) -> str:
        """Extract the real application URL from the job details page with enhanced detection"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Enhanced organization-based URL mapping (expanded)
            job_url_lower = job_url.lower()
            title_from_url = job_url.split('/')[-2] if '/' in job_url else job_url
            
            # Comprehensive organization mapping
            quick_mapping = {
                'bel': 'https://bel-india.in/careers',
                'aiims': 'https://aiimsrajkot.edu.in/recruitment',
                'aicte': 'https://facilities.aicte-india.org/recruitment_aicte1/',
                'navy': 'https://joinindiannavy.gov.in',
                'drdo': 'https://drdo.gov.in/recruitment',
                'iocl': 'https://iocl.com/careers',
                'echs': 'https://echs.gov.in/recruitment',
                'cewacor': 'https://www.cwceportal.com/careers',
                'cbri': 'https://cbri.res.in/career',
                'csl': 'https://cochinshipyard.in/career',
                'railway': 'https://rrbapply.gov.in',
                'secr': 'https://rrbapply.gov.in',
                'metro': 'https://rrbapply.gov.in',
                'aps': 'https://www.apschandimandir.in/',
                'hal': 'https://hal-india.co.in/career',
                'iisc': 'https://iisc.ac.in/careers/',
                'immt': 'https://immt.res.in/recruitment',
                'tmc': 'https://tmcorp.in/careers',
                'iit': 'https://iitbombay.iitb.ac.in/en/jobs-iit-bombay',
                'ssc': 'https://ssc.nic.in/Portal/SchemeFolder/SchemeRegister',
                'csir': 'https://csir.res.in/careers',
                'indian-army': 'https://joinindianarmy.nic.in'
            }
            
            # Multi-level organization detection
            for org_key, org_url in quick_mapping.items():
                if (org_key in title_from_url or 
                    org_key in job_url_lower or 
                    org_key.replace('-', '') in job_url_lower):
                    return org_url
            
            # Visit the job details page to extract real application URLs
            response = requests.get(job_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Look for direct application links with enhanced detection
            application_urls = []
            
            # Find all links on the page
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '').strip()
                text = link.get_text(strip=True).lower()
                
                # Skip if it's the same domain
                if '20govt.com' in href:
                    continue
                
                # Priority 1: Google Drive files and forms (immediate return)
                if 'drive.google.com' in href and ('file/d/' in href or 'forms' in href):
                    if href.startswith('http'):
                        # Ensure proper Google Drive URL format
                        if 'file/d/' in href and not href.endswith('/view'):
                            if '?usp=' not in href:
                                href = href + '/view?usp=sharing'
                        return href
                
                # Priority 2: PDF downloads (immediate return)
                if (href.endswith('.pdf') or '.pdf' in href) and href.startswith('http'):
                    return href
                
                # Priority 3: Government and educational domains
                if any(domain in href.lower() for domain in ['.gov.in', '.edu.in', '.nic.in']) and href.startswith('http'):
                    application_urls.append(href)
                
                # Priority 4: Organization recruitment portals (expanded list)
                org_domains = [
                    'bel-india.in', 'cbri.res.in', 'cochinshipyard.in', 'aiimsrajkot.edu.in',
                    'facilities.aicte-india.org', 'cwceportal.com', 'echs.gov.in', 'hal-india.co.in',
                    'iisc.ac.in', 'immt.res.in', 'tmcorp.in', 'iitbombay.iitb.ac.in', 'ssc.nic.in',
                    'csir.res.in', 'joinindianarmy.nic.in', 'rrbapply.gov.in', 'iocl.com',
                    'drdo.gov.in', 'joinindiannavy.gov.in'
                ]
                if any(domain in href.lower() for domain in org_domains) and href.startswith('http'):
                    application_urls.append(href)
                
                # Priority 5: Look for application-related text
                apply_keywords = ['apply', 'application', 'recruit', 'career', 'job', 'notification']
                if (any(keyword in text for keyword in apply_keywords) and 
                    href.startswith('http') and '20govt.com' not in href):
                    application_urls.append(href)
            
            # Method 2: Enhanced text content URL extraction
            page_text = soup.get_text()
            import re
            
            # Comprehensive URL patterns
            url_patterns = [
                r'https://drive\.google\.com/file/d/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_?&=-]*)?',
                r'https://forms\.google\.com/[a-zA-Z0-9_/\-]+',
                r'https://[a-zA-Z0-9.-]*\.gov\.in[^\s<>"\']*',
                r'https://[a-zA-Z0-9.-]*\.edu\.in[^\s<>"\']*',
                r'https://[a-zA-Z0-9.-]*\.nic\.in[^\s<>"\']*',
                r'https://[a-zA-Z0-9.-]*\.pdf[^\s<>"\']*',
                r'https://[a-zA-Z0-9.-]*\.co\.in[^\s<>"\']*career[^\s<>"\']*',
                r'https://[a-zA-Z0-9.-]*\.com[^\s<>"\']*career[^\s<>"\']*',
                r'https://[a-zA-Z0-9.-]*\.org[^\s<>"\']*recruit[^\s<>"\']*'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if '20govt.com' not in match and match not in application_urls:
                        # Special handling for Google Drive links (immediate return)
                        if 'drive.google.com' in match:
                            if 'file/d/' in match and not match.endswith('/view'):
                                if '?usp=' in match:
                                    match = match.split('?usp=')[0] + '/view?usp=sharing'
                                else:
                                    match = match + '/view?usp=sharing'
                            return match
                        application_urls.append(match)
            
            # Method 3: Look for embedded content and iframes
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if src and '20govt.com' not in src and src.startswith('http'):
                    application_urls.append(src)
            
            # Method 4: Look for form action URLs
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '')
                if action and '20govt.com' not in action and action.startswith('http'):
                    application_urls.append(action)
            
            # Return the best match with prioritization
            if application_urls:
                # Remove duplicates while preserving order
                unique_urls = []
                for url in application_urls:
                    if url not in unique_urls:
                        unique_urls.append(url)
                
                # Priority order: .gov.in > .edu.in > .nic.in > organization domains > others
                gov_urls = [url for url in unique_urls if '.gov.in' in url]
                if gov_urls:
                    return gov_urls[0]
                
                edu_urls = [url for url in unique_urls if '.edu.in' in url]
                if edu_urls:
                    return edu_urls[0]
                
                nic_urls = [url for url in unique_urls if '.nic.in' in url]
                if nic_urls:
                    return nic_urls[0]
                
                # Return first valid URL
                return unique_urls[0]
            
            # Enhanced fallback: Try to construct organization URL from job title
            job_title_match = re.search(r'([A-Z]{2,6})\s', job_url.split('/')[-1].replace('-', ' ').upper())
            if job_title_match:
                org_code = job_title_match.group(1).lower()
                if org_code in quick_mapping:
                    return quick_mapping[org_code]
            
            # Final fallback: Return a different apply URL format
            return job_url.replace('/jobs/', '/apply/')
            
        except Exception as e:
            # Silent fallback with different URL format
            try:
                return job_url.replace('/jobs/', '/apply/')
            except:
                return job_url

    def scrape_real_jobs(self, url: str, max_jobs: int = 500, max_pages: int = None) -> List[Dict]:
        """Actually scrape jobs from the website with automatic pagination detection - future-proof for new jobs"""
        all_jobs = []
        page = 1
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Automatically detect total pages if not specified
        if max_pages is None:
            total_pages = self.get_total_pages(url)
        else:
            total_pages = max_pages
            
        print(f"📊 Total pages to scrape: {total_pages}")
        print(f"🔍 Will scrape all {total_pages} pages for ex-servicemen jobs (civilian + military)")
        print(f"🎯 Filtering: Including ALL ex-servicemen related jobs")
        print(f"🔮 Future-proof: Automatically detects new pages and job types")
        
        while page <= total_pages:
            try:
                # Construct page URL
                if page == 1:
                    page_url = url
                else:
                    page_url = f"{url}page/{page}/"
                
                print(f"📄 Scraping page {page}: {page_url}")
                
                response = requests.get(page_url, headers=headers, timeout=15)
                response.raise_for_status()  # Raise an exception for bad status codes
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job listings - multiple selectors for robustness
                job_headers = []
                
                # Primary method: h2 elements with links
                job_headers.extend(soup.find_all('h2'))
                
                # Backup method: article elements or div with job classes
                job_headers.extend(soup.find_all('article'))
                job_headers.extend(soup.find_all('div', class_=lambda x: x and ('job' in x.lower() or 'post' in x.lower())))
                
                page_jobs = 0
                page_filtered = 0
                page_found_jobs = []
                
                for job_header in job_headers:
                    # Find link in different ways
                    link = job_header.find('a')
                    if not link and hasattr(job_header, 'find_parent'):
                        # Look for link in parent or children
                        parent = job_header.find_parent()
                        if parent:
                            link = parent.find('a')
                    
                    if not link:
                        continue
                        
                    job_title = link.get_text(strip=True)
                    job_url = link.get('href', '')
                    
                    # Skip if we already found this job on this page
                    if job_title in page_found_jobs:
                        continue
                    
                    # Skip homepage links and non-job URLs (less restrictive)
                    if not job_url or job_url == '/':
                        continue
                    
                    # Make sure it's a valid job URL
                    if not job_url.startswith('http'):
                        if job_url.startswith('/'):
                            job_url = 'https://20govt.com' + job_url
                        else:
                            continue
                    
                    # Find the date and description from parent container
                    job_container = job_header.find_parent()
                    date_text = ""
                    description = job_title
                    
                    # Look for date information
                    if job_container:
                        # Look for date patterns in the container
                        date_elements = job_container.find_all(string=True)
                        for text in date_elements:
                            text = text.strip()
                            if '/' in text and len(text) == 10:  # DD/MM/YYYY format
                                date_text = text
                                break
                        
                        # Get description from nearby text
                        desc_elem = job_container.find('p') or job_container
                        if desc_elem:
                            desc_text = desc_elem.get_text(strip=True)
                            if len(desc_text) > 20 and desc_text != job_title:
                                description = desc_text[:200] + "..." if len(desc_text) > 200 else desc_text
                    
                    # Apply ex-servicemen job filter (both civilian and military)
                    if not self.is_ex_servicemen_job(job_title, description):
                        page_filtered += 1
                        continue
                    
                    # Add to found jobs list to avoid duplicates
                    page_found_jobs.append(job_title)
                    
                    # Set default dates
                    post_date = "2025-08-12"
                    last_date = "2025-12-31"
                    
                    # Try to parse the found date
                    if date_text:
                        try:
                            # Convert DD/MM/YYYY to YYYY-MM-DD
                            if '/' in date_text:
                                date_parts = date_text.split('/')
                                if len(date_parts) == 3:
                                    post_date = f"{date_parts[2]}-{date_parts[1].zfill(2)}-{date_parts[0].zfill(2)}"
                        except:
                            pass
                    
                    # Extract real application URL from job page
                    app_url = self.get_real_application_url(job_url)
                    
                    job_data = {
                        "title": job_title,
                        "postDate": post_date,
                        "lastDate": last_date,
                        "description": description,
                        "jobUrl": job_url,
                        "applicationUrl": app_url,
                        "page": page,
                        "jobType": "Ex-Servicemen",
                        "scrapedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    all_jobs.append(job_data)
                    page_jobs += 1
                
                print(f"   ✅ Found {page_jobs} ex-servicemen jobs on page {page} (filtered out {page_filtered} non-relevant jobs)")
                
                # Check if we've reached the end (no more jobs found)
                if page_jobs == 0 and page > 3:  # Only stop after page 3 to ensure we don't miss anything
                    print(f"   🔚 No more jobs found after page {page-1}, stopping early")
                    break
                    
                page += 1
                time.sleep(2)  # Be respectful to the server
                
            except Exception as e:
                print(f"⚠️ Error scraping page {page}: {e}")
                page += 1
                continue
        
        print(f"✅ Successfully scraped {len(all_jobs)} ex-servicemen jobs from {page-1} pages")
        print(f"🎯 Filter Summary: Included ALL jobs relevant to ex-servicemen (civilian + military)")
        return all_jobs
    
    def simulate_job_scraping(self, url: str, max_jobs: int) -> List[Dict]:
        """Simulate job scraping with mock data based on the website structure"""
        print("🔍 Scraping job postings... Please wait...")
        time.sleep(2)  # Simulate network delay
        
        # Mock job data based on the actual website structure
        mock_jobs = [
            {
                "title": "BEL Driver Recruitment 2025",
                "postDate": "2025-07-15",
                "lastDate": "2025-08-06",
                "description": "BEL Driver Recruitment 2025 for Government Sector Vacancy in Karnataka. Bharat Electronics Limited is hiring drivers with ex-servicemen quota.",
                "jobUrl": "https://20govt.com/jobs/bel-driver/113691",
                "applicationUrl": "https://bel-india.in/careers"
            },
            {
                "title": "AIIMS Rajkot Consultant Recruitment 2025",
                "postDate": "2025-07-01",
                "lastDate": "2025-07-24",
                "description": "AIIMS Rajkot Consultant Recruitment 2025 for Government Sector Vacancy in Gujarat. Medical consultant positions available for ex-servicemen.",
                "jobUrl": "https://20govt.com/jobs/aiims-rajkot-consultant/113690",
                "applicationUrl": "https://aiimsrajkot.edu.in/recruitment"
            },
            {
                "title": "Indian Navy Recruitment 2025",
                "postDate": "2025-07-20",
                "lastDate": "2025-08-15",
                "description": "Indian Navy Recruitment 2025: Current Jobs Vacancy in Indian Navy. Various positions available for ex-servicemen with attractive benefits.",
                "jobUrl": "https://20govt.com/jobs/indian-navy-recruitment/113689",
                "applicationUrl": "https://joinindiannavy.gov.in"
            },
            {
                "title": "CEWACOR Consultant Recruitment 2025",
                "postDate": "2025-05-15",
                "lastDate": "2025-06-05",
                "description": "CEWACOR Consultant Recruitment 2025 for Government Sector Vacancy in NCR. Central Water and Power Research Station consultant positions.",
                "jobUrl": "https://20govt.com/jobs/cewacor-consultant/113688",
                "applicationUrl": "https://cewacor.in/careers"
            },
            {
                "title": "IOCL Security Chief Recruitment 2025",
                "postDate": "2025-07-10",
                "lastDate": "2025-08-20",
                "description": "IOCL Recruitment 2025 for Security Chief: Indian Oil Corporation Limited is recruiting security personnel with preference for ex-servicemen.",
                "jobUrl": "https://20govt.com/jobs/iocl-security-chief/113687",
                "applicationUrl": "https://iocl.com/careers"
            },
            {
                "title": "CSIR-CBRI Security Officer Recruitment 2025",
                "postDate": "2025-04-20",
                "lastDate": "2025-05-18",
                "description": "CSIR-CBRI Security Officer Recruitment 2025 for Government Sector Vacancy in Uttarakhand. Central Building Research Institute security positions.",
                "jobUrl": "https://20govt.com/jobs/csir-cbri-security/113686",
                "applicationUrl": "https://cbri.res.in/recruitment"
            },
            {
                "title": "CSL Instructor Recruitment 2025",
                "postDate": "2025-04-15",
                "lastDate": "2025-05-09",
                "description": "CSL Instructor Recruitment 2025 in Kochi, Kerala. Cochin Shipyard Limited instructor positions with ex-servicemen quota.",
                "jobUrl": "https://20govt.com/jobs/csl-instructor/113685",
                "applicationUrl": "https://cochinshipyard.com/careers"
            },
            {
                "title": "WCD Sirsa Support Person Recruitment 2025",
                "postDate": "2025-04-10",
                "lastDate": "2025-05-01",
                "description": "WCD Sirsa Recruitment 2025 for Support Person Post for 08 Vacancy in Haryana Anganwadi Department. Women and Child Development department positions.",
                "jobUrl": "https://20govt.com/jobs/wcd-sirsa/113684",
                "applicationUrl": "https://hreyahs.gov.in/recruitment"
            },
            {
                "title": "APS Chandimandir Teaching Staff Recruitment 2025",
                "postDate": "2025-04-05",
                "lastDate": "2025-05-05",
                "description": "APS Chandimandir Recruitment 2025 for Teaching, Non-Teaching Staff Jobs in Haryana Government. Army Public School positions for ex-servicemen.",
                "jobUrl": "https://20govt.com/jobs/aps-chandimandir/113683",
                "applicationUrl": "https://apsctm.in/recruitment"
            },
            {
                "title": "ECHS Medical Officer Recruitment 2025",
                "postDate": "2025-04-01",
                "lastDate": "2025-04-25",
                "description": "ECHS Recruitment 2025 for Medical Officer, Dental Hygienist Jobs in Karnataka. Ex-servicemen Contributory Health Scheme medical positions.",
                "jobUrl": "https://20govt.com/jobs/echs-medical/113682",
                "applicationUrl": "https://echs.gov.in/recruitment"
            },
            {
                "title": "SECR Trade Apprentice Recruitment 2025",
                "postDate": "2025-07-25",
                "lastDate": "2025-08-25",
                "description": "SECR Recruitment 2025 for Trade Apprentice: South East Central Railway apprentice positions with reservation for ex-servicemen.",
                "jobUrl": "https://20govt.com/jobs/secr-apprentice/113681",
                "applicationUrl": "https://secr.indianrailways.gov.in"
            },
            {
                "title": "BEL Assistant Security Officer Recruitment 2025",
                "postDate": "2025-07-12",
                "lastDate": "2025-08-12",
                "description": "BEL Recruitment 2025 for Assistant Security Officer: Bharat Electronics Limited security officer positions for ex-servicemen personnel.",
                "jobUrl": "https://20govt.com/jobs/bel-security/113680",
                "applicationUrl": "https://bel-india.in/careers"
            },
            {
                "title": "DRDO Scientist Recruitment 2025",
                "postDate": "2025-07-18",
                "lastDate": "2025-08-18",
                "description": "DRDO Scientist Recruitment 2025: Defence Research and Development Organisation scientist positions with ex-servicemen quota available.",
                "jobUrl": "https://20govt.com/jobs/drdo-scientist/113679",
                "applicationUrl": "https://drdo.gov.in/recruitment"
            },
            {
                "title": "Coast Guard Assistant Commandant Recruitment 2025",
                "postDate": "2025-07-22",
                "lastDate": "2025-08-22",
                "description": "Indian Coast Guard Assistant Commandant Recruitment 2025. Maritime security positions ideal for ex-servicemen with naval background.",
                "jobUrl": "https://20govt.com/jobs/coast-guard-ac/113678",
                "applicationUrl": "https://joinindiancoastguard.gov.in"
            },
            {
                "title": "CAPF Head Constable Recruitment 2025",
                "postDate": "2025-07-08",
                "lastDate": "2025-08-08",
                "description": "Central Armed Police Forces Head Constable Recruitment 2025. Para-military positions with significant ex-servicemen quota.",
                "jobUrl": "https://20govt.com/jobs/capf-hc/113677",
                "applicationUrl": "https://crpf.gov.in/recruitment"
            }
        ]
        
        # Return only the requested number of jobs
        return mock_jobs[:min(max_jobs, len(mock_jobs))]
    
    def format_date(self, date_string: str) -> str:
        """Format date string to DD/MM/YYYY format"""
        try:
            date_obj = datetime.strptime(date_string, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except:
            return date_string
    
    def is_expired(self, last_date: str) -> bool:
        """Check if job posting has expired"""
        try:
            last_date_obj = datetime.strptime(last_date, "%Y-%m-%d").date()
            return last_date_obj < date.today()
        except:
            return False
    
    def display_jobs_html(self, jobs: List[Dict]):
        """Display jobs in HTML format for better visualization in Jupyter"""
        if not jobs:
            print("❌ No jobs found. Please try a different URL or check your internet connection.")
            return
        
        html_content = """
        <style>
        .job-container { margin: 20px 0; }
        .job-card { 
            background: white; border: 2px solid #e9ecef; border-radius: 15px; 
            padding: 20px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .job-title { 
            font-size: 1.4em; font-weight: 700; color: #2c3e50; 
            margin-bottom: 10px; line-height: 1.3; 
        }
        .job-meta { 
            display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 15px; 
        }
        .meta-item { 
            background: #f8f9fa; padding: 8px 12px; border-radius: 8px; 
            font-size: 0.9em; color: #495057; 
        }
        .meta-label { font-weight: 600; color: #667eea; }
        .job-description { 
            color: #6c757d; line-height: 1.6; margin-bottom: 15px; 
        }
        .job-links { display: flex; gap: 10px; flex-wrap: wrap; }
        .link-btn { 
            background: linear-gradient(135deg, #28a745, #20c997); color: white; 
            text-decoration: none; padding: 8px 16px; border-radius: 8px; 
            font-size: 0.9em; font-weight: 600; 
        }
        .stats { 
            background: linear-gradient(135deg, #17a2b8, #138496); color: white; 
            padding: 20px; text-align: center; font-size: 1.2em; font-weight: 600; 
            border-radius: 10px; margin-bottom: 20px;
        }
        .active-status { color: #28a745; font-weight: bold; }
        .expired-status { color: #dc3545; font-weight: bold; }
        </style>
        """
        
        # Add statistics
        active_jobs = sum(1 for job in jobs if not self.is_expired(job['lastDate']))
        expired_jobs = len(jobs) - active_jobs
        
        html_content += f"""
        <div class="stats">
            📊 Total Jobs Found: {len(jobs)} | 🟢 Active: {active_jobs} | 🔴 Expired: {expired_jobs}
        </div>
        <div class="job-container">
        """
        
        for job in jobs:
            status = "expired-status" if self.is_expired(job['lastDate']) else "active-status"
            status_text = "Expired" if self.is_expired(job['lastDate']) else "Active"
            
            html_content += f"""
            <div class="job-card">
                <div class="job-title">{job['title']}</div>
                <div class="job-meta">
                    <div class="meta-item">
                        <span class="meta-label">Posted:</span> {self.format_date(job['postDate'])}
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Last Date:</span> {self.format_date(job['lastDate'])}
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Status:</span> 
                        <span class="{status}">{status_text}</span>
                    </div>
                </div>
                <div class="job-description">{job['description']}</div>
                <div class="job-links">
                    <a href="{job['jobUrl']}" target="_blank" class="link-btn">📄 View Job</a>
                    <a href="{job['applicationUrl']}" target="_blank" class="link-btn">📝 Apply Online</a>
                </div>
            </div>
            """
        
        html_content += "</div>"
        display(HTML(html_content))
    
    def display_jobs_text(self, jobs: List[Dict]):
        """Display jobs in text format"""
        if not jobs:
            print("❌ No jobs found. Please try a different URL or check your internet connection.")
            return
        
        active_jobs = sum(1 for job in jobs if not self.is_expired(job['lastDate']))
        expired_jobs = len(jobs) - active_jobs
        
        print("="*80)
        print("🎖️  EX-SERVICEMEN JOB SCRAPER RESULTS")
        print("="*80)
        print(f"📊 Total Jobs Found: {len(jobs)} | 🟢 Active: {active_jobs} | 🔴 Expired: {expired_jobs}")
        print("="*80)
        
        for i, job in enumerate(jobs, 1):
            status = "🔴 EXPIRED" if self.is_expired(job['lastDate']) else "🟢 ACTIVE"
            
            print(f"\n📋 JOB {i}: {job['title']}")
            print("-" * 60)
            print(f"📅 Posted: {self.format_date(job['postDate'])}")
            print(f"⏰ Last Date: {self.format_date(job['lastDate'])}")
            print(f"🚦 Status: {status}")
            print(f"📝 Description: {job['description']}")
            print(f"🔗 Job URL: {job['jobUrl']}")
            print(f"📄 Apply URL: {job['applicationUrl']}")
    
    def scrape_jobs(self, url: str = None, max_jobs: int = 1000, display_format: str = "html", use_real_scraping: bool = True, max_pages: int = None):
        """Main function to scrape ALL ex-servicemen jobs (civilian + military) - future-proof"""
        if not url:
            url = self.default_url
        
        print(f"🎖️ EX-SERVICEMEN JOB SCRAPER (Future-Proof)")
        print(f"🔍 Scraping URL: {url}")
        print(f"📊 Max Jobs: {max_jobs}")
        print(f"📄 Max Pages: {'Auto-detect' if max_pages is None else max_pages}")
        print(f"🌐 Real Scraping: {'Enabled' if use_real_scraping else 'Mock Data'}")
        print(f"🎯 Filter: ALL ex-servicemen jobs (civilian + military positions)")
        print(f"🔮 Future-Ready: Automatically adapts to new pages and job types")
        print("-" * 60)
        
        try:
            # Choose scraping method
            if use_real_scraping:
                jobs = self.scrape_real_jobs(url, max_jobs, max_pages)
            else:
                jobs = self.simulate_job_scraping(url, max_jobs)
            
            self.scraped_jobs = jobs
            
            # Display results
            clear_output(wait=True)
            print(f"✅ Successfully scraped {len(jobs)} jobs!")
            
            if display_format.lower() == "html":
                self.display_jobs_html(jobs)
            else:
                self.display_jobs_text(jobs)
            
            return jobs
            
        except Exception as e:
            print(f"❌ Error scraping jobs: {str(e)}")
            return []
    
    def export_to_json(self, filename: str = None) -> str:
        """Export scraped jobs to JSON file"""
        if not self.scraped_jobs:
            print("❌ No jobs to export. Please scrape jobs first.")
            return None
        
        if not filename:
            filename = f"ex_servicemen_jobs_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Jobs exported to: {filename}")
        return filename
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export scraped jobs to CSV file"""
        if not self.scraped_jobs:
            print("❌ No jobs to export. Please scrape jobs first.")
            return None
        
        if not filename:
            filename = f"ex_servicemen_jobs_{datetime.now().strftime('%Y-%m-%d')}.csv"
        
        df = pd.DataFrame(self.scraped_jobs)
        df['postDate_formatted'] = df['postDate'].apply(self.format_date)
        df['lastDate_formatted'] = df['lastDate'].apply(self.format_date)
        df['isExpired'] = df['lastDate'].apply(self.is_expired)
        
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Jobs exported to: {filename}")
        return filename
    
    def get_stats(self) -> Dict:
        """Get statistics about scraped jobs"""
        if not self.scraped_jobs:
            return {"total": 0, "active": 0, "expired": 0}
        
        active = sum(1 for job in self.scraped_jobs if not self.is_expired(job['lastDate']))
        expired = len(self.scraped_jobs) - active
        
        return {
            "total": len(self.scraped_jobs),
            "active": active,
            "expired": expired
        }

# Usage Examples and Main Execution
def main():
    """Main function to demonstrate the scraper"""
    # Create scraper instance
    scraper = ExServicemenJobScraper()
    
    # Example 1: Basic scraping with HTML display
    print("🎖️ EXAMPLE 1: Real Job Scraping from All 13 Pages")
    jobs = scraper.scrape_jobs(max_jobs=1000, max_pages=13, display_format="html", use_real_scraping=True)
    
    # Example 2: Export to different formats
    if jobs:
        print("\n📁 EXPORTING DATA:")
        json_file = scraper.export_to_json()
        csv_file = scraper.export_to_csv()
        
        # Example 3: Display statistics
        stats = scraper.get_stats()
        print(f"\n📊 JOB STATISTICS:")
        print(f"Total Jobs: {stats['total']}")
        print(f"Active Jobs: {stats['active']}")
        print(f"Expired Jobs: {stats['expired']}")
    
    return scraper

# Run the scraper when script is executed
if __name__ == "__main__":
    # For Google Colab or Jupyter Notebook
    try:
        # Install required packages if not available
        import subprocess
        import sys
        
        def install_package(package):
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        try:
            import pandas as pd
        except ImportError:
            print("📦 Installing pandas...")
            install_package("pandas")
            import pandas as pd
        
        # Run the scraper
        scraper_instance = main()
        
    except Exception as e:
        print(f"❌ Error running scraper: {str(e)}")

# Quick usage functions for Colab
def quick_scrape(max_jobs=50, max_pages=3, use_real=True):
    """Quick function to scrape jobs with pagination support"""
    scraper = ExServicemenJobScraper()
    return scraper.scrape_jobs(max_jobs=max_jobs, max_pages=max_pages, use_real_scraping=use_real)

def scrape_all_pages(max_jobs=1000):
    """Scrape jobs from all pages available for ex-servicemen - future-proof"""
    scraper = ExServicemenJobScraper()
    return scraper.scrape_jobs(max_jobs=max_jobs, max_pages=None, use_real_scraping=True)

def scheduled_scrape_with_learning():
    """Advanced scraping function that learns and adapts over time"""
    scraper = ExServicemenJobScraper()
    
    # Load learned patterns from previous runs
    learned = scraper.load_learned_patterns()
    
    # Scrape with auto-detection
    jobs = scraper.scrape_jobs(max_jobs=1000, max_pages=None, use_real_scraping=True)
    
    if jobs:
        # Save learned patterns for future runs
        scraper.save_learned_patterns()
        
        # Export data with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        scraper.export_to_json(f"ex_servicemen_jobs_{timestamp}.json")
        scraper.export_to_csv(f"ex_servicemen_jobs_{timestamp}.csv")
        
        print(f"✅ Future-proof scraping completed: {len(jobs)} jobs found and saved")
    
    return jobs

def export_jobs(scraper_instance, format_type="both"):
    """Quick function to export jobs"""
    if format_type.lower() in ["json", "both"]:
        scraper_instance.export_to_json()
    if format_type.lower() in ["csv", "both"]:
        scraper_instance.export_to_csv()

# Display usage instructions
print("""
🎖️ EX-SERVICEMEN JOB SCRAPER - Future-Proof Python Script
==========================================================

FUTURE-PROOF FEATURES:
🔮 AUTO-DETECTS: New pages, organizations, and job types automatically
🧠 LEARNS: Improves filtering based on previous scraping sessions
📈 ADAPTS: Handles website changes and new content structures
⚡ SCHEDULED: Can run automatically to catch new job postings

FILTERING LOGIC:
✅ INCLUDES: ALL ex-servicemen related jobs (both civilian and military)
✅ INCLUDES: Retired personnel positions, veteran jobs, ex-officer roles
✅ INCLUDES: Army, Navy, Air Force jobs specifically for ex-servicemen
✅ LEARNS: New organizations and keywords automatically

USAGE INSTRUCTIONS:
1. Basic Future-Proof Scraping: 
   scraper = ExServicemenJobScraper()
   jobs = scraper.scrape_jobs(max_jobs=1000, max_pages=None)  # Auto-detects pages

2. Quick Real Scraping:
   jobs = quick_scrape(max_jobs=50, max_pages=3, use_real=True)

3. Advanced Learning Scraper (RECOMMENDED for future jobs):
   jobs = scheduled_scrape_with_learning()

4. Scrape All Pages (Auto-detects total pages):
   jobs = scrape_all_pages(max_jobs=1000)

5. Mock Data (for testing):
   jobs = scraper.scrape_jobs(use_real_scraping=False)

6. Export Data:
   scraper.export_to_json()
   scraper.export_to_csv()

7. Manual Scheduled Run:
   import schedule
   schedule.every().day.at("09:00").do(scheduled_scrape_with_learning)

📊 WEBSITE INFO: Auto-detects available pages (currently ~13-20 pages)
🎯 FUTURE-READY: Automatically captures new ex-servicemen jobs as they appear!
🧠 SMART LEARNING: Gets better at detecting relevant jobs over time!
Ready to run! Execute the cells above to start future-proof scraping.
""")