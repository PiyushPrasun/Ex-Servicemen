import streamlit as st
import fitz  # PyMuPDF
import re
import io
import json
from xhtml2pdf import pisa
import base64
from mistralai import Mistral
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Initialize Mistral client
@st.cache_resource
def get_mistral_client():
    api_key = os.getenv("MISTRAL_API_KEY", "CC5WANovNiyCtnnWBM3ZLDGB0NU1ZCpI")
    return Mistral(api_key=api_key)

import spacy
SPACY_AVAILABLE = True

from email_validator import validate_email, EmailNotValidError
import phonenumbers
from fuzzywuzzy import process as fuzzy_process

class EnhancedResumeExtractor:
    """Improved resume data extraction using spaCy NER, phonenumbers, email_validator, and fuzzy matching."""

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy English model not found. Download with: python -m spacy download en_core_web_sm")
            self.nlp = None

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common OCR/scanning errors
        text = text.replace(' AT ', '@').replace(' at ', '@')
        text = re.sub(r'(\w)\s+@\s+(\w)', r'\1@\2', text)
        text = text.replace(' DOT ', '.').replace(' dot ', '.')
        text = re.sub(r'(\w)\s+\.\s+(\w)', r'\1.\2', text)
        
        # Fix common character recognition errors
        ocr_fixes = {
            '|': 'l', '1': 'l', '0': 'O', '5': 'S', '8': 'B',
            '@': '@', 'rn': 'm', 'vv': 'w', 'nn': 'n'
        }
        
        # Apply OCR fixes cautiously (only for obvious errors)
        for error, fix in ocr_fixes.items():
            if error in ['|', 'rn', 'vv'] and error in text:
                text = text.replace(error, fix)
        
        # Fix phone number spacing
        text = re.sub(r'(\+91)\s*(\d)', r'\1 \2', text)
        text = re.sub(r'(\d{5})\s*(\d{5})', r'\1 \2', text)
        
        return text

    def analyze_document_structure(self, text: str) -> dict:
        """Analyze document structure to adapt extraction strategies"""
        lines = text.split('\n')
        structure_info = {
            'has_headers': False,
            'has_sections': False,
            'has_bullets': False,
            'layout_type': 'unstructured',
            'key_sections': []
        }
        
        # Detect headers and sections
        section_keywords = ['personal', 'contact', 'education', 'experience', 'skills', 'achievements', 'objective', 'profile']
        headers_found = []
        
        for line in lines:
            line_clean = line.strip().lower()
            
            # Check for section headers
            for keyword in section_keywords:
                if keyword in line_clean and len(line_clean) < 50:
                    headers_found.append(keyword)
                    structure_info['has_sections'] = True
            
            # Check for bullet points
            if re.match(r'^\s*[•\-\*\+]\s', line):
                structure_info['has_bullets'] = True
            
            # Check for all caps headers
            if line.strip() and line.strip().isupper() and len(line.strip()) > 3:
                structure_info['has_headers'] = True
        
        structure_info['key_sections'] = list(set(headers_found))
        
        # Determine layout type
        if structure_info['has_sections'] and structure_info['has_headers']:
            structure_info['layout_type'] = 'structured'
        elif structure_info['has_bullets']:
            structure_info['layout_type'] = 'semi_structured'
        
        return structure_info

    def get_context_window(self, text: str, keyword: str, window_size: int = 3) -> str:
        """Get text context around a keyword"""
        lines = text.split('\n')
        contexts = []
        
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                start = max(0, i - window_size)
                end = min(len(lines), i + window_size + 1)
                context = '\n'.join(lines[start:end])
                contexts.append(context)
        
        # Return the longest/most relevant context
        if contexts:
            return max(contexts, key=len)
        return ""
    
    def extract_by_patterns_and_context(self, text: str, field_name: str, patterns: list, context_keywords: list = None) -> list:
        """Generic extraction method using patterns and context"""
        results = []
        
        # Extract using patterns
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if isinstance(match, tuple):
                        # Join tuple elements
                        result = ' '.join([str(m).strip() for m in match if str(m).strip()])
                    else:
                        result = str(match).strip()
                    
                    if len(result) > 3:  # Basic validation
                        results.append(result)
            except re.error:
                continue
        
        # Extract using context if provided
        if context_keywords:
            for keyword in context_keywords:
                context = self.get_context_window(text, keyword, 3)
                if context:
                    # Apply patterns to context
                    for pattern in patterns:
                        try:
                            matches = re.findall(pattern, context, re.MULTILINE | re.IGNORECASE)
                            for match in matches:
                                if isinstance(match, tuple):
                                    result = ' '.join([str(m).strip() for m in match if str(m).strip()])
                                else:
                                    result = str(match).strip()
                                
                                if len(result) > 3:
                                    results.append(result)
                        except re.error:
                            continue
        
        # Clean and deduplicate
        clean_results = []
        seen = set()
        for result in results:
            clean_result = self.clean_text(result)
            if clean_result and clean_result.lower() not in seen:
                clean_results.append(clean_result)
                seen.add(clean_result.lower())
        
        return clean_results
    def extract_name(self, text: str) -> str:
        """Universal name extraction for different document formats"""
        # Analyze document structure first
        structure = self.analyze_document_structure(text)
        
        # Multiple name extraction patterns for different formats
        name_patterns = [
            # Structured formats
            r'(?:Name|NAME|Full\s*Name|Full\s*NAME)\s*[:\-]?\s*([A-Z][a-zA-Z\s\.]+?)(?:\n|$|,)',
            # Resume headers (common pattern)
            r'^([A-Z][A-Z\s]{8,50})$',  # All caps name on separate line
            # Bio-data format
            r'(?:I\s+am|My\s+name\s+is|Name\s*:)\s*([A-Z][a-zA-Z\s]+?)(?:\n|$|\.|,)',
            # Application format
            r'(?:Applied\s+by|Applicant|Candidate)\s*[:\-]?\s*([A-Z][a-zA-Z\s]+?)(?:\n|$)',
            # Title case names at document start
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$',
        ]
        
        context_keywords = ['name', 'applicant', 'candidate', 'personnel']
        names = self.extract_by_patterns_and_context(text, 'name', name_patterns, context_keywords)
        
        # Strategy: Look at document beginning (first 10 lines)
        lines = text.split('\n')
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Skip lines with obvious non-name content
            skip_indicators = ['phone', 'email', '@', '+91', 'contact', 'address', 'veteran', 'army', 'navy', 'experience']
            if any(indicator in line.lower() for indicator in skip_indicators):
                continue
            
            # Check for name patterns
            words = line.split()
            if 2 <= len(words) <= 4:
                # All words should be alphabetic
                if all(word.replace('.', '').isalpha() for word in words):
                    # Name should be in title case or all caps
                    if line.istitle() or (line.isupper() and len(line) > 8):
                        names.append(line)
        
        # spaCy NER extraction
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                        names.append(ent.text.strip())
            except:
                pass
        
        # Filter and rank names
        valid_names = []
        for name in names:
            name = self.clean_text(name)
            
            # Basic validation
            if len(name) < 5 or len(name) > 60:
                continue
            
            words = name.split()
            if not (2 <= len(words) <= 4):
                continue
            
            # Should be mostly alphabetic
            if not all(word.replace('.', '').isalpha() for word in words):
                continue
            
            # Remove common false positives
            false_positives = ['indian army', 'veteran', 'officer', 'get in contact', 'personal profile', 'work experience']
            if any(fp in name.lower() for fp in false_positives):
                continue
            
            valid_names.append(name.title())
        
        # Return the best name (prefer first occurrence for better accuracy)
        return valid_names[0] if valid_names else ""

    def extract_email(self, text: str) -> str:
        """Universal email extraction for different document formats"""
        # Enhanced email patterns for various formats
        email_patterns = [
            # Standard email patterns
            r'(?:E-?mail|EMAIL|Email|e-mail|Mail)\s*[:\-]?\s*([\w\.-]+@[\w\.-]+\.\w+)',
            r'([\w\.-]+@[\w\.-]+\.\w+)',  # Direct email pattern
            # OCR-affected emails
            r'([\w\.-]+\s+AT\s+[\w\.-]+\s*DOT\s*\w+)',
            r'([\w\.-]+\s+at\s+[\w\.-]+\s*dot\s*\w+)',
            r'([\w\.-]+\s+AT\s+[\w\.-]+\s*\.\s*\w+)',
            r'([\w\.-]+\s+at\s+[\w\.-]+\s*\.\s*\w+)',
            # Spaced out emails
            r'([\w\.-]+\s*@\s*[\w\.-]+\s*\.\s*\w+)',
        ]
        
        context_keywords = ['email', 'mail', 'contact', '@']
        emails = self.extract_by_patterns_and_context(text, 'email', email_patterns, context_keywords)
        
        # Clean and validate emails
        valid_emails = []
        for email in emails:
            # Fix common OCR/formatting issues
            email = email.replace(' AT ', '@').replace(' at ', '@')
            email = email.replace(' DOT ', '.').replace(' dot ', '.')
            email = re.sub(r'\s+', '', email)  # Remove all spaces
            
            # Basic email validation
            if '@' in email and '.' in email and len(email) > 5:
                try:
                    # Use email validator if available
                    valid = validate_email(email)
                    valid_emails.append(valid.email.lower())
                    break  # Return first valid email
                except (EmailNotValidError, Exception):
                    # Basic regex validation as fallback
                    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                        valid_emails.append(email.lower())
                        break
        
        return valid_emails[0] if valid_emails else ""

    def extract_phone(self, text: str) -> str:
        """Universal phone extraction for different document formats"""
        # Comprehensive phone patterns for various formats
        phone_patterns = [
            # Indian mobile numbers with country code
            r'(?:Phone|Mobile|Contact|Ph|Tel|Call|Cell)\s*[:\-]?\s*([+]?91[-\s]?\d{5}[-\s]?\d{5})',
            r'(?:Phone|Mobile|Contact|Ph|Tel|Call|Cell)\s*[:\-]?\s*([+]?91[-\s]?\d{10})',
            # Without labels
            r'([+]?91[-\s]?\d{5}[-\s]?\d{5})',
            r'([+]?91[-\s]?\d{10})',
            # 10-digit numbers (with context)
            r'(?:Phone|Mobile|Contact|Ph|Tel|Call|Cell)\s*[:\-]?\s*(\d{5}[-\s]?\d{5})',
            r'(?:Phone|Mobile|Contact|Ph|Tel|Call|Cell)\s*[:\-]?\s*(\d{10})',
            # General patterns
            r'(\d{5}\s+\d{5})',  # Space separated
            r'(\b\d{10}\b)',     # 10 consecutive digits
            # International formats
            r'([+]\d{1,3}[-\s]?\d{10,11})',
        ]
        
        context_keywords = ['phone', 'mobile', 'contact', 'tel', 'call', 'number']
        phones = self.extract_by_patterns_and_context(text, 'phone', phone_patterns, context_keywords)
        
        # Use phonenumbers library for robust parsing
        validated_phones = []
        try:
            for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
                num = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.NATIONAL)
                validated_phones.append(num.strip())
        except:
            pass
        
        # Combine and process all phone numbers
        all_phones = phones + validated_phones
        formatted_phones = set()
        
        for phone in all_phones:
            # Clean the number
            clean_num = re.sub(r'[^\d+]', '', str(phone))
            
            # Validate and format
            if len(clean_num) == 10 and clean_num.isdigit():
                # Add country code for Indian numbers
                formatted_phones.add(f"+91 {clean_num[:5]} {clean_num[5:]}")
            elif len(clean_num) == 12 and clean_num.startswith('91'):
                # Already has country code
                formatted_phones.add(f"+91 {clean_num[2:7]} {clean_num[7:]}")
            elif len(clean_num) == 13 and clean_num.startswith('+91'):
                # Properly formatted
                num_part = clean_num[3:]
                formatted_phones.add(f"+91 {num_part[:5]} {num_part[5:]}")
            elif len(clean_num) >= 10:
                # Take last 10 digits
                last_10 = clean_num[-10:]
                if last_10.isdigit():
                    formatted_phones.add(f"+91 {last_10[:5]} {last_10[5:]}")
        
        # Return the best formatted number
        if formatted_phones:
            return sorted(list(formatted_phones))[0]  # Return first alphabetically
        
        return ""

    def extract_address(self, text: str) -> str:
        """Enhanced address extraction with better context recognition"""
        addresses = []
        
        # Strategy 1: Look for complete address patterns with house numbers and areas
        address_patterns = [
            # Pattern for "House No. C 55, Area, City, State - PIN"
            r'(?:House\s+No\.?|H\.?No\.?|House)\s*[:\-]?\s*([A-Z]?\s*\d+[A-Z]?[,\s]+[^,\n]+(?:,\s*[^,\n]+)*(?:,\s*[^,\n]+)*\s*-?\s*\d{6})',
            # General address with PIN
            r'([A-Z]?\s*\d+[A-Z]?[,\s]+[^,\n]+(?:,\s*[^,\n]+){2,5}\s*-?\s*\d{6})',
            # Address with clear location indicators
            r'((?:Behind|Near|Opposite|Next to)[^,\n]+(?:,\s*[^,\n]+){1,4}\s*-?\s*\d{6})',
            # Society/Colony addresses
            r'([A-Z][^,\n]*(?:Society|Colony|Nagar|Apartment|Complex|Building)[^,\n]*(?:,\s*[^,\n]+){1,4}\s*-?\s*\d{6})',
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                clean_addr = self.clean_text(match)
                if len(clean_addr) > 20 and ',' in clean_addr:  # Must have reasonable length and commas
                    addresses.append(clean_addr)
        
        # Strategy 2: Context-based extraction around "address" keywords
        address_context = self.get_context_window(text, "address", 3)
        if address_context:
            lines = address_context.split('\n')
            for line in lines:
                if 'address' in line.lower():
                    # Extract text after "address:"
                    addr_match = re.search(r'address\s*[:\-]?\s*(.+)', line, re.IGNORECASE)
                    if addr_match:
                        potential_addr = addr_match.group(1).strip()
                        if len(potential_addr) > 15:
                            addresses.append(potential_addr)
                    
                    # Check next lines for continuation
                    line_idx = address_context.split('\n').index(line)
                    next_lines = address_context.split('\n')[line_idx+1:line_idx+4]
                    full_address_parts = []
                    for next_line in next_lines:
                        next_line = next_line.strip()
                        if next_line and not any(skip in next_line.lower() for skip in ['phone', 'email', 'experience', 'education']):
                            full_address_parts.append(next_line)
                        else:
                            break
                    
                    if full_address_parts:
                        full_addr = ', '.join(full_address_parts)
                        if len(full_addr) > 20:
                            addresses.append(full_addr)
        
        # Strategy 3: Multi-line address detection
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for lines that start with house numbers or area names
            if re.match(r'^(?:House\s+No\.?|H\.?No\.?|[A-Z]?\s*\d+[A-Z]?[,\s])', line, re.IGNORECASE):
                # Collect this line and next few lines as potential address
                addr_lines = [line]
                for j in range(i+1, min(len(lines), i+4)):
                    next_line = lines[j].strip()
                    if next_line and not any(skip in next_line.lower() for skip in ['phone', 'email', 'experience', 'work', 'education', 'personal']):
                        addr_lines.append(next_line)
                        # Stop if we find a PIN code
                        if re.search(r'\d{6}', next_line):
                            break
                    else:
                        break
                
                if len(addr_lines) >= 2:
                    full_addr = ', '.join(addr_lines)
                    if len(full_addr) > 25:
                        addresses.append(full_addr)
        
        # Strategy 4: spaCy NER for locations (as fallback)
        if not addresses and self.nlp:
            doc = self.nlp(text)
            locations = []
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC") and len(ent.text) > 3:
                    locations.append(ent.text)
            
            if len(locations) >= 2:
                # Try to construct address from multiple locations
                address_from_locations = ', '.join(list(dict.fromkeys(locations))[:4])
                if len(address_from_locations) > 15:
                    addresses.append(address_from_locations)
        
        # Clean and validate addresses
        valid_addresses = []
        for addr in addresses:
            addr = self.clean_text(addr)
            # Remove addresses that are too generic or contain unwanted keywords
            if any(skip in addr.lower() for skip in ['indian army', 'veteran', 'officer', 'experience', 'phone', 'email']):
                continue
            
            # Must have reasonable length and structure
            if len(addr) > 20 and (',' in addr or len(addr.split()) >= 5):
                valid_addresses.append(addr)
        
        # Return the longest/most complete address
        if valid_addresses:
            # Sort by length and completeness (prefer addresses with PIN codes)
            valid_addresses.sort(key=lambda x: (re.search(r'\d{6}', x) is not None, len(x)), reverse=True)
            return valid_addresses[0]
        
        return ""

    def extract_education(self, text: str) -> dict:
        """Enhanced education extraction with better pattern recognition"""
        education_info = {'highest_qualification': '', 'courses': ''}
        
        # Strategy 1: Look for education sections
        education_contexts = []
        for keyword in ['education', 'qualification', 'academic', 'educational']:
            context = self.get_context_window(text, keyword, 4)
            if context:
                education_contexts.append(context)
        
        # Strategy 2: Comprehensive degree and qualification patterns
        degree_patterns = [
            # Standard degrees
            r'((?:B\.?A\.?|B\.?Sc\.?|B\.?Com\.?|B\.?Tech\.?|B\.E\.?|Bachelor)[^,\n]*)',
            r'((?:M\.?A\.?|M\.?Sc\.?|M\.?Com\.?|M\.?Tech\.?|M\.E\.?|Master)[^,\n]*)',
            r'((?:PhD|Ph\.D|Doctorate)[^,\n]*)',
            
            # School qualifications
            r'(\d+th[^,\n]*)',
            r'((?:12th|Twelfth|XII)[^,\n]*)',
            r'((?:10th|Tenth|X)[^,\n]*)',
            r'((?:Higher\s+Secondary|Senior\s+Secondary)[^,\n]*)',
            
            # Professional qualifications
            r'((?:Diploma|Certificate|ITI|Polytechnic)[^,\n]*)',
            r'((?:Graduate|Graduation)[^,\n]*)',
            
            # Military/Army education
            r'((?:Army|Military|Defence|Defense)\s+[^,\n]*(?:Course|Training|School|Academy)[^,\n]*)',
        ]
        
        found_qualifications = []
        search_texts = education_contexts + [text]
        
        for search_text in search_texts:
            for pattern in degree_patterns:
                matches = re.findall(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    clean_qual = self.clean_text(match)
                    if len(clean_qual) > 5 and len(clean_qual) < 100:
                        found_qualifications.append(clean_qual)
        
        # Strategy 3: Look for institution names and years
        institution_patterns = [
            r'([A-Z][A-Z\s]+(?:ACADEMY|SCHOOL|COLLEGE|UNIVERSITY|INSTITUTE)[^,\n]*)',
            r'((?:Class\s+of|Graduated)\s+\d{4}[^,\n]*)',
            r'([A-Z][^,\n]*(?:Academy|College|University|Institute)[^,\n]*\d{4})',
        ]
        
        for pattern in institution_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_inst = self.clean_text(match)
                if len(clean_inst) > 8:
                    found_qualifications.append(clean_inst)
        
        # Strategy 4: Course and certification patterns
        course_patterns = [
            r'(Certificate\s+Course\s+in\s+[^,\n]+)',
            r'((?:Basic|Advanced|Professional)\s+[^,\n]*(?:Course|Training|Certificate)[^,\n]*)',
            r'([A-Z][^,\n]*(?:Training|Course|Certification)[^,\n]*(?:Certificate|Training)[^,\n]*)',
            r'(STCW[^,\n]*)',  # Maritime certifications
            r'([A-Z][^,\n]*(?:Safety|Security|Technical)\s+[^,\n]*(?:Course|Training|Certificate)[^,\n]*)',
        ]
        
        found_courses = []
        for pattern in course_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_course = self.clean_text(match)
                if len(clean_course) > 8 and len(clean_course) < 150:
                    found_courses.append(clean_course)
        
        # Strategy 5: Extract from education history sections
        lines = text.split('\n')
        in_education_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check if we're entering education section
            if any(keyword in line.lower() for keyword in ['education history', 'educational background', 'academic']):
                in_education_section = True
                continue
            
            # Check if we're leaving education section
            if in_education_section and any(keyword in line.lower() for keyword in ['work experience', 'employment', 'skills', 'achievements']):
                in_education_section = False
                continue
            
            # Extract from education section
            if in_education_section and line:
                # Look for school/college names (often in all caps)
                if re.match(r'^[A-Z][A-Z\s]+$', line) and len(line) > 8:
                    found_qualifications.append(line)
                # Look for qualification descriptions
                elif any(qual in line.lower() for qual in ['graduated', 'class of', 'honor', 'honours']):
                    found_qualifications.append(line)
        
        # Clean and categorize qualifications
        degrees = []
        courses = []
        
        for qual in found_qualifications:
            qual = self.clean_text(qual).title()
            
            # Skip unwanted content
            if any(skip in qual.lower() for skip in ['phone', 'email', 'address', 'contact', 'experience', 'management']):
                continue
            
            # Categorize as degree or course
            if any(degree_word in qual.lower() for degree_word in ['b.a', 'b.sc', 'b.com', 'b.tech', 'b.e', 'm.a', 'm.sc', 'm.com', 'm.tech', 'm.e', 'phd', 'graduate', '10th', '12th', 'diploma']):
                degrees.append(qual)
            elif any(course_word in qual.lower() for course_word in ['certificate', 'course', 'training', 'certification']):
                courses.append(qual)
            else:
                # If unsure, add to qualifications
                degrees.append(qual)
        
        # Remove duplicates while preserving order
        degrees = list(dict.fromkeys(degrees))
        courses = list(dict.fromkeys(courses))
        
        # Select highest qualification (prefer longer, more detailed descriptions)
        if degrees:
            # Sort by length and content completeness
            degrees.sort(key=lambda x: (any(word in x.lower() for word in ['master', 'm.', 'phd']), len(x)), reverse=True)
            education_info['highest_qualification'] = degrees[0]
        
        # Join courses
        if courses:
            education_info['courses'] = '; '.join(courses[:5])  # Limit to 5 courses
        
        return education_info

    def extract_experience(self, text: str) -> str:
        """Universal experience extraction for different document formats"""
        # Adaptive experience patterns for various formats
        experience_patterns = [
            # Structured resume format
            r'([A-Z][A-Z\s&]+)\s*\n\s*([A-Za-z\s]+(?:Army|Navy|Air Force|Police|Government|Ltd|Company|Corp|Organization)[^\n]*)\s*[\|\-]\s*([A-Za-z]+\s+\d{4}\s*[\-\s]*[A-Za-z]*\s*\d{4})',
            # Bio-data format
            r'(?:Current\s+Post|Present\s+Employment|Job\s+Title|Designation)\s*[:\-]?\s*([^\n]+)',
            r'(?:Organization|Company|Department)\s*[:\-]?\s*([^\n]+)',
            # Service records
            r'(?:Service\s+Period|Period\s+of\s+Service|Duration)\s*[:\-]?\s*([^\n]+)',
            r'(\d+\s+years?\s+(?:of\s+)?(?:experience|service)[^\n]*)',
            # General work patterns
            r'(?:Worked\s+as|Working\s+as|Served\s+as|Posted\s+as)\s+([^\n]+)',
            r'(?:Employer|Previous\s+Employer)\s*[:\-]?\s*([^\n]+)',
            # Date ranges
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s*[\-\s]*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{4})',
        ]
        
        context_keywords = ['experience', 'employment', 'work', 'service', 'job', 'position', 'designation']
        experiences = self.extract_by_patterns_and_context(text, 'experience', experience_patterns, context_keywords)
        
        # Extract bullet points that describe work
        bullet_patterns = [
            r'[•\-\*]\s*([A-Z][^•\-\*\n]+(?:supervisor|management|lead|manage|responsible|coordinate)[^\n]*)',
            r'[•\-\*]\s*([A-Z][^•\-\*\n]{15,100})',  # General work-related bullets
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_bullet = self.clean_text(match)
                if len(clean_bullet) > 20:
                    # Check if it's work-related
                    work_keywords = ['manage', 'lead', 'supervise', 'coordinate', 'responsible', 'handle', 'oversee']
                    if any(keyword in clean_bullet.lower() for keyword in work_keywords):
                        experiences.append(clean_bullet)
        
        # Clean and deduplicate experiences
        unique_experiences = []
        seen = set()
        
        for exp in experiences:
            exp_clean = self.clean_text(exp)
            if len(exp_clean) > 10 and exp_clean.lower() not in seen:
                # Filter out non-experience content
                skip_terms = ['phone', 'email', 'address', 'contact', 'personal', 'education']
                if not any(term in exp_clean.lower() for term in skip_terms):
                    unique_experiences.append(exp_clean)
                    seen.add(exp_clean.lower())
        
        return ' | '.join(unique_experiences[:5])  # Limit to top 5 entries

    def extract_skills(self, text: str) -> str:
        """Universal skills extraction for different document formats"""
        # Adaptive skills patterns for various document formats
        skills_patterns = [
            # Structured format
            r'(?:SKILLS?|Skills?|AREAS?\s+OF\s+EXPERTISE|COMPETENCIES|STRENGTHS?|TECHNICAL\s+SKILLS?)\s*[:\-]?\s*([^\n]+(?:\n[^\n]*){0,4}?)(?=\n\s*[A-Z]{3,}|\Z)',
            # Bio-data format
            r'(?:Computer\s+Knowledge|Software\s+Knowledge|Technical\s+Knowledge)\s*[:\-]?\s*([^\n]+)',
            r'(?:Special\s+Skills?|Professional\s+Skills?|Core\s+Skills?)\s*[:\-]?\s*([^\n]+)',
            # Individual skill mentions
            r'(?:Proficient\s+in|Experience\s+with|Knowledge\s+of|Familiar\s+with)\s+([^\n,]+)',
            # Management skills
            r'([A-Z][a-z]+(?:\s+[A-Z&][a-z]*)*\s+(?:Management|Supervisor|Leadership|Skills?))',
            # Technical skills
            r'((?:Computer|Software|Technical|Microsoft|MS|Office)\s+[A-Za-z\s&]+)',
        ]
        
        context_keywords = ['skills', 'expertise', 'competencies', 'strengths', 'knowledge', 'proficient']
        skills_found = self.extract_by_patterns_and_context(text, 'skills', skills_patterns, context_keywords)
        
        # Extract from bullet points (skills sections)
        bullet_skills_pattern = r'[•\-\*]\s*([A-Z][^•\-\*\n]{3,60}(?:management|skills?|knowledge|experience|proficiency)[^•\-\*\n]*)'
        bullet_matches = re.findall(bullet_skills_pattern, text, re.IGNORECASE)
        for match in bullet_matches:
            clean_skill = self.clean_text(match)
            if 5 <= len(clean_skill) <= 80:
                skills_found.append(clean_skill)
        
        # Look for certification/course names as skills
        cert_patterns = [
            r'(Certificate\s+(?:Course\s+)?in\s+[^,\n]+)',
            r'((?:Basic|Advanced|Professional)\s+[A-Z][^,\n]*(?:Course|Training|Certificate)[^,\n]*)',
            r'([A-Z][^,\n]*(?:Certification|Certificate)[^,\n]*)',
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_cert = self.clean_text(match)
                if 8 <= len(clean_cert) <= 100:
                    skills_found.append(clean_cert)
        
        # Common technical and professional skills (keyword-based detection)
        common_skills = {
            'Computer Skills': ['computer', 'ms office', 'microsoft office', 'excel', 'word', 'powerpoint'],
            'Communication Skills': ['communication', 'english', 'hindi', 'language'],
            'Leadership': ['leadership', 'team lead', 'management', 'supervise'],
            'Technical Skills': ['technical', 'software', 'hardware', 'internet', 'email'],
            'Safety Management': ['fire safety', 'safety', 'security', 'first aid'],
            'Project Management': ['project', 'planning', 'coordination', 'organization'],
            'Problem Solving': ['problem solving', 'analytical', 'decision making'],
            'Time Management': ['time management', 'multitask', 'deadline'],
            'Military Skills': ['discipline', 'tactical', 'strategic', 'operations', 'defense', 'training'],
        }
        
        text_lower = text.lower()
        for skill_category, keywords in common_skills.items():
            if any(keyword in text_lower for keyword in keywords):
                skills_found.append(skill_category)
        
        # Add rank-specific military skills based on detected rank
        military_rank = self.extract_military_rank(text)
        if military_rank != 'Professional':
            if military_rank in ['Brigadier', 'Colonel', 'Lieutenant Colonel']:
                skills_found.extend(['Strategic Leadership', 'Operations Management', 'Crisis Management', 'Personnel Management'])
            elif military_rank in ['Major', 'Captain']:
                skills_found.extend(['Team Leadership', 'Operations Coordination', 'Training & Development'])
            elif military_rank in ['Lieutenant', 'Second Lieutenant']:
                skills_found.extend(['Team Management', 'Leadership Development', 'Operations Support'])
            else:
                skills_found.extend(['Military Leadership', 'Operational Excellence', 'Team Management'])
        
        # Clean and validate skills
        valid_skills = []
        seen = set()
        
        for skill in skills_found:
            skill_clean = self.clean_text(skill).title()
            
            # Skip if already seen or invalid
            if skill_clean.lower() in seen or len(skill_clean) < 3:
                continue
            
            # Filter out non-skill content
            invalid_terms = ['phone', 'email', 'address', 'contact', 'house no', 'indian army', 'name', 'date', 'birth']
            if any(term in skill_clean.lower() for term in invalid_terms):
                continue
            
            # Reasonable length check
            if 3 <= len(skill_clean) <= 80:
                valid_skills.append(skill_clean)
                seen.add(skill_clean.lower())
        
        return ', '.join(valid_skills[:15])  # Limit to 15 skills

    def extract_achievements(self, text: str) -> str:
        """Enhanced achievements extraction"""
        ach_context = self.get_context_window(text, "achievement", 3)
        award_context = self.get_context_window(text, "award", 2)
        
        achievement_patterns = [
            r'(?:ACHIEVEMENTS?|Achievements?|AWARDS?|Awards?|ACCOMPLISHMENTS?|Accomplishments?)\s*[:\-]?\s*([^\n]+(?:\n[^\n]*){0,4}?)(?=\n\s*[A-Z]{3,}|\Z)',
            r'(?:Distinguished|Recognition|Honor|Medal|Certificate|Commendation)\s+([^\n]+)',
            r'(?:Received|Awarded|Won|Achieved)\s+([^\n]+)',
        ]
        
        ach_lines = []
        search_text = ach_context + "\n" + award_context + "\n" + text
        
        for pattern in achievement_patterns:
            matches = re.findall(pattern, search_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            ach_lines.extend([self.clean_text(match) for match in matches if len(match.strip()) > 10])
        
        return ' '.join(list(dict.fromkeys(ach_lines))[:5])  # Limit to 5 achievements

    def extract_references(self, text: str) -> str:
        """Extract references information"""
        ref_context = self.get_context_window(text, "reference", 3)
        
        ref_patterns = [
            r'(?:REFERENCES?|References?)\s*[:\-]?\s*([^\n]+(?:\n[^\n]*){0,3}?)(?=\n\s*[A-Z]{3,}|\Z)',
            r'(?:Contact\s+person|Reference\s+person)\s*[:\-]?\s*([^\n]+)',
        ]
        
        ref_lines = []
        search_text = ref_context + "\n" + text
        
        for pattern in ref_patterns:
            matches = re.findall(pattern, search_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            ref_lines.extend([self.clean_text(match) for match in matches if len(match.strip()) > 5])
        
        return ' '.join(list(dict.fromkeys(ref_lines))[:2])  # Limit to 2 references

    def extract_personal_details(self, text: str) -> dict:
        """Enhanced personal details extraction"""
        details = {}
        
        # Enhanced patterns with better context
        patterns = {
            'date_of_birth': [
                r'(?:Date\s+of\s+birth|DOB|Birth\s+Date)\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
                r'(?:Date\s+of\s+birth|DOB)\s*[:\-]?\s*(\d{1,2}\s+\w+\s+\d{4})',
                r'(?:Born\s+on)\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            ],
            'marital_status': [
                r'(?:Marital\s+Status|Martial\s+status|Marriage\s+Status)\s*[:\-]?\s*(\w+)',
            ],
            'gender': [
                r'(?:Sex|Gender)\s*[:\-]?\s*(\w+)',
            ],
            'nationality': [
                r'(?:Nationality|Nation)\s*[:\-]?\s*(\w+)',
            ],
            'languages': [
                r'(?:Languages?\s+known|Known\s+Languages?)\s*[:\-]?\s*(.*?)(?=\n[A-Z]|\n\s*[A-Z]|$)',
            ],
            'passport': [
                r'(?:Passport\s+No\.?|Passport\s+Number)\s*[:\-]?\s*([\w\d]+|NIL|Nil)',
            ],
            'religion': [
                r'(?:Religion|Caste)\s*[:\-]?\s*(\w+)',
            ],
            'father_name': [
                r'(?:Father\'?s?\s+Name|Father)\s*[:\-]?\s*([A-Z][a-zA-Z\s]+?)(?=\n|$)',
            ],
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    details[key] = self.clean_text(match.group(1))
                    break
        
        # Use spaCy for additional date extraction
        if not details.get('date_of_birth') and self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "DATE" and len(ent.text) > 4:
                    details['date_of_birth'] = ent.text
                    break
        
        return details

    def extract_military_rank(self, text: str) -> str:
        """Extract military rank from text"""
        # Common military ranks to look for (in order of seniority)
        ranks = [
            'Brigadier General', 'Brigadier', 'Colonel', 'Lieutenant Colonel', 'Major', 'Captain', 
            'Lieutenant', 'Second Lieutenant', 'Subedar Major', 'Subedar',
            'Naib Subedar', 'Havildar', 'Naik', 'Lance Naik', 'Sepoy',
            'Wing Commander', 'Squadron Leader', 'Flight Lieutenant',
            'Commodore', 'Rear Admiral', 'Vice Admiral', 'Admiral'
        ]
        
        text_lower = text.lower()
        
        # Look for rank patterns
        rank_patterns = [
            r'(?:rank|present\s+rank|current\s+rank)\s*[:\-]?\s*([a-z\s]+)',
            r'(?:designation|present\s+post|current\s+post)\s*[:\-]?\s*([a-z\s]+)',
            r'(?:served\s+as|working\s+as|posted\s+as)\s+([a-z\s]+)',
        ]
        
        # First try pattern matching
        for pattern in rank_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                for rank in ranks:
                    if rank.lower() in match.lower():
                        return rank
        
        # Direct rank search in text
        for rank in ranks:
            if rank.lower() in text_lower:
                return rank
        
        # Check for common military terms to determine if it's military personnel
        military_terms = ['army', 'navy', 'air force', 'military', 'defence', 'regiment', 'battalion', 'squadron']
        if any(term in text_lower for term in military_terms):
            return "Military Officer"
        
        return "Professional"

    def extract_all_data(self, text: str) -> dict:
        """Extract all resume data with improved accuracy and adaptability"""
        # Analyze document structure first
        structure = self.analyze_document_structure(text)
        
        extracted_data = {}
        
        # Basic information
        extracted_data['Full Name'] = self.extract_name(text)
        extracted_data['Email'] = self.extract_email(text)
        extracted_data['Contact Number'] = self.extract_phone(text)
        extracted_data['Address'] = self.extract_address(text)
        
        # Extract military rank
        extracted_data['Military Rank'] = self.extract_military_rank(text)
        
        # Education (enhanced for different formats)
        education = self.extract_education(text)
        extracted_data['Highest Qualification'] = education['highest_qualification']
        extracted_data['Additional Courses/Certifications'] = education['courses']
        
        # Professional information
        extracted_data['Employment History'] = self.extract_experience(text)
        extracted_data['Key Skills'] = self.extract_skills(text)
        
        # Career objective (adaptive patterns)
        objective_patterns = [
            r'(?:OBJECTIVE|Objective|Career\s+Objective|Professional\s+Summary|PROFILE|Profile)\s*[:\-]?\s*([^\n]+(?:\n[^\n]*){0,3}?)(?=\n\s*[A-Z]{3,}|\n\s*EDUCATION|\n\s*EXPERIENCE|\Z)',
            r'(?:SUMMARY|Summary|About\s+Me|Personal\s+Statement)\s*[:\-]?\s*([^\n]+(?:\n[^\n]*){0,2}?)(?=\n\s*[A-Z]{3,}|\Z)',
            # For bio-data format
            r'(?:Looking\s+to|Seeking\s+to|Aspiring\s+to|Objective\s+is)\s*([^\n]+(?:\n[^\n]*){0,2}?)(?=\n\s*[A-Z]{3,}|\Z)',
        ]
        
        objective_contexts = ['objective', 'summary', 'profile', 'about', 'looking']
        objectives = self.extract_by_patterns_and_context(text, 'objective', objective_patterns, objective_contexts)
        
        # Generate rank-specific objective if none found
        if not objectives and extracted_data.get('Military Rank', 'Professional') != 'Professional':
            military_rank = extracted_data['Military Rank']
            rank_objectives = {
                'Brigadier': f"Experienced {military_rank} seeking to transition strategic military leadership and operational expertise to senior executive roles in civilian sector.",
                'Colonel': f"Accomplished {military_rank} with proven track record in strategic planning and team leadership, seeking to leverage military expertise in civilian management roles.",
                'Lieutenant Colonel': f"Seasoned {military_rank} with extensive experience in operations management and team leadership, transitioning to civilian sector leadership opportunities.",
                'Major': f"Dedicated {military_rank} with strong background in project management and team coordination, seeking to apply military discipline and leadership in civilian career.",
                'Captain': f"Experienced {military_rank} with proven leadership and operational skills, seeking to transition military expertise to civilian professional opportunities."
            }
            
            if military_rank in rank_objectives:
                objectives = [rank_objectives[military_rank]]
            else:
                objectives = [f"Experienced {military_rank} seeking to leverage military experience and leadership skills in civilian career opportunities."]
        
        extracted_data['Career Objective'] = objectives[0] if objectives else ""
        
        # Achievements and references
        extracted_data['Notable Achievements/Awards'] = self.extract_achievements(text)
        extracted_data['References'] = self.extract_references(text)
        
        # Personal details
        extracted_data['Personal Details'] = self.extract_personal_details(text)
        
        # Add document structure info for debugging
        extracted_data['_document_structure'] = structure
        
        return extracted_data

# Enhanced extraction function to replace the original
def extract_resume_data(uploaded_file):
    """Enhanced resume data extraction function with OCR support"""
    try:
        file_type = uploaded_file.type
        text = ""

        if file_type == "application/pdf":
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # First try direct text extraction
            for page in doc:
                text += page.get_text()
            
            # If no text found, try OCR on images
            if not text.strip():
                st.info("📸 No direct text found. Attempting OCR extraction from images...")
                try:
                    import pytesseract
                    from PIL import Image
                    import io
                    
                    progress_bar = st.progress(0)
                    total_pages = len(doc)
                    
                    for page_num in range(total_pages):
                        progress_bar.progress((page_num + 1) / total_pages)
                        page = doc[page_num]
                        
                        # Convert page to image with higher resolution for better OCR
                        mat = fitz.Matrix(2.0, 2.0)  # 2x resolution
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        
                        # Perform OCR
                        image = Image.open(io.BytesIO(img_data))
                        page_text = pytesseract.image_to_string(
                            image, 
                            lang='eng',
                            config='--psm 6 --oem 3'
                        )
                        text += page_text + "\n"
                    
                    progress_bar.empty()
                    
                    if text.strip():
                        st.success(f"✅ OCR successful! Extracted {len(text)} characters from {total_pages} pages.")
                    else:
                        st.warning("⚠️ OCR completed but no readable text found.")
                        
                except ImportError:
                    st.error("""
                    🚫 OCR libraries not available. To process image-based PDFs, please install:
                    ```
                    pip install pytesseract pillow
                    ```
                    Also ensure Tesseract OCR is installed on your system.
                    """)
                    doc.close()
                    return None
                except Exception as ocr_e:
                    st.error(f"OCR failed: {ocr_e}")
                    st.info("💡 Tip: Ensure the PDF contains clear, readable text and isn't corrupted.")
                    doc.close()
                    return None
            else:
                st.success(f"✅ Direct text extraction successful! Extracted {len(text)} characters.")
            
            doc.close()
            
        elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
            # OCR for image files
            try:
                import pytesseract
                from PIL import Image
                image = Image.open(uploaded_file)
                
                with st.spinner("🔍 Performing OCR on image..."):
                    text = pytesseract.image_to_string(image, lang='eng', config='--psm 6 --oem 3')
                
                if text.strip():
                    st.success(f"✅ OCR successful! Extracted {len(text)} characters from image.")
                else:
                    st.warning("⚠️ OCR completed but no readable text found in image.")
                    
            except ImportError:
                st.error("""
                🚫 OCR libraries not available. To process images, please install:
                ```
                pip install pytesseract pillow
                ```
                """)
                return None
            except Exception as ocr_e:
                st.error(f"OCR failed: {ocr_e}")
                return None
        else:
            st.error("Please upload a PDF or image file (PNG, JPG, JPEG) for data extraction")
            return None

        if not text.strip():
            st.error("""
            ❌ Could not extract text from file. 
            
            **Possible solutions:**
            1. **For PDF files:** Ensure the PDF contains selectable text or clear images for OCR
            2. **For scanned documents:** Check if the scan quality is good enough for OCR
            3. **File format:** Try converting to a different format if possible
            4. **OCR setup:** Ensure pytesseract and Tesseract are properly installed
            
            **File information:**
            - File type: {file_type}
            - File size: {len(uploaded_file.getvalue()) if hasattr(uploaded_file, 'getvalue') else 'Unknown'} bytes
            """)
            return None

        # Use enhanced extractor
        with st.spinner("🔍 Analyzing extracted text and identifying resume fields..."):
            extractor = EnhancedResumeExtractor()
            extracted_data = extractor.extract_all_data(text)

        # Validate extraction results
        key_fields = ['Full Name', 'Email', 'Contact Number']
        found_fields = sum(1 for field in key_fields if extracted_data.get(field))
        
        if found_fields == 0:
            st.warning("""
            ⚠️ Limited data could be extracted. 
            
            **Extracted text sample:**
            ```
            {text[:200]}...
            ```
            
            Please verify:
            - Document quality and clarity
            - Text is in English
            - Document contains typical resume information
            """)
        else:
            st.success(f"✅ Successfully identified {found_fields}/{len(key_fields)} key fields!")

        return extracted_data

    except Exception as e:
        st.error(f"❌ Error during data extraction: {str(e)}")
        st.info("💡 Try uploading a different file or check if the file is corrupted.")
        return None

# Add a function to display extracted data in Streamlit
def display_extracted_data(extracted_data):
    """Display extracted data in a structured format"""
    if not extracted_data:
        st.error("No data to display")
        return
    
    st.subheader("📋 Extracted Information")
    
    # Personal Information
    with st.expander("👤 Personal Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {extracted_data.get('Full Name', 'Not found')}")
            st.write(f"**Email:** {extracted_data.get('Email', 'Not found')}")
            st.write(f"**Phone:** {extracted_data.get('Contact Number', 'Not found')}")
            # Display military rank if detected
            if extracted_data.get('Military Rank') and extracted_data.get('Military Rank') != 'Professional':
                st.write(f"**Military Rank:** {extracted_data.get('Military Rank')}")
        
        with col2:
            personal_details = extracted_data.get('Personal Details', {})
            st.write(f"**Date of Birth:** {personal_details.get('date_of_birth', 'Not found')}")
            st.write(f"**Marital Status:** {personal_details.get('marital_status', 'Not found')}")
            st.write(f"**Nationality:** {personal_details.get('nationality', 'Not found')}")
            if personal_details.get('gender'):
                st.write(f"**Gender:** {personal_details.get('gender')}")
            if personal_details.get('father_name'):
                st.write(f"**Father's Name:** {personal_details.get('father_name')}")
        
        if extracted_data.get('Address'):
            st.write(f"**Address:** {extracted_data.get('Address')}")
        
        if personal_details.get('languages'):
            st.write(f"**Languages Known:** {personal_details.get('languages')}")
        if personal_details.get('passport'):
            st.write(f"**Passport:** {personal_details.get('passport')}")
    
    # Education
    with st.expander("🎓 Education & Qualifications"):
        st.write(f"**Highest Qualification:** {extracted_data.get('Highest Qualification', 'Not found')}")
        if extracted_data.get('Additional Courses/Certifications'):
            st.write(f"**Additional Courses:** {extracted_data.get('Additional Courses/Certifications')}")
    
    # Professional Information
    with st.expander("💼 Professional Information"):
        if extracted_data.get('Career Objective'):
            st.write(f"**Career Objective:** {extracted_data.get('Career Objective')}")
        
        if extracted_data.get('Employment History'):
            st.write(f"**Employment History:** {extracted_data.get('Employment History')}")
        
        if extracted_data.get('Key Skills'):
            st.write(f"**Key Skills:** {extracted_data.get('Key Skills')}")
    
    # Achievements
    if extracted_data.get('Notable Achievements/Awards'):
        with st.expander("🏆 Achievements & Awards"):
            st.write(extracted_data.get('Notable Achievements/Awards'))
    
    # References
    if extracted_data.get('References'):
        with st.expander("📞 References"):
            st.write(extracted_data.get('References'))
    
    # Raw data for debugging (optional)
    with st.expander("🔍 Debug: All Extracted Data"):
        st.json(extracted_data)

# AI-powered content generation functions (keeping original ones)
def generate_professional_summary(personal_info, experience, skills, target_position=""):
    """Generate a professional summary using Mistral AI"""
    client = get_mistral_client()
    
    prompt = f"""
    Create a compelling professional summary for a military veteran transitioning to civilian career. 
    
    Personal Information:
    - Name: {personal_info.get('name', 'N/A')}
    - Current/Target Position: {target_position or 'Professional Role'}
    - Military Experience: {experience}
    - Key Skills: {skills}
    
    Write a 3-4 sentence professional summary that:
    1. Highlights military leadership and discipline
    2. Translates military experience to civilian value
    3. Emphasizes relevant skills and achievements
    4. Shows career transition readiness
    
    Keep it concise, professional, and ATS-friendly. Focus on value proposition.
    """
    
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating professional summary: {str(e)}")
        return "Dedicated military professional with proven leadership skills and strong work ethic, seeking to transition expertise to civilian sector."

def generate_work_experience(raw_experience, target_position=""):
    """Enhance work experience descriptions using Mistral AI"""
    client = get_mistral_client()
    
    prompt = f"""
    Transform this military service experience into civilian-friendly resume bullet points:
    
    Raw Military Experience: {raw_experience}
    Target Position: {target_position}
    
    Guidelines:
    1. Translate military jargon to civilian terminology
    2. Quantify achievements with numbers/metrics where possible
    3. Use strong action verbs (Led, Managed, Coordinated, Implemented)
    4. Focus on leadership, project management, and transferable skills
    5. Format as professional bullet points
    6. Emphasize results and impact
    
    Provide 4-6 compelling bullet points that showcase professional value.
    """
    
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating work experience: {str(e)}")
        return raw_experience

def generate_skills_section(raw_skills, target_position=""):
    """Organize and enhance skills using Mistral AI"""
    client = get_mistral_client()
    
    prompt = f"""
    Organize and enhance these skills for a military veteran's resume:
    
    Raw Skills: {raw_skills}
    Target Position: {target_position}
    
    Tasks:
    1. Categorize skills into: Technical Skills, Leadership Skills, Soft Skills
    2. Add relevant civilian equivalent skills
    3. Include military-specific valuable skills (Security Clearance, etc.)
    4. Make skills ATS-friendly with proper keywords
    5. Format as comma-separated list
    
    Return only the enhanced skills list, properly formatted.
    """
    
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating skills: {str(e)}")
        return raw_skills

def generate_achievements(raw_achievements, service_record=""):
    """Generate compelling achievements section"""
    client = get_mistral_client()
    
    prompt = f"""
    Transform military achievements into compelling civilian resume achievements:
    
    Raw Achievements: {raw_achievements}
    Service Context: {service_record}
    
    Guidelines:
    1. Quantify achievements with specific metrics
    2. Highlight leadership and recognition
    3. Translate military awards to civilian understanding
    4. Focus on results and impact
    5. Use powerful action words
    
    Create 3-5 impressive achievement statements.
    """
    
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating achievements: {str(e)}")
        return raw_achievements

# Generate HTML for the resume (updated with modern design)
def get_resume_html(cv_data):
    # Process skills as a list
    skills_list = []
    if cv_data.get('skills'):
        skills_list = [skill.strip() for skill in cv_data['skills'].split(',') if skill.strip()]
    
    # Generate skills HTML
    skills_html = '\n'.join([f'<li>{skill}</li>' for skill in skills_list[:10]]) if skills_list else '<li>Not specified</li>'
    
    # Process experience data
    experience_html = ''
    if cv_data.get('professional_experience'):
        # Split experience into structured format if possible
        exp_parts = cv_data['professional_experience'].split('|')
        for i, exp in enumerate(exp_parts[:3]):  # Limit to 3 experiences
            exp = exp.strip()
            if exp:
                # Try to extract job title, company, and description
                lines = exp.split(' - ')
                job_title = lines[0] if lines else exp[:50] + '...'
                company_info = lines[1] if len(lines) > 1 else 'Military Service'
                description = exp
                
                experience_html += f'''
                <div class="experience-item">
                    <div class="job-title">{job_title}</div>
                    <div class="company-name">{company_info}</div>
                    <div class="job-duration">Service Period</div>
                    <div class="job-description">{description}</div>
                </div>
                '''
    
    if not experience_html:
        experience_html = '''
        <div class="experience-item">
            <div class="job-title">Military Service Professional</div>
            <div class="company-name">Armed Forces</div>
            <div class="job-duration">Career Service</div>
            <div class="job-description">Dedicated military professional with proven leadership and operational expertise.</div>
        </div>
        '''
    
    # Process education data
    education_html = ''
    if cv_data['education']['highest_qualification']:
        education_html += f'''
        <div class="education-item">
            <div class="degree">{cv_data['education']['highest_qualification']}</div>
            <div class="institution">Educational Institution</div>
            <div class="education-duration">Completed</div>
        </div>
        '''
    
    # Process certifications
    certifications_html = ''
    if cv_data['education']['courses']:
        courses = cv_data['education']['courses'].split(';')
        for course in courses[:3]:  # Limit to 3 certifications
            course = course.strip()
            if course:
                certifications_html += f'''
                <div class="certification-item">
                    <div class="cert-name">{course}</div>
                    <div class="cert-authority">Professional Training</div>
                    <div class="cert-year">Certified</div>
                </div>
                '''
    
    if not certifications_html:
        certifications_html = '''
        <div class="certification-item">
            <div class="cert-name">Professional Military Training</div>
            <div class="cert-authority">Armed Forces</div>
            <div class="cert-year">Service Period</div>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume - {cv_data['personal_details']['name']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.4;
            color: #333;
            background-color: #f5f5f5;
        }}

        .resume-container {{
            max-width: 800px;
            margin: 20px auto;
            background-color: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

       .header {{
    background-color: white;
    color: #333;
    padding: 30px;
    position: relative;
    border-bottom: 2px solid #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 20px; /* This moves the header 20px down */
}}
        .profile-image {{
            position: absolute;
            top: 50%;
            right: 30px;
            transform: translateY(-50%);
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background-color: #666;
            background-size: cover;
            background-position: center;
            border: 3px solid #2d9da6;
        }}

        .header-content {{
            text-align: left;
            flex: 1;
            height: 50px; /* Reduced height */
    margin-top: 10px;
        }}

        .name {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #000;
        }}

        .title {{
            font-size: 14px;
            color: #666;
            font-weight: normal;
        }}

        .main-content {{
            display: flex;
        }}

        .left-column {{
            background-color: #2d9da6;
            color: white;
            width: 35%;
            padding: 0;
        }}

        .section {{
            padding: 25px 20px;
        }}

        .section-title {{
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            color: white;
        }}

        .right-column {{
            width: 65%;
            padding: 0;
        }}

        .right-section {{
            padding: 25px 30px;
            border-bottom: 1px solid #eee;
        }}

        .right-section:last-child {{
            border-bottom: none;
        }}

        .right-section-title {{
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            color: #2d9da6;
        }}

        .contact-item {{
            margin-bottom: 10px;
            font-size: 12px;
        }}

        .contact-label {{
            font-weight: bold;
            display: inline-block;
            width: 60px;
        }}

        .objective-text {{
            font-size: 12px;
            line-height: 1.5;
            text-align: justify;
        }}

        .skills-list {{
            list-style: none;
        }}

        .skills-list li {{
            font-size: 12px;
            margin-bottom: 8px;
            position: relative;
            padding-left: 15px;
        }}

        .skills-list li:before {{
            content: '•';
            position: absolute;
            left: 0;
            color: white;
        }}

        .experience-item {{
            margin-bottom: 20px;
        }}

        .job-title {{
            font-weight: bold;
            font-size: 14px;
            color: #333;
            margin-bottom: 2px;
        }}

        .company-name {{
            font-style: italic;
            font-size: 12px;
            color: #666;
            margin-bottom: 2px;
        }}

        .job-duration {{
            font-size: 11px;
            color: #999;
            margin-bottom: 8px;
        }}

        .job-description {{
            font-size: 12px;
            line-height: 1.5;
        }}

        .job-description ul {{
            margin-left: 15px;
            margin-top: 5px;
        }}

        .job-description li {{
            margin-bottom: 3px;
            font-size: 11px;
        }}

        .education-item {{
            margin-bottom: 15px;
        }}

        .degree {{
            font-weight: bold;
            font-size: 13px;
            color: #333;
            margin-bottom: 2px;
        }}

        .institution {{
            font-size: 12px;
            color: #666;
            font-style: italic;
            margin-bottom: 2px;
        }}

        .education-duration {{
            font-size: 11px;
            color: #999;
        }}

        .certification-item {{
            margin-bottom: 10px;
        }}

        .cert-name {{
            font-weight: bold;
            font-size: 12px;
            color: #333;
        }}

        .cert-authority {{
            font-size: 11px;
            color: #666;
            font-style: italic;
        }}

        .cert-year {{
            font-size: 11px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="resume-container">
        <!-- Header Section -->
        <div class="header">
            <div class="header-content">
                <div class="name">{cv_data['personal_details']['name']}</div>
                <div class="title">{cv_data['personal_details']['position']}</div>
            </div>
            {cv_data['personal_details']['photo'] if cv_data['personal_details']['photo'] else '<div class="profile-image"></div>'}
        </div>

        <div class="main-content">
            <!-- Left Column -->
            <div class="left-column">
                <!-- Contact Section -->
                <div class="section">
                    <div class="section-title">CONTACT</div>
                    <div class="contact-item">
                        <span class="contact-label">Phone:</span>
                        <span>{cv_data['personal_details']['contact']}</span>
                    </div>
                    <div class="contact-item">
                        <span class="contact-label">Email:</span>
                        <span>{cv_data['personal_details']['email']}</span>
                    </div>
                    <div class="contact-item">
                        <span class="contact-label">Address:</span>
                        <span>{cv_data['personal_details']['address']}</span>
                    </div>
                </div>

                <!-- Objective Section -->
                <div class="section">
                    <div class="section-title">OBJECTIVE</div>
                    <div class="objective-text">
                        {cv_data['objective'] if cv_data['objective'] else 'Dedicated professional seeking to leverage military experience and skills in civilian career opportunities.'}
                    </div>
                </div>

                <!-- Skills Section -->
                <div class="section">
                    <div class="section-title">SKILLS</div>
                    <ul class="skills-list">
                        {skills_html}
                    </ul>
                </div>
            </div>

            <!-- Right Column -->
            <div class="right-column">
                <!-- Professional Career Section -->
                <div class="right-section">
                    <div class="right-section-title">PROFESSIONAL CAREER</div>
                    <div>
                        {experience_html}
                    </div>
                </div>

                <!-- Academic Background Section -->
                <div class="right-section">
                    <div class="right-section-title">ACADEMIC BACKGROUND</div>
                    <div>
                        {education_html if education_html else '<div class="education-item"><div class="degree">Educational Background</div><div class="institution">To be updated</div><div class="education-duration">-</div></div>'}
                    </div>
                </div>

                <!-- Certifications Section -->
                <div class="right-section">
                    <div class="right-section-title">CERTIFICATIONS</div>
                    <div>
                        {certifications_html}
                    </div>
                </div>

                {('<!-- Achievements Section -->' + 
                '<div class="right-section">' + 
                '<div class="right-section-title">ACHIEVEMENTS</div>' + 
                '<div class="job-description">' + cv_data.get("achievements", "") + '</div>' + 
                '</div>') if cv_data.get('achievements') else ''}

                {('<!-- References Section -->' + 
                '<div class="right-section">' + 
                '<div class="right-section-title">REFERENCES</div>' + 
                '<div class="job-description">' + cv_data.get("references", "") + '</div>' + 
                '</div>') if cv_data.get('references') else ''}
            </div>
        </div>
    </div>
</body>
</html>'''
    return html

# Convert HTML to PDF bytes (keeping original)
def html_to_pdf_bytes(html_content):
    result = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html_content), dest=result)
    return result.getvalue()

# Enhanced form processing with AI generation (keeping original)
def process_with_ai_enhancement(extracted_data, target_position=""):
    """Process extracted data and enhance with AI-generated content"""
    
    if not extracted_data:
        return None
    
    # Generate AI-enhanced content
    with st.spinner("Generating professional content with AI..."):
        
        # Create enhanced data structure
        enhanced_data = extracted_data.copy()
        
        # Generate professional summary
        if st.session_state.get('generate_summary', True):
            enhanced_data['Professional Summary'] = generate_professional_summary(
                {'name': extracted_data.get('Full Name', '')},
                extracted_data.get('Employment History', ''),
                extracted_data.get('Key Skills', ''),
                target_position
            )
        
        # Enhance work experience
        if extracted_data.get('Employment History') and st.session_state.get('generate_experience', True):
            enhanced_data['Enhanced Experience'] = generate_work_experience(
                extracted_data.get('Employment History', ''),
                target_position
            )
        
        # Enhance skills
        if extracted_data.get('Key Skills') and st.session_state.get('generate_skills', True):
            enhanced_data['Enhanced Skills'] = generate_skills_section(
                extracted_data.get('Key Skills', ''),
                target_position
            )
        
        # Generate achievements
        if extracted_data.get('Notable Achievements/Awards') and st.session_state.get('generate_achievements', True):
            enhanced_data['Enhanced Achievements'] = generate_achievements(
                extracted_data.get('Notable Achievements/Awards', ''),
                extracted_data.get('Employment History', '')
            )
    
    return enhanced_data

# LLM-powered full form enhancement (keeping original)
def llm_enhance_full_resume_data(raw_data, target_position=""):
    """Use Mistral to enhance and structure all resume fields from raw extracted data."""
    import json
    client = get_mistral_client()
    
    # Get military rank for better positioning
    military_rank = raw_data.get('Military Rank', 'Professional')
    if not target_position and military_rank != 'Professional':
        target_position = military_rank
    
    # Pass the raw extracted data as JSON for better parsing
    raw_json = json.dumps(raw_data, ensure_ascii=False)
    prompt = f'''
You are an expert resume writer and information extractor. Given the following JSON object containing raw extracted information from a military service document, extract and enhance all the following fields for a professional civilian resume:

MUST extract and enhance (if present in the document):
- name (full name)
- address (complete address)
- contact (phone number in proper format)
- email (valid email address)
- education (highest qualification, certifications/courses)
- professional experience (detailed work history)
- skills (technical and soft skills)
- achievements (awards, recognitions, accomplishments)
- references (contact persons if mentioned)

ENHANCEMENT RULES:
1. Do NOT hallucinate or invent information
2. Use only the extracted data provided
3. Rewrite content for clarity and professionalism
4. Make it civilian-friendly (translate military terms)
5. Format properly for resume presentation
6. If a field is missing, leave it blank or use "Available upon request" for references

Return your answer as a JSON object with these exact keys:
{{
  "personal_details": {{
    "name": "extracted full name",
    "position": "{target_position or 'Professional'}",
    "contact": "formatted phone number",
    "email": "email address",
    "address": "complete address",
    "photo": ""
  }},
  "objective": "professional summary/career objective (2-3 sentences)",
  "skills": "comma-separated list of skills",
  "professional_experience": "enhanced work experience description",
  "education": {{
    "highest_qualification": "highest degree/qualification",
    "courses": "additional courses and certifications"
  }},
  "achievements": "enhanced achievements and awards",
  "references": "reference information or 'Available upon request'"
}}

Target Position: {target_position}
Raw Extracted Data (JSON):
{raw_json}

Respond ONLY with the JSON object, no explanation or additional text.
'''
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.6
        )
        import json
        # Find the first { ... } block in the response (in case LLM adds text)
        import re
        response_text = response.choices[0].message.content.strip()
        match = re.search(r'\{[\s\S]*\}', response_text)
        if match:
            parsed_data = json.loads(match.group(0))
            # Validate and ensure all required fields exist
            required_structure = {
                "personal_details": {
                    "name": raw_data.get('Full Name', ''),
                    "position": target_position or 'Professional',
                    "contact": raw_data.get('Contact Number', ''),
                    "email": raw_data.get('Email', ''),
                    "address": raw_data.get('Address', ''),
                    "photo": ""
                },
                "objective": raw_data.get('Career Objective', ''),
                "skills": raw_data.get('Key Skills', ''),
                "professional_experience": raw_data.get('Employment History', ''),
                "education": {
                    "highest_qualification": raw_data.get('Highest Qualification', ''),
                    "courses": raw_data.get('Additional Courses/Certifications', '')
                },
                "achievements": raw_data.get('Notable Achievements/Awards', ''),
                "references": raw_data.get('References', 'Available upon request')
            }
            
            # Merge enhanced data with fallback values
            for key in required_structure:
                if key not in parsed_data:
                    parsed_data[key] = required_structure[key]
                elif isinstance(required_structure[key], dict):
                    for subkey in required_structure[key]:
                        if subkey not in parsed_data.get(key, {}):
                            parsed_data[key][subkey] = required_structure[key][subkey]
            
            return parsed_data
        else:
            st.warning("Could not parse enhanced resume data from LLM. Using raw extracted data.")
            return None
    except Exception as e:
        st.error(f"Error enhancing full resume data: {str(e)}")
        return None

# Modified main application
def main():
    # st.set_page_config(page_title="NeoResuMaker", layout="wide", page_icon="")  # Removed to prevent conflict with main_app.py
    
    # Add CSS for larger fonts and better visibility
    st.markdown("""
    <style>
        /* Main app styling with larger fonts */
        .stApp {
            background-color: #000000;
            color: #ffffff;
            font-size: 20px;
        }
        
        /* Headers and titles - much larger */
        h1 {
            color: #ffffff !important;
            font-size: 4rem !important;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-size: 2.5rem !important;
            font-weight: 700;
            margin: 1.5rem 0;
        }
        
        /* Section headers specifically larger */
        .stMarkdown h3 {
            color: #ffffff !important;
            font-size: 2.8rem !important;
            font-weight: 700;
            margin: 2rem 0 1.5rem 0;
        }
        
        /* Main content text - larger */
        .stMarkdown {
            color: #ffffff;
            font-size: 1.4rem;
            line-height: 1.6;
        }
        
        /* Input fields and labels - much larger */
        .stTextInput > label, .stTextArea > label, .stSelectbox > label, .stFileUploader > label {
            color: #ffffff !important;
            font-size: 1.4rem !important;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        /* Input field text */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            font-size: 1.2rem !important;
            padding: 0.8rem !important;
        }
        
        /* Selectbox text */
        .stSelectbox > div > div > div {
            font-size: 1.2rem !important;
        }
        
        /* Buttons - much larger with blue color */
        .stButton > button {
            background: #1f77b4 !important;
            color: white !important;
            border: none;
            border-radius: 15px;
            padding: 1.2rem 3rem;
            font-weight: 700;
            font-size: 2.8rem;
            min-height: 4rem;
            width: 100%;
        }
        
        .stButton > button:hover {
            background: #0d5aa7 !important;
            transform: scale(1.02);
        }
        
        /* Tabs - appropriately sized headers */
        .stTabs [data-baseweb="tab-list"] {
            font-size: 2.5rem !important;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 1.8rem 2.8rem;
            font-weight: 700;
            min-height: 4.5rem;
            font-size: 2.5rem !important;
        }
        
        /* Tab specific text styling */
        .stTabs [data-baseweb="tab"] span {
            font-size: 2.5rem !important;
            font-weight: 700;
        }
        
        /* Additional tab styling for better visibility */
        .stTabs [data-baseweb="tab-list"] button {
            font-size: 2.5rem !important;
            font-weight: 700;
            color: #ffffff !important;
        }
        
        /* Force tab text to be larger */
        .stTabs [data-baseweb="tab"] div {
            font-size: 2.5rem !important;
            font-weight: 700;
        }
        
        /* Override any default tab styling */
        .stTabs [data-baseweb="tab"] * {
            font-size: 2.5rem !important;
            font-weight: 700;
        }
        
        /* Info boxes - larger */
        .stInfo, .stSuccess, .stWarning, .stError {
            font-size: 1.3rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        /* File uploader styling */
        .stFileUploader {
            background: #222222;
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
        }
        
        /* Expander - larger */
        .streamlit-expanderHeader {
            font-size: 1.4rem !important;
            color: #ffffff !important;
            font-weight: 600;
            padding: 1rem;
        }
        
        /* Columns and containers */
        .css-1r6slb0 {
            background-color: #111111;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #000000;
            color: #ffffff;
            font-size: 1.2rem;
        }
        
        /* Progress bars */
        .stProgress {
            margin: 1rem 0;
        }
        
        /* Metrics */
        [data-testid="metric-container"] {
            background-color: #222222;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        /* Subheaders in forms - larger */
        .stForm h4, .stForm .stSubheader {
            color: #ffffff !important;
            font-size: 2.2rem !important;
            font-weight: 700;
            margin: 1.5rem 0 1rem 0;
        }
        
        /* Specific styling for subheader elements */
        [data-testid="stSubheader"] {
            color: #ffffff !important;
            font-size: 2.2rem !important;
            font-weight: 700;
            margin: 1.5rem 0 1rem 0;
        }
        
        /* Remove small text */
        small {
            font-size: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🎖 Resume Builder")
    st.markdown("Transform military experience into professional civilian resumes")
    
    # Add tabs for better organization
    tab1, tab2, tab3 = st.tabs(["📄 Upload Document", "✏ Manual Entry", "📊 Preview & Export"])
    
    with tab1:
        st.markdown("### Upload Your Military Document")
        
        uploaded_file = st.file_uploader(
            "Choose PDF or Image file", 
            type=["pdf", "png", "jpg", "jpeg"],
            help="Upload service records, discharge papers, or biodata"
        )
        
        if uploaded_file:
            st.success(f"📁 **{uploaded_file.name}** uploaded successfully!")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("🔍 Extract Data", type="primary"):
                    st.markdown("---")
                    extracted_data = extract_resume_data(uploaded_file)
                    if extracted_data:
                        st.session_state.extracted_data = extracted_data
                        st.markdown("---")
                        st.success("✅ Data extraction completed! Switch to 'Data Preview' tab to see results.")
                    else:
                        st.markdown("---")
                        st.error("❌ Failed to extract data from the document.")
            
            with col2:
                if st.button("🤖 Extract + AI Enhancement"):
                    st.markdown("---")
                    with st.spinner("Extracting and enhancing with AI..."):
                        # Get target position first
                        target_position = st.session_state.get('target_position', '')
                        
                        extracted_data = extract_resume_data(uploaded_file)
                        if extracted_data:
                            # Use LLM to enhance and fill all fields
                            enhanced_data = llm_enhance_full_resume_data(extracted_data, target_position)
                            if enhanced_data:
                                st.session_state.form_data = enhanced_data
                                st.session_state.extracted_data = extracted_data
                                st.success("✅ Data extracted and enhanced with AI!")
                                st.info("Switch to 'Manual Entry' tab to review and edit the form.")
                            else:
                                st.session_state.extracted_data = extracted_data
                                st.warning("⚠ AI enhancement failed, but raw data extracted successfully.")
        
        # Sidebar for AI options
        with st.sidebar:
            st.header("🤖 AI Enhancement")
            st.session_state['generate_summary'] = st.checkbox("Professional Summary", value=True)
            st.session_state['generate_experience'] = st.checkbox("Work Experience", value=True)
            st.session_state['generate_skills'] = st.checkbox("Skills Organization", value=True)
            
            # Target position input
            st.session_state['target_position'] = st.text_input(
                "🎯 Target Position", 
                value=st.session_state.get('target_position', ''),
                placeholder="e.g., Project Manager"
            )
    
    with tab2:
        st.markdown("### Complete Your Profile")
        
        with st.form("cv_form"):
            col1, col2 = st.columns(2)

            form_data = st.session_state.get('form_data', {})
            extracted_data = st.session_state.get('extracted_data', {})
            personal = form_data.get('personal_details', {})
            education = form_data.get('education', {})

            with col1:
                st.subheader("👤 Personal Details")
                name = st.text_input("Full Name", value=personal.get("name", extracted_data.get("Full Name", "")))
                position = st.text_input("Designation", value=personal.get("position", extracted_data.get("Military Rank", st.session_state.get('target_position', ''))))
                contact = st.text_input("Contact Number", value=personal.get("contact", extracted_data.get("Contact Number", "")))
                email = st.text_input("Email", value=personal.get("email", extracted_data.get("Email", "")))
                address = st.text_area("Address", value=personal.get("address", extracted_data.get("Address", "")))
                photo = st.file_uploader("Upload Photo", type=["jpg", "png", "jpeg"])
                
                # Additional personal details
                personal_details = extracted_data.get('Personal Details', {})
                st.subheader("📋 Additional Info")
                date_of_birth = st.text_input("Date of Birth", value=personal_details.get("date_of_birth", ""))
                marital_status = st.selectbox("Marital Status", 
                    ["", "Single", "Married", "Divorced", "Widowed"], 
                    index=0 if not personal_details.get("marital_status") else ["", "Single", "Married", "Divorced", "Widowed"].index(personal_details.get("marital_status", "")) if personal_details.get("marital_status", "") in ["Single", "Married", "Divorced", "Widowed"] else 0)
                nationality = st.text_input("Nationality", value=personal_details.get("nationality", ""))
                languages = st.text_input("Languages Known", value=personal_details.get("languages", ""))

            with col2:
                st.subheader("📝 Professional Summary")
                objective = st.text_area(
                    "Career Objective/Professional Summary", 
                    value=form_data.get("objective", extracted_data.get("Career Objective", "")), 
                    height=100
                )

                st.subheader("🛠 Skills")
                skills = st.text_area(
                    "Key Skills", 
                    value=form_data.get("skills", extracted_data.get("Key Skills", "")), 
                    height=100
                )

                st.subheader("💼 Professional Experience")
                professional_experience = st.text_area(
                    "Professional Experience", 
                    value=form_data.get("professional_experience", extracted_data.get("Employment History", "")), 
                    height=200
                )

                st.subheader("🎓 Education")
                highest_qualification = st.text_input(
                    "Highest Qualification", 
                    value=education.get("highest_qualification", extracted_data.get("Highest Qualification", ""))
                )
                courses = st.text_area(
                    "Certifications & Courses", 
                    value=education.get("courses", extracted_data.get("Additional Courses/Certifications", ""))
                )

                st.subheader("🏆 Achievements")
                achievements = st.text_area(
                    "Achievements", 
                    value=form_data.get("achievements", extracted_data.get("Notable Achievements/Awards", "")), 
                    height=100
                )

                st.subheader("📞 References")
                references = st.text_area("References", value=form_data.get("references", extracted_data.get("References", "")))

            submit_btn = st.form_submit_button("🚀 Generate AI-Enhanced Resume", type="primary")
        
        # Handle form submission and show preview/download
        if submit_btn:
            # Prepare the data for the resume
            if photo is not None:
                photo_bytes = photo.read()
                photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                photo_src = f"data:{photo.type};base64,{photo_base64}"
                photo_html = f"<img src='{photo_src}' alt='Photo' class='photo'>"
            else:
                photo_html = ""

            cv_data = {
                "personal_details": {
                    "name": name,
                    "position": position,
                    "contact": contact,
                    "email": email,
                    "address": address,
                    "photo": photo_html
                },
                "objective": objective,
                "skills": skills,
                "professional_experience": professional_experience,
                "education": {
                    "highest_qualification": highest_qualification,
                    "courses": courses
                },
                "achievements": achievements if achievements else None,
                "references": references if references else None
            }

            # Generate HTML and PDF
            resume_html = get_resume_html(cv_data)
            pdf_bytes = html_to_pdf_bytes(resume_html)

            # Show preview and download
            st.markdown("---")
            st.markdown("### 📄 Your Resume")
            with st.expander("👀 Preview", expanded=True):
                st.components.v1.html(resume_html, height=1000, scrolling=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=f"{name.replace(' ', '_')}_resume.pdf" if name else "military_resume.pdf",
                    mime="application/pdf"
                )
            
            with col2:
                st.download_button(
                    label="💾 Download HTML",
                    data=resume_html.encode('utf-8'),
                    file_name=f"{name.replace(' ', '_')}_resume.html" if name else "military_resume.html",
                    mime="text/html"
                )
    
    with tab3:
        st.markdown("### 📊 Data Preview")
        
        if 'extracted_data' in st.session_state:
            display_extracted_data(st.session_state.extracted_data)
            
            # Option to export extracted data
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📋 Copy Extracted Data"):
                    st.code(str(st.session_state.extracted_data), language='json')
            
            with col2:
                extracted_json = json.dumps(st.session_state.extracted_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="💾 Download Extracted Data (JSON)",
                    data=extracted_json.encode('utf-8'),
                    file_name="extracted_resume_data.json",
                    mime="application/json"
                )
        else:
            st.info("📤 Upload a document in the 'Document Upload' tab to see extracted data here.")
            st.markdown("""
            *What you'll see here:*
            - 👤 Personal information (name, contact, address)
            - 🎓 Educational qualifications and certifications
            - 💼 Professional experience and career history
            - 🛠 Skills and competencies
            - 🏆 Achievements and awards
            - 📋 All other relevant details
            """)

if __name__ == "__main__":
    main()