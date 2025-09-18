#!/usr/bin/env python3
"""
Fixed Job Scraper for CGResettlement.com with relative paths
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
from pathlib import Path

# Get the current directory where the script is located
CURRENT_DIR = Path(__file__).parent
OUTPUT_FILE = CURRENT_DIR / "jobs_with_dates.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.base_url = "https://www.cgresettlement.com"
        self.delay = 2  # Delay between requests to be respectful
        
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page with retry logic"""
        for attempt in range(retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Check if we got redirected or blocked
                if "blocked" in response.url.lower() or response.status_code == 403:
                    logger.warning(f"Possible blocking detected for {url}")
                    time.sleep(self.delay * 2)
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                time.sleep(self.delay)  # Be respectful
                return soup
                
            except requests.RequestException as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
        
        return None
    
    def extract_job_listings(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """Extract job listings from a page"""
        jobs = []
        found_urls = set()  # Track URLs to avoid duplicates within the same page
        
        # Look for common job listing selectors (in order of preference)
        job_selectors = [
            'a[href*="/job/"]',  # Most specific - links containing /job/
            '.job-item a',
            '.job-listing a',
            '.job-card a',
            '.listing-item a',
            '[class*="job"] a',
            'tr[class*="row"] a',
            '.table tbody tr a',
            'div[class*="list"] div[class*="item"] a'
        ]
        
        job_elements = []
        for selector in job_selectors:
            elements = soup.select(selector)
            if elements:
                job_elements = elements
                logger.info(f"Found {len(elements)} job links using selector: {selector}")
                break
        
        # If no specific selectors work, try to find links that look like job URLs
        if not job_elements:
            # Look for links containing job-related keywords
            all_links = soup.find_all('a', href=True)
            job_links = []
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if (('/job' in href.lower() or '/vacancy' in href.lower()) and text and len(text) > 5):
                    job_links.append(link)
            
            if job_links:
                logger.info(f"Found {len(job_links)} potential job links")
                job_elements = job_links
        
        for element in job_elements:
            try:
                job_data = self.extract_job_from_element(element, category)
                if job_data and job_data['view_url'] not in found_urls:
                    found_urls.add(job_data['view_url'])
                    jobs.append(job_data)
            except Exception as e:
                logger.error(f"Error extracting job from element: {e}")
                continue
        
        logger.info(f"Extracted {len(jobs)} unique jobs from this page")
        return jobs
    
    def extract_job_from_element(self, element, category: str) -> Optional[Dict]:
        """Extract job data from a single element"""
        job = {
            'title': '',
            'category': category,
            'view_url': '',
            'apply_link': '',
            'description': '',
            'posted_date': '',
            'deadline': ''
        }
        
        # Extract title (will be updated later from detail page)
        if element.name == 'a':
            # If element is a link itself
            title = element.get_text(strip=True)
            href = element.get('href')
        else:
            # Look for title and link within element
            title_elem = element.find('a') or element.find(['h1', 'h2', 'h3', 'h4', '.title', '.job-title'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title_elem.name == 'a':
                    href = title_elem.get('href')
                else:
                    link_elem = element.find('a', href=True)
                    href = link_elem.get('href') if link_elem else ''
            else:
                return None
        
        if title and href and len(title) > 3:
            job['title'] = title
            job['view_url'] = urljoin(self.base_url, href)
            return job
        
        return None
    
    def get_full_title_from_detail_page(self, view_url: str) -> str:
        """
        FIX #1: Get full job title from detail page to fix truncated titles
        """
        soup = self.get_page(view_url)
        if not soup:
            return ""
        
        # Look for the main job title on the detail page
        title_selectors = [
            'h1',
            '.job-title',
            '[class*="title"]:first-of-type',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                full_title = title_elem.get_text(strip=True)
                # Clean up title - remove site name and extra content
                if ' | ' in full_title:
                    full_title = full_title.split(' | ')[0].strip()
                if 'cgresettlement' not in full_title.lower() and len(full_title) > 5:
                    return full_title
        
        return ""
    
    def construct_apply_link_from_job_url(self, view_url: str) -> str:
        """
        FIX #2: Construct proper apply link from job URL
        Format: https://www.cgresettlement.com/login?redirect=/job/<slug>
        """
        try:
            parsed_url = urlparse(view_url)
            job_path = parsed_url.path  # e.g., '/job/junior-engineer-lineman-gssc'
            
            if job_path.startswith('/job/'):
                apply_link = f"{self.base_url}/login?redirect={job_path}"
                return apply_link
            else:
                logger.warning(f"Unexpected job URL format: {view_url}")
                return f"{self.base_url}/login"
                
        except Exception as e:
            logger.error(f"Error constructing apply link for {view_url}: {e}")
            return f"{self.base_url}/login"
    
    def extract_dates_from_detail_page(self, soup: BeautifulSoup) -> tuple[str, str]:
        """
        Extract posted date and deadline from job detail page
        Returns: (posted_date, deadline)
        """
        posted_date = ""
        deadline = ""
        
        # FIRST: Look for structured date information in specific elements
        # This handles the sidebar job info like "Last date to apply: 02/08/2025"
        
        # Look for specific date fields in the job information section
        # First try direct text search in page content
        page_text = soup.get_text(separator=' ', strip=True)
        
        # Handle "Last date to apply: DD/MM/YYYY" pattern specifically
        last_date_pattern = r'Last date to apply:\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
        last_date_match = re.search(last_date_pattern, page_text, re.IGNORECASE)
        if last_date_match and not deadline:
            deadline = self.normalize_date(last_date_match.group(1))
            logger.debug(f"Found deadline from 'Last date to apply': {deadline}")
        
        # Handle "Posted X days ago" pattern
        posted_days_pattern = r'Posted\s+(\d+)\s+days?\s+ago'
        posted_days_match = re.search(posted_days_pattern, page_text, re.IGNORECASE)
        if posted_days_match and not posted_date:
            days_ago = int(posted_days_match.group(1))
            posted_date_obj = datetime.now() - timedelta(days=days_ago)
            posted_date = posted_date_obj.strftime('%Y-%m-%d')
            logger.debug(f"Found posted date from 'Posted X days ago': {posted_date}")
        
        # Look for direct "Posted: DD/MM/YYYY" pattern
        posted_date_pattern = r'Posted(?:\s+date)?:\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
        posted_date_match = re.search(posted_date_pattern, page_text, re.IGNORECASE)
        if posted_date_match and not posted_date:
            posted_date = self.normalize_date(posted_date_match.group(1))
            logger.debug(f"Found posted date from direct pattern: {posted_date}")
        
        # Look for "Start Date to apply online" pattern (common in Indian govt notifications)
        start_date_pattern = r'Start Date to apply online[:\s\-–]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
        start_date_match = re.search(start_date_pattern, page_text, re.IGNORECASE)
        if start_date_match and not posted_date:
            posted_date = self.normalize_date(start_date_match.group(1))
            logger.debug(f"Found posted date from start date pattern: {posted_date}")
        
        # Look for "Notification जारी:" pattern (Hindi notifications)
        notification_pattern = r'Notification\s+जारी:\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
        notification_match = re.search(notification_pattern, page_text, re.IGNORECASE)
        if notification_match and not posted_date:
            posted_date = self.normalize_date(notification_match.group(1))
            logger.debug(f"Found posted date from notification pattern: {posted_date}")
        
        # Look in HTML elements for structured data (avoiding :contains which may not work)
        date_info_selectors = [
            '.job-info', '.job-details', '.sidebar', '.info-section', 
            'td', 'th', 'div', 'span', 'p'
        ]
        
        # Extract dates from structured elements
        for selector in date_info_selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(separator=' ', strip=True)
                    
                    # Look for "Last date to apply" pattern
                    if 'last date' in text.lower() and 'apply' in text.lower() and not deadline:
                        date_match = re.search(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})', text)
                        if date_match:
                            deadline = self.normalize_date(date_match.group(1))
                            logger.debug(f"Found deadline from HTML element: {deadline}")
                    
                    # Look for "Posted" pattern  
                    if 'posted' in text.lower() and not posted_date:
                        # First check for "Posted X days ago"
                        days_match = re.search(r'posted\s+(\d+)\s+days?\s+ago', text, re.IGNORECASE)
                        if days_match:
                            days_ago = int(days_match.group(1))
                            posted_date_obj = datetime.now() - timedelta(days=days_ago)
                            posted_date = posted_date_obj.strftime('%Y-%m-%d')
                            logger.debug(f"Found posted date from element (days ago): {posted_date}")
                        else:
                            # Look for direct date
                            date_match = re.search(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})', text)
                            if date_match:
                                posted_date = self.normalize_date(date_match.group(1))
                                logger.debug(f"Found posted date from HTML element: {posted_date}")
            except Exception as e:
                logger.debug(f"Error processing selector {selector}: {e}")
                continue
        
        # If we found dates from structure, return them
        if posted_date or deadline:
            return posted_date, deadline
        
        # FALLBACK: Get all text content for date parsing (original method)
        page_text = soup.get_text(separator=' ', strip=True)
        
        # Enhanced date patterns for Indian format dates
        date_patterns = [
            r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})',      # DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
            r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})',      # YYYY-MM-DD, YYYY/MM/DD
            r'(\d{1,2}\s+[\u0900-\u097F]+\s+\d{4})',  # DD Month YYYY (Hindi months)
            r'(\d{1,2}\s+\w+\s+\d{4})',               # DD Month YYYY (English months)
            r'(\w+\s+\d{1,2},?\s+\d{4})',             # Month DD, YYYY
            r'(\d{1,2}‑\d{1,2}‑\d{4})',               # DD‑MM‑YYYY (en-dash)
            r'(\d{1,2}\s*-\s*\d{1,2}\s*-\s*\d{4})',   # DD - MM - YYYY (with spaces)
            r'(\d{1,2}st|nd|rd|th\s+\w+\s+\d{4})',    # 1st January 2025
        ]
        
        # Enhanced keywords for Indian government notifications
        posted_keywords = [
            'notification जारी', 'published', 'posted', 'notification released',
            'जारी', 'released', 'announced', 'advertised', 'issued',
            'notification date', 'published on', 'released on', 'जारी की गई',
            'अधिसूचना जारी', 'भर्ती जारी', 'recruitment released',
            'start date to apply online', 'online application शुरू', 'आवेदन प्रारंभ',
            'notification जारी:', 'start date to apply', 'आवेदन प्रारंभ :',
            'online आवेदन शुरू', 'notification जारी :', 'notification date:'
        ]
        
        deadline_keywords = [
            'last date', 'अंतिम तिथि', 'deadline', 'closing date', 'apply by',
            'application deadline', 'final date', 'अंतिम दिनांक', 'last day',
            'आवेदन की अंतिम तिथि', 'अंतिम तारीख', 'registration closes',
            'apply till', 'apply before', 'अंतिम दिन', 'last date to apply',
            'online registration', 'application close', 'submit by',
            'last date to apply online', 'अंतिम तिथि:', 'last date to apply:',
            'आवेदन अंतिम तिथि', 'apply online:', 'registration deadline',
            'अंतिम तिथि :', 'अंतिम तारीख :', 'last date:',
            'application last date', 'अंतिम दिनांक :', 'final date:',
            'करने की तिथि', 'submit करने की तिथि', 'की तिथि:', 'तक)', 'से', 'तक'
        ]
        
        # Store potential dates with their context to avoid overlap
        date_candidates = []
        
        # Extract all possible dates with their positions and context
        for pattern in date_patterns:
            matches = re.finditer(pattern, page_text, re.IGNORECASE)
            for match in matches:
                date_text = match.group(1)
                start_pos = match.start()
                
                # Get context around the date (300 characters before and after)
                context_start = max(0, start_pos - 300)
                context_end = min(len(page_text), start_pos + 300)
                context = page_text[context_start:context_end].lower()
                
                normalized_date = self.normalize_date(date_text)
                if normalized_date:
                    date_candidates.append({
                        'date': normalized_date,
                        'raw_date': date_text,
                        'context': context,
                        'position': start_pos
                    })
        
        # Sort candidates by position to process in order of appearance
        date_candidates.sort(key=lambda x: x['position'])
        
        # Assign dates based on context
        for candidate in date_candidates:
            context = candidate['context']
            normalized_date = candidate['date']
            
            # Check if this date is related to posting
            if any(keyword in context for keyword in posted_keywords) and not posted_date:
                posted_date = normalized_date
                logger.debug(f"Found posted date from context: {candidate['raw_date']} -> {posted_date}")
                continue
            
            # Check if this date is related to deadline
            if any(keyword in context for keyword in deadline_keywords) and not deadline:
                deadline = normalized_date
                logger.debug(f"Found deadline from context: {candidate['raw_date']} -> {deadline}")
                continue
        
        # Special logic for date ranges (e.g., "22-07-2025 से 21-08-2025")
        # If we have multiple dates but no clear deadline, look for the latest date in a range pattern
        if posted_date and not deadline and len(date_candidates) > 1:
            # Look for range patterns like "date1 से date2" or "date1 to date2"
            for i, candidate in enumerate(date_candidates):
                context = candidate['context']
                # Check if this date is part of a range and is the later date
                if 'से' in context or 'to' in context:
                    # Find all dates in this context and pick the latest one as deadline
                    context_dates = [c['date'] for c in date_candidates if abs(c['position'] - candidate['position']) < 50]
                    if len(context_dates) > 1:
                        latest_date = max(context_dates)
                        if latest_date != posted_date:
                            deadline = latest_date
                            logger.debug(f"Found deadline from range pattern: {latest_date}")
                            break
        
        # Special handling for DSSSB-style notifications
        if not posted_date or not deadline:
            found_posted, found_deadline = self.handle_dsssb_style_dates(page_text, date_candidates, posted_date, deadline)
            if not posted_date and found_posted:
                posted_date = found_posted
            if not deadline and found_deadline:
                deadline = found_deadline
        
        # If only one date was found, determine if it's more likely a posted date or deadline
        if len(date_candidates) == 1 and (posted_date or deadline) and not (posted_date and deadline):
            single_date = posted_date or deadline
            single_candidate = date_candidates[0]
            context = single_candidate['context']
            
            # Check if context suggests it's a deadline
            is_deadline_context = any(keyword in context for keyword in deadline_keywords)
            is_posted_context = any(keyword in context for keyword in posted_keywords)
            
            if is_deadline_context and not is_posted_context:
                # It's clearly a deadline, leave posted_date empty or estimate it
                deadline = single_date
                posted_date = ""
                logger.debug(f"Single date identified as deadline: {deadline}")
            elif is_posted_context and not is_deadline_context:
                # It's clearly a posted date, leave deadline empty
                posted_date = single_date
                deadline = ""
                logger.debug(f"Single date identified as posted date: {posted_date}")
        
        # Final validation: ensure posted_date is not after deadline
        if posted_date and deadline:
            try:
                posted_dt = datetime.strptime(posted_date, '%Y-%m-%d')
                deadline_dt = datetime.strptime(deadline, '%Y-%m-%d')
                if posted_dt > deadline_dt:
                    # Check if this makes sense - don't swap if deadline is "Announced Soon" equivalent
                    if deadline != "":
                        logger.warning(f"Date order issue: posted_date ({posted_date}) is after deadline ({deadline})")
                        # Only swap if deadline is not empty and seems reasonable
                        # Otherwise, clear the problematic deadline
                        deadline = ""
                        logger.warning(f"Cleared problematic deadline, keeping posted_date: {posted_date}")
            except ValueError:
                pass
        
        # Additional validation: if we have "Announced Soon" or similar, clear deadline
        if deadline and any(word in page_text.lower() for word in ['announced soon', 'to be announced', 'will be announced']):
            deadline = ""
            logger.debug("Cleared deadline due to 'Announced Soon' text")
        
        return posted_date, deadline
    
    def extract_dates_from_common_patterns(self, text: str) -> tuple[str, str]:
        """Extract dates from common notification patterns"""
        posted_date = ""
        deadline = ""
        
        # Pattern: "Online Registration 01.08.2025 – 21.08.2025"
        registration_pattern = r'online\s+registration[:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})\s*[–\-]\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})'
        match = re.search(registration_pattern, text, re.IGNORECASE)
        if match:
            start_date = self.normalize_date(match.group(1))
            end_date = self.normalize_date(match.group(2))
            if not posted_date and start_date:
                posted_date = start_date
            if not deadline and end_date:
                deadline = end_date
        
        # Pattern: "Application Dates: Start Date ... Last Date ..."
        app_dates_pattern = r'application\s+dates:.*?(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4}).*?(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})'
        match = re.search(app_dates_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            if not posted_date:
                posted_date = self.normalize_date(match.group(1))
            if not deadline:
                deadline = self.normalize_date(match.group(2))
        
        return posted_date, deadline
    
    def extract_dates_from_structure(self, soup: BeautifulSoup) -> tuple[str, str]:
        """Extract dates from structured elements like tables or specific classes"""
        posted_date = ""
        deadline = ""
        
        # Look for structured date information in tables or divs
        date_selectors = [
            'table td', 'table th', '.date', '.dates', '[class*="date"]',
            '.info', '[class*="info"]', '.details td', '.application-dates'
        ]
        
        for selector in date_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                
                # Check for date patterns in structured elements
                if any(keyword in text.lower() for keyword in ['notification', 'जारी', 'published', 'released']):
                    date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', text)
                    if date_match and not posted_date:
                        posted_date = self.normalize_date(date_match.group(1))
                
                if any(keyword in text.lower() for keyword in ['last date', 'अंतिम', 'deadline', 'closing']):
                    date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', text)
                    if date_match and not deadline:
                        deadline = self.normalize_date(date_match.group(1))
        
        return posted_date, deadline
    
    def handle_dsssb_style_dates(self, page_text, date_candidates, current_posted, current_deadline):
        """Handle DSSSB-style date formats and notification patterns"""
        posted_date = current_posted
        deadline = current_deadline
        
        # Look for specific DSSSB patterns
        dsssb_patterns = [
            r'notification\s+dated?\s*:?\s*([^\s\n]+)',
            r'notification\s+no\.?\s*[^\s]+\s+dated?\s*:?\s*([^\s\n]+)',
            r'advt\.?\s+no\.?\s*[^\s]+\s+dated?\s*:?\s*([^\s\n]+)',
            r'पोस्ट\s+कोड\s*:?\s*[^\s]+\s+दिनांक\s*:?\s*([^\s\n]+)',
        ]
        
        for pattern in dsssb_patterns:
            matches = re.finditer(pattern, page_text, re.IGNORECASE)
            for match in matches:
                date_text = match.group(1)
                normalized_date = self.normalize_date(date_text)
                if normalized_date and not posted_date:
                    posted_date = normalized_date
                    break
        
        return posted_date, deadline
    
    def normalize_date(self, date_str: str) -> str:
        """Normalize date to a standard format (YYYY-MM-DD)"""
        if not date_str:
            return ""
        
        try:
            # Clean the date string
            date_str = date_str.strip().replace('‑', '-').replace('–', '-')  # Replace en-dash with hyphen
            
            # Try different date formats commonly used in Indian notifications
            date_formats = [
                '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y',  # DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
                '%Y-%m-%d', '%Y/%m/%d',               # YYYY-MM-DD, YYYY/MM/DD
                '%d %B %Y', '%d %b %Y',               # DD Month YYYY, DD Mon YYYY
                '%B %d, %Y', '%b %d, %Y',             # Month DD, YYYY
                '%d-%m-%y', '%d/%m/%y',               # DD-MM-YY, DD/MM/YY
                '%Y-%m-%d', '%Y/%m/%d',               # YYYY-MM-DD
                '%d %B, %Y', '%d %b, %Y',             # DD Month, YYYY
                '%dst %B %Y', '%dnd %B %Y', '%drd %B %Y', '%dth %B %Y',  # 1st January 2025
            ]
            
            for fmt in date_formats:
                try:
                    # Handle ordinal numbers (1st, 2nd, 3rd, 4th, etc.)
                    if 'st' in fmt or 'nd' in fmt or 'rd' in fmt or 'th' in fmt:
                        clean_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
                        parsed_date = datetime.strptime(clean_date, fmt.replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
                    else:
                        parsed_date = datetime.strptime(date_str, fmt)
                    
                    # Convert 2-digit years to 4-digit (assume 2000-2099)
                    if parsed_date.year < 100:
                        if parsed_date.year > 50:
                            parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                        else:
                            parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                    
                    return parsed_date.strftime('%Y-%m-%d')
                    
                except ValueError:
                    continue
            
            # Try manual parsing for some common Indian formats
            # Format: "21-08-2025" or "21/08/2025"
            simple_pattern = r'(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})'
            match = re.match(simple_pattern, date_str)
            if match:
                day, month, year = match.groups()
                try:
                    parsed_date = datetime(int(year), int(month), int(day))
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            
            # If no format works, return the original string
            return date_str.strip()
            
        except Exception as e:
            logger.debug(f"Error normalizing date '{date_str}': {e}")
            return date_str.strip()

    def get_job_details(self, job: Dict) -> Dict:
        """Fetch detailed job description and apply correct title/apply_link"""
        view_url = job['view_url']
        
        # FIX #1: Get full title from detail page
        full_title = self.get_full_title_from_detail_page(view_url)
        if full_title and len(full_title) > len(job['title']):
            logger.info(f"Updated title from '{job['title']}' to '{full_title}'")
            job['title'] = full_title
        
        # FIX #2: Construct proper apply link
        job['apply_link'] = self.construct_apply_link_from_job_url(view_url)
        
        # Get description and dates
        soup = self.get_page(view_url)
        if soup:
            job['description'] = self.extract_description(soup)
            
            # NEW: Extract posted date and deadline
            posted_date, deadline = self.extract_dates_from_detail_page(soup)
            job['posted_date'] = posted_date
            job['deadline'] = deadline
            
            if posted_date:
                logger.debug(f"Found posted date: {posted_date}")
            if deadline:
                logger.debug(f"Found deadline: {deadline}")
        
        return job
    
    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract clean job description from detail page"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Look for description content
        desc_selectors = [
            '.job-description',
            '.description',
            '.content',
            '.details',
            '[class*="desc"]',
            '.job-detail',
            'main',
            'body'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(strip=True, separator=' ')
                if description and len(description) > 50:
                    # Clean up description
                    description = re.sub(r'\s+', ' ', description)
                    return description[:2000]  # Limit length
        
        return ""
    
    def get_pagination_urls(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract pagination URLs from the current page"""
        urls = []
        
        # Look for pagination elements
        pagination_selectors = [
            '.pagination a',
            '.pager a',
            'a[href*="page"]',
            'a:contains("Next")',
            'a:contains("»")',
            '.next-page',
            '[class*="pagination"] a'
        ]
        
        for selector in pagination_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True).lower()
                    
                    # Skip invalid URLs
                    if not href or href.startswith('javascript:') or href == '#':
                        continue
                    
                    if ('next' in text or '»' in text or 
                        'page' in href.lower() or text.isdigit()):
                        full_url = urljoin(current_url, href)
                        if full_url not in urls and full_url != current_url:
                            urls.append(full_url)
            except:
                continue
        
        return urls
    
    def scrape_category(self, url: str, category: str) -> List[Dict]:
        """Scrape all jobs from a category with pagination"""
        all_jobs = []
        visited_urls = set()
        urls_to_visit = [url]
        seen_job_urls = set()  # Track job URLs to avoid processing same job twice
        
        while urls_to_visit:
            current_url = urls_to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
                
            visited_urls.add(current_url)
            logger.info(f"Scraping {category} jobs from: {current_url}")
            
            soup = self.get_page(current_url)
            if not soup:
                continue
            
            # Extract jobs from current page
            jobs = self.extract_job_listings(soup, category)
            logger.info(f"Found {len(jobs)} jobs on this page")
            
            # Get detailed information for each job (with fixes) and deduplicate
            jobs_processed = 0
            for job in jobs:
                job_url = job['view_url']
                if job_url in seen_job_urls:
                    logger.debug(f"Skipping already processed job: {job['title'][:50]}...")
                    continue
                    
                seen_job_urls.add(job_url)
                jobs_processed += 1
                logger.info(f"Processing job {jobs_processed}/{len(jobs)}: {job['title'][:50]}...")
                
                try:
                    enhanced_job = self.get_job_details(job)
                    all_jobs.append(enhanced_job)
                except Exception as e:
                    logger.error(f"Error processing job {job['view_url']}: {e}")
                    # Add job with basic info if detail extraction fails
                    all_jobs.append(job)
                
                # Small delay between job detail requests
                time.sleep(0.5)
            
            # Find pagination URLs
            pagination_urls = self.get_pagination_urls(soup, current_url)
            for page_url in pagination_urls:
                if page_url not in visited_urls and page_url not in urls_to_visit:
                    urls_to_visit.append(page_url)
                    logger.info(f"Added pagination URL: {page_url}")
            
            # Limit to prevent infinite loops
            if len(visited_urls) > 50:
                logger.warning(f"Reached maximum page limit for {category}")
                break
        
        logger.info(f"Total {category} jobs found: {len(all_jobs)}")
        return all_jobs
    
    def remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on view_url (unique identifier)"""
        seen_urls = set()
        unique_jobs = []
        
        for job in jobs:
            view_url = job.get('view_url', '')
            if view_url and view_url not in seen_urls:
                seen_urls.add(view_url)
                unique_jobs.append(job)
            else:
                logger.debug(f"Removing duplicate job: {job.get('title', 'Unknown')[:50]}...")
        
        logger.info(f"Removed {len(jobs) - len(unique_jobs)} duplicate jobs")
        return unique_jobs
    
    def scrape_all_jobs(self) -> List[Dict]:
        """Scrape jobs from both Government and Private categories"""
        urls = {
            'Government': 'https://www.cgresettlement.com/jobs/Government',
            'Private': 'https://www.cgresettlement.com/jobs/Private'
        }
        
        all_jobs = []
        
        for category, url in urls.items():
            logger.info(f"Starting to scrape {category} jobs...")
            try:
                jobs = self.scrape_category(url, category)
                all_jobs.extend(jobs)
                logger.info(f"Completed scraping {category}: {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"Error scraping {category}: {e}")
                continue
            
            # Delay between categories
            time.sleep(self.delay * 2)
        
        # Remove duplicates before returning
        logger.info(f"Total jobs before deduplication: {len(all_jobs)}")
        all_jobs = self.remove_duplicates(all_jobs)
        logger.info(f"Total unique jobs after deduplication: {len(all_jobs)}")
        
        return all_jobs

def clean_existing_json(input_file: str, output_file: str):
    """Clean an existing JSON file by removing duplicates"""
    try:
        logger.info(f"Loading jobs from {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        logger.info(f"Original job count: {len(jobs)}")
        
        # Create a scraper instance to use the deduplication method
        scraper = JobScraper()
        unique_jobs = scraper.remove_duplicates(jobs)
        
        # Save cleaned data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_jobs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Cleaned jobs saved to {output_file}")
        logger.info(f"Removed {len(jobs) - len(unique_jobs)} duplicates")
        
        return unique_jobs
        
    except FileNotFoundError:
        logger.error(f"File {input_file} not found")
        return None
    except Exception as e:
        logger.error(f"Error cleaning JSON file: {e}")
        return None

def main():
    """Main function to run the scraper"""
    scraper = JobScraper()
    
    try:
        logger.info("Starting job scraping with fixes and deduplication...")
        jobs = scraper.scrape_all_jobs()
        
        # Save to JSON file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Scraping completed! Found {len(jobs)} unique jobs")
        logger.info(f"Results saved to {OUTPUT_FILE}")
        
        # Print summary
        gov_jobs = [j for j in jobs if j['category'] == 'Government']
        private_jobs = [j for j in jobs if j['category'] == 'Private']
        
        print(f"\n=== SCRAPING SUMMARY ===")
        print(f"Total Unique Jobs: {len(jobs)}")
        print(f"Government Jobs: {len(gov_jobs)}")
        print(f"Private Jobs: {len(private_jobs)}")
        print(f"Results saved to: {OUTPUT_FILE}")
        
        # Print first few jobs as sample
        if jobs:
            print(f"\n=== SAMPLE JOBS ===")
            for i, job in enumerate(jobs[:3], 1):
                print(f"\nJob #{i}:")
                print(f"Title: {job['title']}")
                print(f"Category: {job['category']}")
                print(f"Posted Date: {job.get('posted_date', 'Not found')}")
                print(f"Deadline: {job.get('deadline', 'Not found')}")
                print(f"View URL: {job['view_url']}")
                print(f"Apply Link: {job['apply_link']}")
                print(f"Description: {job['description'][:150]}...")
        
        # Validate uniqueness
        view_urls = [job['view_url'] for job in jobs]
        unique_urls = set(view_urls)
        if len(view_urls) == len(unique_urls):
            print(f"\n✅ VALIDATION PASSED: All {len(jobs)} jobs are unique!")
        else:
            print(f"\n❌ VALIDATION FAILED: Found {len(view_urls) - len(unique_urls)} duplicates!")
        
        # Also print JSON to stdout for immediate use
        print(f"\n=== FULL JSON OUTPUT ===")
        print(json.dumps(jobs, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        # Clean existing JSON files
        if len(sys.argv) > 3:
            input_file = sys.argv[2]
            output_file = sys.argv[3]
        else:
            input_file = "jobs_fixed.json"
            output_file = "jobs_cleaned.json"
        
        print(f"Cleaning duplicates from {input_file} -> {output_file}")
        cleaned_jobs = clean_existing_json(input_file, output_file)
        
        if cleaned_jobs:
            print(f"✅ Successfully cleaned {input_file}")
            print(f"Original: Unknown count")
            print(f"Cleaned: {len(cleaned_jobs)} unique jobs")
            print(f"Output: {output_file}")
    else:
        # Run the main scraper
        main()