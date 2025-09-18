import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path

# Get the current directory where the script is located
CURRENT_DIR = Path(__file__).parent
OUTPUT_FILE = CURRENT_DIR / "servicemen_jobs.json"

class JobScraper:
    def __init__(self):
        self.base_url = "https://linkingsky.com"
        self.target_url = "https://linkingsky.com/government-exams/Servicemen_Jobs.html"
        self.session = requests.Session()
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def clean_text(self, text):
        """Clean and normalize text by removing extra whitespace and special characters"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        # Remove any remaining unwanted characters
        cleaned = re.sub(r'[^\w\s\-\(\)\,\.\:]', '', cleaned)
        return cleaned

    def extract_job_title(self, organization_cell):
        """Extract job title from organization cell"""
        # Look for links within the organization cell
        links = organization_cell.find_all('a')
        
        if links:
            # Get the first meaningful link text
            for link in links:
                title = self.clean_text(link.get_text())
                if title and not title.lower().startswith('#'):
                    return title
        
        # If no good link found, use the cell text
        title = self.clean_text(organization_cell.get_text())
        return title if title and not title.lower().startswith('#') else None

    def extract_view_url(self, organization_cell):
        """Extract the view/apply URL from organization cell"""
        links = organization_cell.find_all('a')
        
        if links:
            # Get the first meaningful link
            for link in links:
                href = link.get('href')
                if href and not href.lower().startswith('#'):
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        return urljoin(self.base_url, href)
                    elif href.startswith('http'):
                        return href
                    else:
                        return urljoin(self.base_url, '/' + href)
        
        return None

    def extract_apply_link(self, view_url):
        """Extract the actual apply link from the job detail page"""
        if not view_url:
            return ""
        
        try:
            print(f"  -> Fetching apply link from: {view_url}")
            response = self.session.get(view_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for all links in the page
            all_links = soup.find_all('a', href=True)
            
            # Priority 1: Look for official government/organization application portals
            high_priority_domains = [
                'gov.in', 'nic.in', 'ibps.in', 'ssc.nic.in', 'upsconline.nic.in',
                'mponline.gov.in', 'regn.', 'recruitment.', 'careers.', 'apply.',
                'application.', 'online.', 'portal.', 'register.', 'admission.'
            ]
            
            # Priority 2: Look for links with apply-related keywords
            apply_keywords = [
                'apply', 'application', 'online', 'register', 'recruitment',
                'notification', 'portal', 'careers', 'admission', 'exam'
            ]
            
            best_links = []
            
            for link in all_links:
                href = link.get('href', '').strip()
                link_text = link.get_text().strip().lower()
                
                # Skip invalid links
                if not href or href.startswith('#') or 'javascript:' in href.lower():
                    continue
                
                # Convert to absolute URL
                if href.startswith('/'):
                    full_url = urljoin(self.base_url, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(view_url, href)
                
                # Skip internal LinkingSky links and document links unless they're the only option
                if self.base_url in full_url and not any(keyword in full_url.lower() for keyword in ['regn', 'apply', 'online', 'portal']):
                    continue
                
                # Calculate priority score
                score = 0
                
                # High priority for government domains
                for domain in high_priority_domains:
                    if domain in full_url.lower():
                        score += 100
                        break
                
                # Medium priority for apply-related keywords in URL
                for keyword in apply_keywords:
                    if keyword in full_url.lower():
                        score += 50
                        break
                
                # Medium priority for apply-related text
                for keyword in apply_keywords:
                    if keyword in link_text:
                        score += 30
                        break
                
                # Bonus for external sites (not LinkingSky)
                if self.base_url not in full_url:
                    score += 20
                
                # Penalty for PDF files (they're usually notifications, not application links)
                if full_url.lower().endswith('.pdf'):
                    score -= 10
                
                if score > 0:
                    best_links.append((score, full_url, link_text))
            
            # Sort by score and return the best match
            if best_links:
                best_links.sort(key=lambda x: x[0], reverse=True)
                best_link = best_links[0][1]
                print(f"  -> Found apply link: {best_link}")
                return best_link
            
            # Fallback: look for any external links
            for link in all_links:
                href = link.get('href', '').strip()
                if href and href.startswith('http') and self.base_url not in href:
                    print(f"  -> Using fallback external link: {href}")
                    return href
            
            # Last resort: return the view URL
            print(f"  -> No apply link found, using view URL")
            return view_url
            
        except Exception as e:
            print(f"  -> Error fetching apply link: {e}")
            return view_url

    def parse_date(self, date_text):
        """Parse and normalize date text"""
        if not date_text:
            return ""
        
        cleaned_date = self.clean_text(date_text)
        
        # Remove common suffixes like "(X days left)"
        cleaned_date = re.sub(r'\([^)]*\)', '', cleaned_date).strip()
        
        return cleaned_date

    def scrape_jobs(self):
        """Main method to scrape job postings"""
        try:
            print(f"Fetching data from: {self.target_url}")
            response = self.session.get(self.target_url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all tables on the page
            tables = soup.find_all('table')
            jobs = []
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    # Skip header rows and rows with insufficient data
                    if len(cells) < 4:
                        continue
                    
                    # Check if this is a header row
                    if any(cell.name == 'th' for cell in cells):
                        continue
                    
                    # Extract data from cells
                    post_date_cell = cells[0] if len(cells) > 0 else None
                    organization_cell = cells[1] if len(cells) > 1 else None
                    posts_cell = cells[2] if len(cells) > 2 else None
                    last_date_cell = cells[3] if len(cells) > 3 else None
                    
                    # Skip if organization cell is empty or contains ads
                    if not organization_cell:
                        continue
                    
                    org_text = organization_cell.get_text().strip().lower()
                    if not org_text or 'google_vignette' in org_text or org_text.startswith('#'):
                        continue
                    
                    # Extract job details
                    job_title = self.extract_job_title(organization_cell)
                    if not job_title:
                        continue
                    
                    post_date = self.parse_date(post_date_cell.get_text() if post_date_cell else "")
                    last_date = self.parse_date(last_date_cell.get_text() if last_date_cell else "")
                    view_url = self.extract_view_url(organization_cell)
                    
                    # Extract the actual apply link from the job detail page
                    apply_link = self.extract_apply_link(view_url)
                    
                    # Create job entry
                    job_entry = {
                        "job_title": job_title,
                        "post_date": post_date,
                        "last_date": last_date,
                        "view_url": view_url if view_url else "",
                        "apply_link": apply_link
                    }
                    
                    jobs.append(job_entry)
                    print(f"Extracted: {job_title}")
            
            print(f"\nTotal jobs extracted: {len(jobs)}")
            return jobs
            
        except requests.RequestException as e:
            print(f"Error fetching the page: {e}")
            return []
        except Exception as e:
            print(f"Error parsing the page: {e}")
            return []

    def save_to_json(self, jobs, filename=None):
        """Save jobs data to JSON file"""
        if filename is None:
            filename = OUTPUT_FILE
        else:
            filename = CURRENT_DIR / filename
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")

    def run(self):
        """Run the complete scraping process"""
        print("Starting LinkingSky Ex-Servicemen Jobs Scraper...")
        print("=" * 50)
        
        jobs = self.scrape_jobs()
        
        if jobs:
            # Print sample output
            print("\nSample job entries:")
            print("-" * 30)
            for i, job in enumerate(jobs[:3]):  # Show first 3 jobs
                print(f"{i+1}. {json.dumps(job, indent=2, ensure_ascii=False)}")
            
            # Save to JSON file
            self.save_to_json(jobs)
            
            # Return JSON string for direct use
            return json.dumps(jobs, indent=2, ensure_ascii=False)
        else:
            print("No jobs found!")
            return "[]"

def main():
    """Main function to run the scraper"""
    scraper = JobScraper()
    result = scraper.run()
    
    # Print the complete JSON output
    print("\n" + "=" * 50)
    print("COMPLETE JSON OUTPUT:")
    print("=" * 50)
    print(result)

if __name__ == "__main__":
    main()