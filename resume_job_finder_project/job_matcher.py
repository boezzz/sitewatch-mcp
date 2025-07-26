import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import urllib.parse

class JobMatcher:
    """Match resume with relevant job postings and extract direct links"""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        
        # Job search engines and their APIs
        self.search_engines = {
            'indeed': 'https://www.indeed.com/jobs',
            'linkedin': 'https://www.linkedin.com/jobs/search',
            'glassdoor': 'https://www.glassdoor.com/Job',
            'ziprecruiter': 'https://www.ziprecruiter.com/candidate/search'
        }
        
        # Company career page patterns
        self.career_patterns = [
            r'careers?\.{company}\.com',
            r'{company}\.com/careers?',
            r'{company}\.com/jobs?',
            r'jobs?\.{company}\.com',
            r'{company}\.com/opportunities?'
        ]
    
    def setup_session(self):
        """Setup session with bot detection bypass headers"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def find_relevant_jobs(self, resume_data: Dict, max_jobs: int = 20) -> List[Dict]:
        """Find relevant jobs based on resume data"""
        print("🔍 Finding relevant jobs based on your resume...")
        
        # Extract key information from resume
        skills = self._extract_skills_for_search(resume_data)
        experience = resume_data.get('years_experience', 0)
        job_titles = resume_data.get('job_titles', [])
        location = resume_data.get('location', '')
        
        # Generate search queries
        search_queries = self._generate_search_queries(skills, job_titles, experience)
        
        all_jobs = []
        
        for query in search_queries:
            print(f"🔎 Searching for: {query}")
            
            # Search multiple sources
            jobs = self._search_job_sources(query, location)
            all_jobs.extend(jobs)
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(2, 4))
            
            if len(all_jobs) >= max_jobs:
                break
        
        # Remove duplicates and rank by relevance
        unique_jobs = self._remove_duplicates(all_jobs)
        ranked_jobs = self._rank_jobs_by_relevance(unique_jobs, resume_data)
        
        return ranked_jobs[:max_jobs]
    
    def _extract_skills_for_search(self, resume_data: Dict) -> List[str]:
        """Extract skills for job search"""
        skills = resume_data.get('skills', {})
        all_skills = []
        
        for category, skill_list in skills.items():
            all_skills.extend(skill_list)
        
        # Add common variations
        skill_variations = {
            'python': ['python', 'django', 'flask', 'fastapi'],
            'javascript': ['javascript', 'js', 'react', 'angular', 'vue', 'node.js'],
            'java': ['java', 'spring', 'android'],
            'aws': ['aws', 'amazon web services', 'cloud'],
            'docker': ['docker', 'containerization', 'kubernetes']
        }
        
        expanded_skills = []
        for skill in all_skills:
            expanded_skills.append(skill)
            if skill in skill_variations:
                expanded_skills.extend(skill_variations[skill])
        
        return list(set(expanded_skills))
    
    def _generate_search_queries(self, skills: List[str], job_titles: List[str], experience: int) -> List[str]:
        """Generate search queries based on resume data"""
        queries = []
        
        # Query 1: Primary skills + job title
        if skills and job_titles:
            primary_skills = skills[:3]  # Top 3 skills
            for title in job_titles[:2]:  # Top 2 job titles
                query = f'"{title}" {" ".join(primary_skills)}'
                queries.append(query)
        
        # Query 2: Skills only
        if skills:
            skill_query = ' '.join(skills[:5])  # Top 5 skills
            queries.append(skill_query)
        
        # Query 3: Experience level
        if experience:
            if experience < 2:
                level = "entry level"
            elif experience < 5:
                level = "mid level"
            else:
                level = "senior"
            
            if job_titles:
                for title in job_titles[:2]:
                    queries.append(f'"{title}" "{level}"')
        
        # Query 4: Technology stack
        if skills:
            tech_stack = ' '.join(skills[:3])
            queries.append(f'"{tech_stack}" developer')
        
        return queries[:5]  # Limit to 5 queries
    
    def _search_job_sources(self, query: str, location: str = '') -> List[Dict]:
        """Search multiple job sources"""
        jobs = []
        
        # Search Indeed
        indeed_jobs = self._search_indeed(query, location)
        jobs.extend(indeed_jobs)
        
        # Search LinkedIn
        linkedin_jobs = self._search_linkedin(query, location)
        jobs.extend(linkedin_jobs)
        
        # Search company career pages
        company_jobs = self._search_company_careers(query)
        jobs.extend(company_jobs)
        
        return jobs
    
    def _search_indeed(self, query: str, location: str = '') -> List[Dict]:
        """Search Indeed for jobs"""
        try:
            params = {
                'q': query,
                'l': location,
                'sort': 'date'
            }
            
            response = self.session.get(
                'https://www.indeed.com/jobs',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return self._parse_indeed_results(response.text)
            
        except Exception as e:
            print(f"❌ Indeed search failed: {e}")
        
        return []
    
    def _parse_indeed_results(self, html: str) -> List[Dict]:
        """Parse Indeed search results"""
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for job cards
        job_cards = soup.find_all('div', {'class': re.compile(r'job_seen_beacon|jobsearch-ResultsList')})
        
        for card in job_cards[:10]:  # Limit to 10 results
            try:
                # Extract job title
                title_elem = card.find('h2', {'class': re.compile(r'jobTitle|title')})
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                # Extract company
                company_elem = card.find('span', {'class': re.compile(r'companyName|company')})
                company = company_elem.get_text(strip=True) if company_elem else ''
                
                # Extract location
                location_elem = card.find('div', {'class': re.compile(r'location|companyLocation')})
                location = location_elem.get_text(strip=True) if location_elem else ''
                
                # Extract job link
                link_elem = card.find('a', href=True)
                if link_elem:
                    job_url = urljoin('https://www.indeed.com', link_elem['href'])
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'url': job_url,
                        'source': 'Indeed',
                        'description': ''
                    })
            
            except Exception as e:
                continue
        
        return jobs
    
    def _search_linkedin(self, query: str, location: str = '') -> List[Dict]:
        """Search LinkedIn for jobs"""
        try:
            params = {
                'keywords': query,
                'location': location,
                'f_TPR': 'r86400'  # Last 24 hours
            }
            
            response = self.session.get(
                'https://www.linkedin.com/jobs/search',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return self._parse_linkedin_results(response.text)
            
        except Exception as e:
            print(f"❌ LinkedIn search failed: {e}")
        
        return []
    
    def _parse_linkedin_results(self, html: str) -> List[Dict]:
        """Parse LinkedIn search results"""
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for job cards
        job_cards = soup.find_all('div', {'class': re.compile(r'job-search-card|job-card-container')})
        
        for card in job_cards[:10]:
            try:
                # Extract job title
                title_elem = card.find('h3', {'class': re.compile(r'job-search-card__title|title')})
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                # Extract company
                company_elem = card.find('h4', {'class': re.compile(r'job-search-card__subtitle|company')})
                company = company_elem.get_text(strip=True) if company_elem else ''
                
                # Extract location
                location_elem = card.find('span', {'class': re.compile(r'job-search-card__location|location')})
                location = location_elem.get_text(strip=True) if location_elem else ''
                
                # Extract job link
                link_elem = card.find('a', href=True)
                if link_elem:
                    job_url = urljoin('https://www.linkedin.com', link_elem['href'])
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'url': job_url,
                        'source': 'LinkedIn',
                        'description': ''
                    })
            
            except Exception as e:
                continue
        
        return jobs
    
    def _search_company_careers(self, query: str) -> List[Dict]:
        """Search company career pages directly"""
        jobs = []
        
        # Extract potential company names from query
        companies = self._extract_companies_from_query(query)
        
        for company in companies[:5]:  # Limit to 5 companies
            try:
                company_jobs = self._search_single_company(company, query)
                jobs.extend(company_jobs)
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                continue
        
        return jobs
    
    def _extract_companies_from_query(self, query: str) -> List[str]:
        """Extract potential company names from search query"""
        # Common tech companies
        tech_companies = [
            'google', 'microsoft', 'amazon', 'apple', 'meta', 'facebook', 'netflix',
            'salesforce', 'oracle', 'ibm', 'intel', 'adobe', 'cisco', 'vmware',
            'twitter', 'uber', 'lyft', 'airbnb', 'spotify', 'slack', 'zoom'
        ]
        
        companies = []
        query_lower = query.lower()
        
        for company in tech_companies:
            if company in query_lower:
                companies.append(company)
        
        return companies
    
    def _search_single_company(self, company: str, query: str) -> List[Dict]:
        """Search a single company's career page"""
        jobs = []
        
        # Try different career page URLs
        career_urls = [
            f'https://careers.{company}.com',
            f'https://jobs.{company}.com',
            f'https://{company}.com/careers',
            f'https://{company}.com/jobs',
            f'https://{company}.jobs'
        ]
        
        for url in career_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    company_jobs = self._parse_company_careers(response.text, company, url)
                    jobs.extend(company_jobs)
                    break
            except:
                continue
        
        return jobs
    
    def _parse_company_careers(self, html: str, company: str, base_url: str) -> List[Dict]:
        """Parse company career page"""
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for job listings
        job_selectors = [
            'a[href*="job"]',
            'a[href*="career"]',
            '.job-listing',
            '.career-item',
            '[class*="job"]',
            '[class*="position"]'
        ]
        
        for selector in job_selectors:
            elements = soup.select(selector)
            for elem in elements[:5]:  # Limit to 5 jobs per company
                try:
                    title = elem.get_text(strip=True)
                    if title and len(title) > 10:
                        # Get job URL
                        if elem.name == 'a' and elem.get('href'):
                            job_url = urljoin(base_url, elem['href'])
                        else:
                            job_url = base_url
                        
                        jobs.append({
                            'title': title,
                            'company': company.title(),
                            'location': '',
                            'url': job_url,
                            'source': f'{company.title()} Careers',
                            'description': ''
                        })
                except:
                    continue
        
        return jobs
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate job postings"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a unique identifier
            job_id = f"{job['title']}_{job['company']}"
            
            if job_id not in seen:
                seen.add(job_id)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _rank_jobs_by_relevance(self, jobs: List[Dict], resume_data: Dict) -> List[Dict]:
        """Rank jobs by relevance to resume - only recommend jobs with 18/20+ relevant skills"""
        skills = self._extract_skills_for_search(resume_data)
        job_titles = resume_data.get('job_titles', [])
        
        # Calculate total skills for percentage calculation
        total_skills = len(skills)
        if total_skills == 0:
            total_skills = 1  # Avoid division by zero
        
        for job in jobs:
            score = 0
            matched_skills = []
            
            # Get job description for skill matching
            job_description = job.get('description', '').lower()
            job_title_lower = job['title'].lower()
            
            # Score based on title match
            for title in job_titles:
                if title.lower() in job_title_lower:
                    score += 10
            
            # Score based on skills match in job description
            for skill in skills:
                skill_lower = skill.lower()
                # Check in job title and description
                if (skill_lower in job_title_lower or 
                    skill_lower in job_description or
                    skill_lower.replace(' ', '') in job_description):
                    score += 5
                    matched_skills.append(skill)
            
            # Calculate skills match percentage
            skills_match_percentage = (len(matched_skills) / total_skills) * 100
            
            # Only include jobs with 18/20+ relevant skills (90%+ match)
            if skills_match_percentage >= 90:
                # Additional score for high skills match
                score += skills_match_percentage
                
                # Score based on company reputation (simple heuristic)
                if job['company'].lower() in ['google', 'microsoft', 'amazon', 'apple', 'meta', 'netflix', 'uber', 'airbnb']:
                    score += 3
                
                job['relevance_score'] = score
                job['skills_match_percentage'] = skills_match_percentage
                job['matched_skills'] = matched_skills
                job['total_skills_required'] = total_skills
                job['meets_skill_threshold'] = True
            else:
                # Mark jobs that don't meet the threshold
                job['relevance_score'] = 0
                job['skills_match_percentage'] = skills_match_percentage
                job['matched_skills'] = matched_skills
                job['total_skills_required'] = total_skills
                job['meets_skill_threshold'] = False
        
        # Filter to only include jobs that meet the skill threshold and sort by relevance score
        qualified_jobs = [job for job in jobs if job.get('meets_skill_threshold', False)]
        return sorted(qualified_jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def get_direct_job_links(self, jobs: List[Dict]) -> List[Dict]:
        """Get direct job posting links from company websites"""
        print("🔗 Extracting direct job posting links...")
        
        for job in jobs:
            try:
                # Try to get the actual job posting page
                if 'indeed.com' in job['url'] or 'linkedin.com' in job['url']:
                    direct_link = self._extract_direct_link(job['url'])
                    if direct_link:
                        job['direct_url'] = direct_link
                        job['is_direct'] = True
                    else:
                        job['is_direct'] = False
                else:
                    job['is_direct'] = True
                    job['direct_url'] = job['url']
                
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                job['is_direct'] = False
                job['direct_url'] = job['url']
        
        return jobs
    
    def _extract_direct_link(self, job_url: str) -> Optional[str]:
        """Extract direct company link from job board URL"""
        try:
            response = self.session.get(job_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for "Apply on company website" or similar links
                apply_selectors = [
                    'a[href*="apply"]',
                    'a[href*="company"]',
                    'a[href*="external"]',
                    '.apply-button',
                    '.company-link'
                ]
                
                for selector in apply_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        href = elem.get('href')
                        if href and not any(domain in href for domain in ['indeed.com', 'linkedin.com']):
                            return urljoin(job_url, href)
            
        except Exception as e:
            pass
        
        return None 