import PyPDF2
import docx
import re
import json
from typing import Dict, List, Optional
from pathlib import Path
import spacy
from collections import Counter

class ResumeParser:
    """Parse resumes and extract relevant information for job matching"""
    
    def __init__(self):
        self.nlp = None
        try:
            # Load spaCy model for NLP processing
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("⚠️ spaCy model not found. Install with: python -m spacy download en_core_web_sm")
        
        # Common skills and technologies
        self.tech_skills = {
            'programming': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'node.js', 'asp.net', 'laravel'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb', 'sqlite', 'oracle'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'gitlab'],
            'tools': ['git', 'jira', 'confluence', 'slack', 'figma', 'postman', 'swagger'],
            'ai_ml': ['tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'opencv']
        }
        
        # Job titles and roles
        self.job_titles = [
            'software engineer', 'developer', 'programmer', 'full stack', 'frontend', 'backend',
            'data scientist', 'machine learning engineer', 'devops engineer', 'site reliability engineer',
            'product manager', 'project manager', 'technical lead', 'architect', 'consultant'
        ]
    
    def parse_resume(self, file_path: str) -> Dict:
        """Parse resume file and extract structured information"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        # Extract text based on file type
        if file_path.suffix.lower() == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            text = self._extract_docx_text(file_path)
        elif file_path.suffix.lower() == '.txt':
            text = self._extract_txt_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Parse the extracted text
        return self._parse_text(text)
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {e}")
    
    def _extract_txt_text(self, file_path: Path) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error reading TXT: {e}")
    
    def _parse_text(self, text: str) -> Dict:
        """Parse resume text and extract structured information"""
        text = text.lower()
        
        # Extract basic information
        parsed_data = {
            'name': self._extract_name(text),
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'location': self._extract_location(text),
            'skills': self._extract_skills(text),
            'experience': self._extract_experience(text),
            'education': self._extract_education(text),
            'job_titles': self._extract_job_titles(text),
            'years_experience': self._extract_years_experience(text),
            'summary': self._extract_summary(text)
        }
        
        return parsed_data
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name"""
        # Look for common name patterns at the beginning
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 2 and len(line) < 50:
                # Simple heuristic: name is usually in title case and not all caps
                if line[0].isupper() and not line.isupper():
                    return line.title()
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group() if match else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (123) 456-7890
            r'\b\d{10}\b'  # 1234567890
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location/city"""
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == 'GPE':  # Geographical location
                    return ent.text
        return None
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical skills from resume"""
        skills = {}
        
        for category, skill_list in self.tech_skills.items():
            found_skills = []
            for skill in skill_list:
                # Look for skill mentions with word boundaries
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    found_skills.append(skill)
            if found_skills:
                skills[category] = found_skills
        
        return skills
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience with proper parsing of job titles, companies, and dates"""
        experience = []
        
        # Common job title patterns
        job_title_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Engineer|Developer|Manager|Analyst|Specialist|Lead|Architect|Consultant|Coordinator|Director|VP|CTO|CEO))',
            r'(Senior|Junior|Lead|Principal|Staff)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(Software|Data|DevOps|Product|Project|Business|Systems|Network|Security|Cloud|Machine Learning|AI|Full Stack|Frontend|Backend)\s+([A-Z][a-z]+)'
        ]
        
        # Date patterns
        date_patterns = [
            r'(\d{4})\s*[-–—]\s*(\d{4}|present|current|now)',
            r'(\d{4})\s+to\s+(\d{4}|present|current|now)',
            r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4}|present|current|now)',
            r'(\w+\s+\d{4})\s+to\s+(\w+\s+\d{4}|present|current|now)'
        ]
        
        lines = text.split('\n')
        in_experience_section = False
        in_education_section = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Check for section headers
            if any(edu_header in line_lower for edu_header in ['education', 'academic', 'degree', 'graduation']):
                in_education_section = True
                in_experience_section = False
                continue
            
            if any(exp_header in line_lower for exp_header in ['experience', 'work history', 'employment', 'career', 'professional experience', 'work experience']):
                in_experience_section = True
                in_education_section = False
                continue
            
            # Skip if in education section
            if in_education_section:
                continue
            
            # Look for job entries (title | company | dates pattern)
            job_entry = self._parse_job_entry(line_stripped, lines, i, job_title_patterns, date_patterns)
            if job_entry:
                experience.append(job_entry)
                continue
            
            # Look for date patterns in current line
            for pattern in date_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    # Try to extract job info from surrounding context
                    job_entry = self._extract_job_from_context(lines, i, match.group(), job_title_patterns)
                    if job_entry:
                        experience.append(job_entry)
                    break
        
        return experience
    
    def _parse_job_entry(self, line: str, lines: List[str], line_index: int, job_title_patterns: List[str], date_patterns: List[str]) -> Optional[Dict]:
        """Parse a single job entry line"""
        # Common patterns: "Job Title | Company | Dates" or "Job Title at Company | Dates"
        patterns = [
            r'^(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)$',  # Title | Company | Dates
            r'^(.+?)\s+at\s+(.+?)\s*\|\s*(.+)$',  # Title at Company | Dates
            r'^(.+?)\s*,\s*(.+?)\s*\|\s*(.+)$',   # Title, Company | Dates
            r'^(.+?)\s*\|\s*(.+)$',               # Title | Company (no dates)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                
                if len(groups) >= 2:
                    potential_title = groups[0].strip()
                    potential_company = groups[1].strip()
                    dates = groups[2].strip() if len(groups) > 2 else ""
                    
                    # Validate job title
                    if self._is_valid_job_title(potential_title):
                        # Extract dates if not provided
                        if not dates:
                            dates = self._extract_dates_from_context(lines, line_index, date_patterns)
                        
                        return {
                            'title': potential_title,
                            'company': potential_company,
                            'dates': dates,
                            'line': line,
                            'confidence': 'high'
                        }
        
        return None
    
    def _is_valid_job_title(self, title: str) -> bool:
        """Check if a string looks like a valid job title"""
        title_lower = title.lower()
        
        # Must contain job-related keywords
        job_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'specialist', 'lead', 'architect',
            'consultant', 'coordinator', 'director', 'vp', 'cto', 'ceo', 'officer', 'executive',
            'associate', 'senior', 'junior', 'principal', 'staff', 'head', 'chief'
        ]
        
        # Must not be education-related
        edu_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'gpa']
        
        # Check for job keywords
        has_job_keyword = any(keyword in title_lower for keyword in job_keywords)
        
        # Check for education keywords (should not have)
        has_edu_keyword = any(keyword in title_lower for keyword in edu_keywords)
        
        # Must be reasonable length
        reasonable_length = 5 <= len(title.split()) <= 8
        
        return has_job_keyword and not has_edu_keyword and reasonable_length
    
    def _extract_dates_from_context(self, lines: List[str], line_index: int, date_patterns: List[str]) -> str:
        """Extract dates from context around a line"""
        # Check current line and surrounding lines
        for i in range(max(0, line_index-1), min(len(lines), line_index+2)):
            line = lines[i].strip()
            for pattern in date_patterns:
                match = re.search(pattern, line.lower())
                if match:
                    return match.group()
        return ""
    
    def _extract_job_from_context(self, lines: List[str], line_index: int, dates: str, job_title_patterns: List[str]) -> Optional[Dict]:
        """Extract job information from context around a line with dates"""
        # Look for job title and company in surrounding lines
        for i in range(max(0, line_index-2), min(len(lines), line_index+3)):
            line = lines[i].strip()
            if not line or line == lines[line_index].strip():
                continue
            
            # Try to find job title
            for pattern in job_title_patterns:
                match = re.search(pattern, line)
                if match:
                    title = match.group()
                    # Look for company in nearby lines
                    company = self._extract_company_from_context(lines, i)
                    if company:
                        return {
                            'title': title,
                            'company': company,
                            'dates': dates,
                            'line': lines[line_index].strip(),
                            'confidence': 'medium'
                        }
        
        return None
    
    def _extract_company_from_context(self, lines: List[str], line_index: int) -> Optional[str]:
        """Extract company name from context around experience line"""
        # Check lines before and after the experience line
        for i in range(max(0, line_index-2), min(len(lines), line_index+3)):
            line = lines[i].strip()
            if line and len(line) < 100:
                # Look for company indicators
                if any(indicator in line.lower() for indicator in ['inc', 'corp', 'ltd', 'company', 'tech', 'solutions', 'systems', 'group', 'partners']):
                    return line
                # Also check for common company name patterns
                if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|Ltd|LLC|Company|Technologies|Solutions|Systems|Group|Partners)$', line):
                    return line
        return None
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        
        # Look for education patterns
        edu_patterns = [
            r'(bachelor|master|phd|b\.s\.|m\.s\.|ph\.d\.)',
            r'(university|college|institute)',
            r'(\d{4})\s*[-–]\s*(\d{4})'  # Graduation years
        ]
        
        lines = text.split('\n')
        for line in lines:
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in edu_patterns):
                education.append({'line': line.strip()})
        
        return education
    
    def _extract_job_titles(self, text: str) -> List[str]:
        """Extract job titles from resume using improved parsing"""
        titles = []
        
        # Job title patterns
        title_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Engineer|Developer|Manager|Analyst|Specialist|Lead|Architect|Consultant|Coordinator|Director|VP|CTO|CEO))',
            r'(Senior|Junior|Lead|Principal|Staff)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(Software|Data|DevOps|Product|Project|Business|Systems|Network|Security|Cloud|Machine Learning|AI|Full Stack|Frontend|Backend)\s+([A-Z][a-z]+)'
        ]
        
        # Extract from experience section
        experience = self._extract_experience(text)
        for exp in experience:
            if 'title' in exp and exp['title']:
                titles.append(exp['title'])
        
        # Also look for job titles in the text using patterns
        for pattern in title_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle groups
                    title = ' '.join(match)
                else:
                    title = match
                
                if self._is_valid_job_title(title):
                    titles.append(title)
        
        # Remove duplicates and return
        return list(set(titles))
    
    def _extract_years_experience(self, text: str) -> Optional[float]:
        """Calculate full-time years of experience from work history"""
        from datetime import datetime, date
        import re
        
        # Full-time job indicators
        full_time_indicators = [
            'full-time', 'full time', 'fulltime', 'permanent', 'regular',
            'full-time employee', 'full time employee', 'staff', 'employee'
        ]
        
        # Non-full-time indicators (to exclude)
        exclude_indicators = [
            'intern', 'internship', 'part-time', 'part time', 'parttime',
            'freelance', 'freelancer', 'contract', 'contractor', 'consultant',
            'volunteer', 'temporary', 'temp', 'seasonal', 'summer',
            'co-op', 'coop', 'cooperative', 'student', 'graduate'
        ]
        
        # Date patterns for parsing
        date_patterns = [
            r'(\d{4})\s*[-–—]\s*(\d{4}|present|current|now)',
            r'(\d{4})\s+to\s+(\d{4}|present|current|now)',
            r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4}|present|current|now)',
            r'(\w+\s+\d{4})\s+to\s+(\w+\s+\d{4}|present|current|now)',
        ]
        
        # Month mapping
        month_map = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
            'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        def parse_date(date_string: str) -> Optional[date]:
            """Parse date string to date object"""
            if not date_string:
                return None
            
            date_string = date_string.lower().strip()
            
            # Handle "present", "current", "now"
            if date_string in ['present', 'current', 'now']:
                return date.today()
            
            try:
                # Year only
                if re.match(r'^\d{4}$', date_string):
                    year = int(date_string)
                    return date(year, 1, 1)  # January 1st of that year
                
                # Month Year
                month_year_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})', date_string)
                if month_year_match:
                    month_name = month_year_match.group(1)
                    year = int(month_year_match.group(2))
                    month = month_map.get(month_name.lower())
                    if month:
                        return date(year, month, 1)
                
                # MM/DD/YYYY or MM-DD-YYYY
                date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_string)
                if date_match:
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    year = int(date_match.group(3))
                    return date(year, month, day)
                
                # YYYY/MM/DD or YYYY-MM-DD
                date_match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', date_string)
                if date_match:
                    year = int(date_match.group(1))
                    month = int(date_match.group(2))
                    day = int(date_match.group(3))
                    return date(year, month, day)
                    
            except Exception as e:
                print(f"⚠️ Could not parse date: {date_string} - {e}")
            
            return None
        
        def is_full_time_position(context_text: str) -> bool:
            """Check if position is full-time based on context"""
            context_lower = context_text.lower()
            
            # Check for non-full-time indicators first
            for indicator in exclude_indicators:
                if indicator in context_lower:
                    return False
            
            # Check for explicit full-time indicators
            for indicator in full_time_indicators:
                if indicator in context_lower:
                    return True
            
            # Default to full-time if no indicators found (assume full-time)
            return True
        
        # Extract work experience entries
        experience_entries = []
        lines = text.split('\n')
        
        # Track if we're in education section
        in_education_section = False
        in_experience_section = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Skip empty lines
            if not line_lower:
                continue
            
            # Check for section headers
            if any(edu_header in line_lower for edu_header in ['education', 'academic', 'degree', 'university', 'college', 'bachelor', 'master', 'phd', 'graduation']):
                in_education_section = True
                in_experience_section = False
                print(f"📚 Entering education section: {line.strip()}")
                continue
            
            if any(exp_header in line_lower for exp_header in ['experience', 'work history', 'employment', 'career', 'professional experience', 'work experience']):
                in_experience_section = True
                in_education_section = False
                print(f"💼 Entering work experience section: {line.strip()}")
                continue
            
            # Skip if we're in education section
            if in_education_section:
                continue
            
            # Only process if we're in experience section or if no clear section markers found
            if in_experience_section or not in_education_section:
                # Look for duration patterns
                for pattern in date_patterns:
                    match = re.search(pattern, line_lower)
                    if match:
                        start_date_str = match.group(1)
                        end_date_str = match.group(2)
                        
                        # Parse dates
                        start_date = parse_date(start_date_str)
                        end_date = parse_date(end_date_str)
                        
                        if start_date:
                            # Get context around this line
                            context_lines = []
                            for j in range(max(0, i-3), min(len(lines), i+4)):
                                if lines[j].strip():
                                    context_lines.append(lines[j].strip())
                            context_text = ' '.join(context_lines)
                            
                            # Additional check: exclude education-related content (but be more specific)
                            edu_indicators = ['bachelor', 'master degree', 'phd', 'graduation', 'gpa', 'thesis', 'dissertation', 'academic']
                            # Don't exclude just because of 'university' or 'college' as they could be company names
                            # Only exclude if it's clearly education context
                            if any(edu_indicator in context_text.lower() for edu_indicator in edu_indicators):
                                print(f"⏭️ Excluding education content: {line.strip()}")
                                continue
                            
                            # Check if this is a full-time position
                            if is_full_time_position(context_text):
                                entry = {
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'line': line.strip(),
                                    'context': context_text
                                }
                                experience_entries.append(entry)
                                print(f"✅ Including work experience: {line.strip()}")
                            else:
                                print(f"⏭️ Excluding non-full-time position: {line.strip()}")
                            break
        
        # Calculate total full-time experience
        if not experience_entries:
            return 0.0
        
        total_days = 0
        current_date = date.today()
        
        for entry in experience_entries:
            start_date = entry['start_date']
            end_date = entry['end_date'] or current_date
            
            # Calculate days between dates
            duration = (end_date - start_date).days
            
            # Ensure positive duration
            if duration > 0:
                total_days += duration
                print(f"📅 Full-time position: {start_date} to {end_date} ({duration} days)")
        
        # Convert to years (using 365.25 days per year for leap years)
        total_years = total_days / 365.25
        return round(total_years, 2)
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract summary/objective section"""
        # Look for summary indicators
        summary_indicators = ['summary', 'objective', 'profile', 'about']
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(indicator in line.lower() for indicator in summary_indicators):
                # Extract next few lines as summary
                summary_lines = []
                for j in range(i+1, min(len(lines), i+5)):
                    if lines[j].strip():
                        summary_lines.append(lines[j].strip())
                    else:
                        break
                if summary_lines:
                    return ' '.join(summary_lines)
        
        return None
    
    def get_skills_summary(self, parsed_data: Dict) -> str:
        """Generate a summary of skills for job matching"""
        skills = parsed_data.get('skills', {})
        all_skills = []
        
        for category, skill_list in skills.items():
            all_skills.extend(skill_list)
        
        if all_skills:
            return f"Skills: {', '.join(all_skills)}"
        else:
            return "No specific technical skills detected"
    
    def get_experience_summary(self, parsed_data: Dict) -> str:
        """Generate a summary of experience for job matching"""
        experience = parsed_data.get('experience', [])
        job_titles = parsed_data.get('job_titles', [])
        years = parsed_data.get('years_experience')
        
        summary_parts = []
        
        if job_titles:
            summary_parts.append(f"Roles: {', '.join(job_titles)}")
        
        if years:
            summary_parts.append(f"Experience: {years} years")
        
        if experience:
            companies = [exp.get('company') for exp in experience if exp.get('company')]
            if companies:
                summary_parts.append(f"Companies: {', '.join(companies[:3])}")
        
        return ' | '.join(summary_parts) if summary_parts else "Experience information not clearly detected"
    
    def print_parsed_resume(self, parsed_data: Dict):
        """Print parsed resume in a clear, readable format"""
        print("\n" + "="*60)
        print("📄 PARSED RESUME SUMMARY")
        print("="*60)
        
        # Basic Information
        print("\n👤 BASIC INFORMATION")
        print("-" * 30)
        name = parsed_data.get('name', 'Not found')
        email = parsed_data.get('email', 'Not found')
        phone = parsed_data.get('phone', 'Not found')
        location = parsed_data.get('location', 'Not found')
        
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Phone: {phone}")
        print(f"Location: {location}")
        
        # Experience Summary
        print("\n💼 EXPERIENCE SUMMARY")
        print("-" * 30)
        years_exp = parsed_data.get('years_experience', 0)
        print(f"Total Full-Time Experience: {years_exp} years")
        
        # Work Experience Details
        experience = parsed_data.get('experience', [])
        if experience:
            print(f"\n📋 WORK EXPERIENCE ({len(experience)} positions)")
            print("-" * 40)
            
            for i, exp in enumerate(experience, 1):
                title = exp.get('title', 'Unknown Title')
                company = exp.get('company', 'Unknown Company')
                dates = exp.get('dates', 'No dates')
                confidence = exp.get('confidence', 'unknown')
                
                print(f"\n{i}. {title}")
                print(f"   🏢 Company: {company}")
                print(f"   📅 Duration: {dates}")
                print(f"   🎯 Confidence: {confidence}")
        else:
            print("No work experience entries found")
        
        # Job Titles
        job_titles = parsed_data.get('job_titles', [])
        if job_titles:
            print(f"\n🎯 JOB TITLES ({len(job_titles)} found)")
            print("-" * 30)
            for i, title in enumerate(job_titles, 1):
                print(f"{i}. {title}")
        
        # Skills
        skills = parsed_data.get('skills', {})
        if skills:
            print(f"\n🛠️ SKILLS")
            print("-" * 20)
            total_skills = 0
            for category, skill_list in skills.items():
                if skill_list:
                    print(f"\n{category.upper().replace('_', ' ')} ({len(skill_list)} skills):")
                    print(f"  {', '.join(skill_list)}")
                    total_skills += len(skill_list)
            print(f"\nTotal Skills: {total_skills}")
        
        # Education
        education = parsed_data.get('education', [])
        if education:
            print(f"\n🎓 EDUCATION ({len(education)} entries)")
            print("-" * 30)
            for i, edu in enumerate(education, 1):
                line = edu.get('line', 'No details')
                print(f"{i}. {line}")
        
        # Summary/Objective
        summary = parsed_data.get('summary')
        if summary:
            print(f"\n📝 SUMMARY/OBJECTIVE")
            print("-" * 25)
            print(summary)
        
        # Experience Report (if available)
        experience_report = parsed_data.get('experience_report')
        if experience_report:
            print(f"\n📊 DETAILED EXPERIENCE ANALYSIS")
            print("-" * 35)
            print(f"Total Full-Time Years: {experience_report.get('total_full_time_years', 0)}")
            print(f"Total Full-Time Months: {experience_report.get('total_full_time_months', 0)}")
            print(f"Positions Count: {experience_report.get('positions_count', 0)}")
            
            positions = experience_report.get('positions', [])
            if positions:
                print(f"\n📋 POSITION DETAILS:")
                for i, pos in enumerate(positions, 1):
                    print(f"\n{i}. {pos.get('job_title', 'Unknown')}")
                    print(f"   Company: {pos.get('company', 'Unknown')}")
                    print(f"   Duration: {pos.get('start_date', 'Unknown')} - {pos.get('end_date', 'Unknown')}")
                    print(f"   Years: {pos.get('duration_years', 0)}")
        
        print("\n" + "="*60)
        print("✅ Resume parsing completed!")
        print("="*60) 