import requests
from bs4 import BeautifulSoup
import re
import random
import time
from llama_index.core.tools import ToolMetadata

class JobScraperQueryEngine:
    def __init__(self):
        self.metadata = ToolMetadata(
            name="JobScraperTool",
            description="Scrapes job listings from official company pages. Input is a comma-separated list like 'Amazon, Microsoft'."
        )

    def query(self, query: str) -> str:
        companies = [c.strip() for c in query.split(",")]
        result = ""
        for company in companies:
            job_links = self.search_jobs(company)
            print(job_links)
            job_data = self.extract_jobs(job_links[:2])  # Limit to top 2 links
            result += f"\n🧠 {company} Jobs:\n" + "\n".join(job_data) + "\n"
        return result or "No jobs found."

    def search_jobs(self, company):
        # Rotate user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        headers = {
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
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        # Try multiple search queries for better results
        search_queries = [
            f'"{company} careers"',
            f'"{company} jobs"',
            f'site:{company.lower().replace(" ", "")}.com "careers"',
            f'{company} career opportunities'
        ]
        
        links = []
        for query in search_queries:
            try:
                # Use DuckDuckGo instead of Google (less likely to block)
                import urllib.parse
                encoded_query = urllib.parse.quote(query)
                search_url = f"https://duckduckgo.com/html/?q={encoded_query}"
                print(f"Searching: {search_url}")
                
                # Add random delay to avoid detection
                time.sleep(random.uniform(1, 3))
                res = requests.get(search_url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")

                # Improved link extraction for DuckDuckGo
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    # DuckDuckGo redirects through /l/?uddg=
                    if '/l/?uddg=' in href:
                        # Extract the actual URL from DuckDuckGo redirect
                        try:
                            actual_url = urllib.parse.unquote(href.split('uddg=')[1])
                            if (company.lower() in actual_url.lower() and 
                                any(keyword in actual_url.lower() for keyword in ['career', 'job', 'employment', 'opportunity'])):
                                links.append(actual_url)
                        except:
                            continue
                    # Direct links
                    elif href.startswith('http'):
                        if (company.lower() in href.lower() and 
                            any(keyword in href.lower() for keyword in ['career', 'job', 'employment', 'opportunity'])):
                            links.append(href)
                
                if links:
                    break  # Found some links, no need to try other queries
                    
            except Exception as e:
                print(f"Search failed for query '{query}': {e}")
                continue
        
        return list(set(links))[:3]  # Remove duplicates and limit to 3

    def extract_jobs(self, urls):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        job_summaries = []

        for url in urls:
            try:
                # Add random delay between requests
                time.sleep(random.uniform(0.5, 2))
                res = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Look for job titles in various HTML elements
                job_selectors = [
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # Headers
                    'a[href*="job"]', 'a[href*="career"]',  # Job links
                    '.job-title', '.position-title', '.title',  # Common job title classes
                    '[class*="job"]', '[class*="position"]', '[class*="title"]'  # Partial class matches
                ]
                
                jobs_found = []
                for selector in job_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        # Filter for likely job titles
                        if (text and len(text) > 10 and len(text) < 100 and
                            any(keyword in text.lower() for keyword in ['engineer', 'developer', 'software', 'programmer', 'analyst', 'manager', 'specialist'])):
                            jobs_found.append(text)
                
                # Remove duplicates and limit
                unique_jobs = list(set(jobs_found))[:5]
                for job in unique_jobs:
                    job_summaries.append(f"🔹 {job} — from {url}")
                    
            except Exception as e:
                job_summaries.append(f"❌ Failed to scrape {url}: {str(e)[:50]}...")
        return job_summaries
