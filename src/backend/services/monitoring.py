"""
Monitoring service adapted from demo.py
"""

import os
import json
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from tavily import TavilyClient
import openai
from dataclasses import dataclass

from database import get_db
from models import ChatMessage, MonitoringJob, MonitoringResult

# Configuration
TAVILY_API_KEY = "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"  # disposable key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class MonitoringService:
    def __init__(self):
        """Initialize the monitoring service"""
        self.tavily_client = TavilyClient(TAVILY_API_KEY)
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    
    async def process_user_query(self, user_query: str, connection_manager) -> Optional[MonitoringJob]:
        """Process user query and potentially create a monitoring job"""
        try:
            # Send analysis message
            await connection_manager.broadcast({
                "type": "chat_message",
                "message": {
                    "content": f"Analyzing your request: '{user_query}'",
                    "sender": "system",
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Analyze user query
            analysis = await self.analyze_user_query(user_query)
            
            # Generate URLs
            await connection_manager.broadcast({
                "type": "chat_message", 
                "message": {
                    "content": "Generating specific URLs for monitoring...",
                    "sender": "system",
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            urls = await self.get_search_urls_from_gpt(user_query)
            
            if not urls:
                await connection_manager.broadcast({
                    "type": "chat_message",
                    "message": {
                        "content": "Sorry, I couldn't generate specific URLs for your query. Please try a more specific request.",
                        "sender": "system", 
                        "timestamp": datetime.now().isoformat()
                    }
                })
                return None
            
            # Create monitoring job
            monitoring_focus = analysis.get('monitoring_focus', 'general updates')
            job_name = f"Monitor: {user_query[:50]}..."
            
            async with get_db() as db:
                job = MonitoringJob(
                    name=job_name,
                    query=user_query,
                    urls=urls,
                    monitoring_focus=monitoring_focus,
                    next_run=datetime.now()
                )
                db.add(job)
                await db.commit()
                await db.refresh(job)
                
                # Save system message
                system_message = ChatMessage(
                    content=f"Created monitoring job '{job_name}' for {len(urls)} URLs. Running initial check...",
                    sender="system",
                    timestamp=datetime.now(),
                    job_id=job.id
                )
                db.add(system_message)
                await db.commit()
            
            # Send job creation message
            await connection_manager.broadcast({
                "type": "chat_message",
                "message": {
                    "content": f"Created monitoring job '{job_name}' for {len(urls)} URLs. Running initial check...",
                    "sender": "system",
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            await connection_manager.broadcast({
                "type": "job_created",
                "job": {
                    "id": job.id,
                    "name": job.name,
                    "query": job.query,
                    "urls": job.urls,
                    "monitoring_focus": job.monitoring_focus,
                    "is_active": job.is_active,
                    "created_at": job.created_at.isoformat()
                }
            })
            
            # Run initial monitoring
            await self.run_monitoring_for_job(job.id, connection_manager)
            
            return job
            
        except Exception as e:
            await connection_manager.broadcast({
                "type": "chat_message",
                "message": {
                    "content": f"Error processing your request: {str(e)}",
                    "sender": "system",
                    "timestamp": datetime.now().isoformat()
                }
            })
            return None
    
    async def analyze_user_query(self, user_query: str) -> Dict[str, Any]:
        """Analyze user query to understand intent"""
        if not self.openai_client:
            return {"monitoring_focus": "general updates", "analysis": "Basic analysis"}
        
        try:
            analysis_prompt = f"""Analyze this monitoring request: "{user_query}"

Return a JSON object with:
- "monitoring_focus": string (what to monitor like "job postings", "product releases", "news", etc.)
- "domain": string (industry/area like "tech", "finance", "healthcare", etc.)
- "analysis": string (brief analysis)

Example: {{"monitoring_focus": "job postings", "domain": "tech", "analysis": "User wants to monitor tech job opportunities"}}"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                return json.loads(analysis_text)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*?\}', analysis_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"monitoring_focus": "general updates", "analysis": "Could not parse analysis"}
                    
        except Exception as e:
            print(f"Error analyzing query: {e}")
            return {"monitoring_focus": "general updates", "analysis": "Analysis failed"}

    async def get_search_urls_from_gpt(self, user_query: str) -> List[str]:
        """Use GPT to generate specific URLs based on user query"""
        if not self.openai_client:
            print("WARNING: OpenAI API key not set. Using default URLs.")
            return ["https://example.com"]
        
        try:
            prompt = f"""Generate highly specific URLs for monitoring changes related to: "{user_query}"

Requirements for URL selection:
1. AVOID generic sites like example.com, google.com, wikipedia.org, linkedin.com, ycombinator.com, etc.
2. Find SPECIFIC pages that would show relevant changes
3. Focus on pages likely to update frequently with relevant information
4. Include official sources, company pages, government sites, or authoritative news sources

Return ONLY a JSON array of 3-5 specific URLs.
Format: ["https://specific-site.com/relevant-page", "https://another-specific.com/targeted-section"]"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            urls_text = response.choices[0].message.content.strip()
            
            # Parse URLs
            urls = self._extract_urls_from_response(urls_text)
            filtered_urls = self._filter_generic_urls(urls)
            
            if not filtered_urls:
                return self._get_fallback_urls(user_query)
            
            return filtered_urls
            
        except Exception as e:
            print(f"Error getting URLs from GPT: {e}")
            return self._get_fallback_urls(user_query)

    def _extract_urls_from_response(self, response_text: str) -> List[str]:
        """Extract URLs from GPT response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # Extract URLs using regex
            url_pattern = r'https?://[^\s\'"<>]+[^\s\'"<>.,)]'
            found_urls = re.findall(url_pattern, response_text)
            return found_urls[:5] if found_urls else []

    def _filter_generic_urls(self, urls: List[str]) -> List[str]:
        """Filter out generic/placeholder URLs"""
        generic_domains = [
            'example.com', 'google.com', 'wikipedia.org', 'github.com', 
            'stackoverflow.com', 'reddit.com', 'twitter.com', 'facebook.com',
            'youtube.com', 'amazon.com', 'ebay.com'
        ]
        
        filtered = []
        for url in urls:
            is_generic = any(domain in url.lower() for domain in generic_domains)
            if not is_generic and url.startswith(('http://', 'https://')):
                filtered.append(url)
        
        return filtered

    def _get_fallback_urls(self, user_query: str) -> List[str]:
        """Generate fallback URLs"""
        return [
            'https://techcrunch.com/startups/',
            'https://news.ycombinator.com/',
            'https://www.producthunt.com/'
        ]
    
    def extract_content_from_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Extract content from URLs using Tavily"""
        try:
            response = self.tavily_client.extract(urls=urls)
            return response
        except Exception as e:
            print(f"Error extracting content: {e}")
            return {}
    
    async def generate_summary_with_gpt(self, content: Dict[str, Any], user_query: str = "", monitoring_focus: str = "") -> str:
        """Generate summary using GPT"""
        if not self.openai_client:
            return "Summary generation requires OpenAI API key"
        
        try:
            content_text = json.dumps(content, indent=2)[:4000]
            
            prompt = f"""Analyze the following web content for monitoring purposes:

User's request: "{user_query}"
Focus: {monitoring_focus}

Content:
{content_text}

Provide a focused summary that addresses:
1. Key findings relevant to the user's request
2. Notable changes or updates
3. Actionable insights

Keep the summary under 300 words and actionable."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Summary generation failed: {str(e)}"
    
    def calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """Calculate hash of content for change detection"""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    async def run_monitoring_for_job(self, job_id: int, connection_manager=None) -> Optional[MonitoringResult]:
        """Run monitoring for a specific job"""
        try:
            async with get_db() as db:
                # Get job
                job = await db.get(MonitoringJob, job_id)
                if not job or not job.is_active:
                    return None
                
                # Extract content
                content = self.extract_content_from_urls(job.urls)
                
                # Generate summary
                summary = await self.generate_summary_with_gpt(
                    content, job.query, job.monitoring_focus
                )
                
                # Calculate hash and detect changes
                content_hash = self.calculate_content_hash(content)
                
                # Get previous result for comparison
                from sqlalchemy import select, desc
                stmt = select(MonitoringResult).where(
                    MonitoringResult.job_id == job_id
                ).order_by(desc(MonitoringResult.timestamp)).limit(1)
                result = await db.execute(stmt)
                previous_result = result.scalar_one_or_none()
                
                has_changes = previous_result is None or previous_result.content_hash != content_hash
                
                # Create new result
                new_result = MonitoringResult(
                    job_id=job_id,
                    content=content,
                    summary=summary,
                    content_hash=content_hash,
                    has_changes=has_changes
                )
                
                # Generate change analysis if there are changes
                if has_changes and previous_result and self.openai_client:
                    change_analysis = await self.generate_change_analysis(
                        new_result, previous_result, job.query, job.monitoring_focus
                    )
                    new_result.change_analysis = change_analysis
                
                db.add(new_result)
                
                # Update job last run
                job.last_run = datetime.now()
                await db.commit()
                await db.refresh(new_result)
                
                # Broadcast results if connection manager provided
                if connection_manager:
                    message = f"Monitoring update for '{job.name}': "
                    if has_changes:
                        message += "Changes detected! " + summary[:100] + "..."
                    else:
                        message += "No changes detected."
                    
                    await connection_manager.broadcast({
                        "type": "chat_message",
                        "message": {
                            "content": message,
                            "sender": "system",
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                    
                    await connection_manager.broadcast({
                        "type": "monitoring_update",
                        "result": {
                            "job_id": job_id,
                            "job_name": job.name,
                            "has_changes": has_changes,
                            "summary": summary,
                            "timestamp": new_result.timestamp.isoformat()
                        }
                    })
                
                return new_result
                
        except Exception as e:
            print(f"Error running monitoring for job {job_id}: {e}")
            return None
    
    async def generate_change_analysis(self, current: MonitoringResult, previous: MonitoringResult, 
                                     user_query: str, monitoring_focus: str) -> str:
        """Generate change analysis using GPT"""
        try:
            prompt = f"""Compare these monitoring results and identify changes:

User's request: "{user_query}"
Focus: {monitoring_focus}

PREVIOUS:
{json.dumps(previous.content, indent=2)[:2000]}

CURRENT:
{json.dumps(current.content, indent=2)[:2000]}

Provide a focused change analysis:
1. What changed that impacts the user's monitoring goals?
2. How significant are these changes?
3. What should the user do based on these changes?

Keep analysis under 200 words."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Change analysis failed: {str(e)}" 