#!/usr/bin/env python3
"""
SiteWatch Demo - A web content monitoring system
Monitors websites for changes and provides summaries using AI
"""

import os
import json
import time
import schedule
import difflib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tavily import TavilyClient
import openai
from dataclasses import dataclass
import hashlib

# Configuration
TAVILY_API_KEY = "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" # disposable key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set this environment variable
DATA_DIR = "sitewatch_data"
RESULTS_FILE = os.path.join(DATA_DIR, "monitoring_results.json")

@dataclass
class MonitoringResult:
    """Data class for storing monitoring results"""
    timestamp: str
    urls: List[str]
    content: Dict[str, Any]
    summary: str
    content_hash: str
    user_query: str = ""
    monitoring_focus: str = ""

class SiteWatchDemo:
    def __init__(self):
        """Initialize the SiteWatch demo application"""
        self.tavily_client = TavilyClient(TAVILY_API_KEY)
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.setup_data_directory()
        
    def setup_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
    
    def analyze_user_query(self, user_query: str) -> Dict[str, Any]:
        """Analyze user query to understand intent and identify if clarification is needed"""
        if not self.openai_client:
            return {"needs_clarification": False, "analysis": "Basic query analysis"}
        
        try:
            analysis_prompt = f"""Analyze this monitoring request: "{user_query}"

Determine:
1. Is this query specific enough to generate targeted URLs? 
2. What domain/industry is this about?
3. What type of changes would be most valuable to monitor?
4. Are there any ambiguities that need clarification?

Return a JSON object with:
- "is_specific": boolean (true if query is specific enough)
- "domain": string (industry/area like "tech", "finance", "healthcare", etc.)
- "monitoring_focus": string (what to monitor like "job postings", "product releases", "news", etc.)
- "clarification_needed": boolean
- "follow_up_question": string (if clarification needed)
- "analysis": string (brief analysis)

Example: {{"is_specific": true, "domain": "tech", "monitoring_focus": "job postings", "clarification_needed": false, "follow_up_question": "", "analysis": "Clear request to monitor tech job postings"}}"""

            response = self.openai_client.responses.create(
                model="gpt-4.1-mini",
                tools=[{"type": "web_search_preview"}],
                input=analysis_prompt
            )
            
            analysis_text = response.output_text.strip()
            
            # Try to parse JSON
            try:
                return json.loads(analysis_text)
            except json.JSONDecodeError:
                # Extract JSON if wrapped in other text
                json_match = re.search(r'\{.*?\}', analysis_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"is_specific": True, "analysis": "Could not parse analysis"}
                    
        except Exception as e:
            print(f"ERROR: Error analyzing query: {e}")
            return {"is_specific": True, "analysis": "Analysis failed"}

    def _run_clarification_loop(self, initial_query: str) -> str:
        """Intelligent clarification loop where AI decides when enough info is gathered"""
        current_query = initial_query
        conversation_history = [f"Initial request: {initial_query}"]
        max_iterations = 2  # Keep it concise - max 2 clarifying questions
        
        print(f"\n🤖 Quick query analysis (max 1-2 questions if needed)...")
        print(f"Initial query: '{initial_query}'")
        
        for iteration in range(max_iterations):
            print(f"\n--- Clarification Round {iteration + 1} ---")
            
            # AI evaluates if more information is needed
            evaluation = self._evaluate_information_sufficiency(current_query, conversation_history)
            
            if not evaluation.get('needs_more_info', True):
                print(f"✅ Sufficient info gathered! Confidence: {evaluation.get('confidence_level', 'medium')}")
                break
            
            # AI asks a specific follow-up question
            question = evaluation.get('next_question', 'Can you provide more details?')
            reasoning = evaluation.get('reasoning', 'Need more context')
            
            print(f"🤔 Need clarification: {reasoning}")
            print(f"❓ Quick question: {question}")
            
            # Get user response
            user_response = input("\n👤 Your response: ").strip()
            
            if not user_response:
                print("⏭️ No response provided, proceeding with current information...")
                break
            
            # Update conversation history and current query
            conversation_history.append(f"Question {iteration + 1}: {question}")
            conversation_history.append(f"User response: {user_response}")
            current_query = f"{current_query} | Additional context from clarification: {user_response}"
            
            print(f"✨ Updated...")
        
        print(f"\n🎯 Ready for URL generation")
        return current_query

    def _evaluate_information_sufficiency(self, current_query: str, conversation_history: List[str]) -> Dict[str, Any]:
        """AI evaluates if enough information has been gathered for informed URL generation"""
        if not self.openai_client:
            return {"needs_more_info": False, "confidence_level": "low"}
        
        try:
            history_text = "\n".join(conversation_history)
            
            evaluation_prompt = f"""You are an AI agent that needs to quickly determine if you have enough info to generate useful monitoring URLs.

Current query: "{current_query}"

Conversation history:
{history_text}

IMPORTANT: Be pragmatic and efficient. Don't over-analyze.

MINIMAL requirements to proceed:
1. Basic domain/topic is identifiable (even if broad like "tech" or "business")
2. General focus area exists (jobs, news, products, etc.)

ONLY ask for clarification if the query is genuinely vague like:
- "monitor stuff" 
- "watch things"
- "track changes" (with no context)

If you can identify ANY reasonable domain + focus, proceed immediately.

Examples that should PROCEED without questions:
- "monitor AI companies" ✅ (domain: tech/AI, focus: general updates)
- "track startup funding" ✅ (domain: startups, focus: funding news)
- "watch FDA approvals" ✅ (domain: healthcare, focus: regulatory)
- "monitor job openings" ✅ (domain: general, focus: jobs)

Return JSON:
- "needs_more_info": boolean (default to FALSE unless truly hopeless)
- "confidence_level": string ("medium" is fine to proceed)
- "reasoning": string (brief explanation)
- "next_question": string (only if absolutely necessary)

Be efficient - ask at most 1 focused question to resolve major ambiguity.

Example: {{"needs_more_info": false, "confidence_level": "medium", "reasoning": "Sufficient domain and focus identified", "next_question": ""}}"""

            response = self.openai_client.responses.create(
                model="gpt-4.1-mini",
                tools=[{"type": "web_search_preview"}],
                input=evaluation_prompt
            )
            
            evaluation_text = response.output_text.strip()
            
            # Parse the evaluation response
            try:
                return json.loads(evaluation_text)
            except json.JSONDecodeError:
                # Extract JSON if wrapped in other text
                json_match = re.search(r'\{.*?\}', evaluation_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {
                        "needs_more_info": False, 
                        "confidence_level": "low",
                        "reasoning": "Could not parse evaluation response"
                    }
                    
        except Exception as e:
            print(f"ERROR: Error evaluating information sufficiency: {e}")
            return {"needs_more_info": False, "confidence_level": "low", "reasoning": "Evaluation failed"}

    def get_search_urls_from_gpt(self, user_query: str) -> List[str]:
        """Use GPT-4.1 to generate highly specific URLs based on user query"""
        if not self.openai_client:
            print("WARNING: OpenAI API key not set. Using default URLs.")
            return ["https://example.com"]
        
        # Intelligent clarification loop
        enriched_query = self._run_clarification_loop(user_query)
        
        # Final analysis with enriched query
        analysis = self.analyze_user_query(enriched_query)
        print(f"\nFinal Analysis: {analysis.get('analysis', 'No analysis')}")
        
        try:
            # Enhanced prompt for specific URL generation
            domain = analysis.get('domain', 'general')
            monitoring_focus = analysis.get('monitoring_focus', 'updates')
            
            prompt = f"""Generate highly specific URLs for monitoring changes related to: "{enriched_query}"

Context from analysis:
- Domain: {domain}
- Focus: {monitoring_focus}

Requirements for URL selection:
1. AVOID generic sites like example.com, google.com, wikipedia.org, linkedin.com, ycombinator.com, etc.
2. Find SPECIFIC pages that would show relevant changes (for example, a company's careers page)
3. Focus on pages likely to update frequently with relevant information
4. Include official sources, company pages, government sites, or authoritative news sources
5. Consider: job boards, product pages, news sections, regulatory filings, press release pages

For each URL type, think strategically:
- Job monitoring: specific company career pages, not general job sites
- Product releases: company product/blog pages, not news aggregators  
- Market analysis: specific industry reports, regulatory pages, company investor pages
- News monitoring: specific beat reporters, official agency pages, industry publications

Use web search to find the most current and relevant specific URLs.

Return ONLY a JSON array of 3-5 specific URLs that are most likely to contain relevant changes.
Each URL should be targeted and specific, not generic.

Format: ["https://specific-site.com/relevant-page", "https://another-specific.com/targeted-section"]"""
            
            response = self.openai_client.responses.create(
                model="gpt-4.1-mini",
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            
            urls_text = response.output_text.strip()
            print(f"DEBUG: Raw URL response: '{urls_text[:200]}...'")
            
            # Parse URLs with robust error handling
            urls = self._extract_urls_from_response(urls_text)
            
            # Validate URLs are not generic
            filtered_urls = self._filter_generic_urls(urls)
            
            if not filtered_urls:
                print("WARNING: No specific URLs found, trying alternative approach...")
                return self._get_fallback_specific_urls(enriched_query, domain, monitoring_focus)
            
            print(f"Generated {len(filtered_urls)} specific URLs for monitoring")
            return filtered_urls
            
        except Exception as e:
            print(f"ERROR: Error getting URLs from GPT: {e}")
            return self._get_fallback_specific_urls(enriched_query, analysis.get('domain', 'general'), analysis.get('monitoring_focus', 'updates'))

    def _extract_urls_from_response(self, response_text: str) -> List[str]:
        """Extract URLs from GPT response with multiple fallback methods"""
        try:
            # Try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON array
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

    def _get_fallback_specific_urls(self, user_query: str, domain: str, monitoring_focus: str) -> List[str]:
        """Generate fallback URLs based on domain and focus"""
        fallback_urls = {
            'tech': [
                'https://techcrunch.com/startups/',
                'https://news.ycombinator.com/',
                'https://www.producthunt.com/'
            ],
            'finance': [
                'https://www.sec.gov/edgar/searchedgar/companysearch.html',
                'https://finance.yahoo.com/news/',
                'https://www.bloomberg.com/markets'
            ],
            'healthcare': [
                'https://www.fda.gov/news-events/press-announcements',
                'https://www.nih.gov/news-events',
                'https://www.cdc.gov/media/releases/'
            ],
            'government': [
                'https://www.whitehouse.gov/news/',
                'https://www.congress.gov/',
                'https://www.regulations.gov/'
            ]
        }
        
        specific_urls = fallback_urls.get(domain, [
            'https://reuters.com/',
            'https://apnews.com/',
            'https://www.bbc.com/news'
        ])
        
        print(f"Using fallback URLs for domain: {domain}")
        return specific_urls[:3]
    
    def extract_content_from_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Extract content from URLs using Tavily"""
        try:
            print(f"Extracting content from {len(urls)} URLs...")
            response = self.tavily_client.extract(urls=urls)
            return response
        except Exception as e:
            print(f"ERROR: Error extracting content: {e}")
            return {}
    
    def generate_summary_with_gpt(self, content: Dict[str, Any], user_query: str = "", monitoring_focus: str = "") -> str:
        """Generate a user-focused summary of the extracted content using GPT-4.1"""
        if not self.openai_client:
            return "Summary generation requires OpenAI API key"
        
        try:
            # Prepare content for summarization
            content_text = json.dumps(content, indent=2)[:4000]  # Limit content length
            
            # Create focused prompt based on user intent
            focus_instruction = ""
            if user_query:
                focus_instruction = f"""
USER'S ORIGINAL REQUEST: "{user_query}"
MONITORING FOCUS: {monitoring_focus}

IMPORTANT: Tailor your summary to address what the user specifically wants to monitor. Focus on information most relevant to their request."""

            prompt = f"""{focus_instruction}

Analyze the following web content and provide a focused summary:

{content_text}

Provide a summary that specifically addresses the user's monitoring intentions:

1. **Key Findings Relevant to User's Request**: What was found that directly relates to their query?
2. **Actionable Insights**: What specific changes or updates should they pay attention to?
3. **Monitoring Recommendations**: Based on the content, what should they watch for in future checks?
4. **Notable Patterns**: Any trends or patterns relevant to their interests?

If the user was looking for:
- Job opportunities: Focus on open positions, requirements, application processes
- Product releases: Highlight new features, launch dates, pricing changes  
- Company updates: Emphasize news, announcements, strategic changes
- Regulatory changes: Focus on policy updates, compliance requirements, deadlines
- Market trends: Highlight industry shifts, competitive landscape, opportunities

Keep the summary under 400 words and make it actionable for monitoring purposes."""
            
            response = self.openai_client.responses.create(
                model="gpt-4.1-mini",
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            
            return response.output_text.strip()
            
        except Exception as e:
            print(f"ERROR: Error generating summary: {e}")
            return f"Summary generation failed: {str(e)}"
    
    def calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """Calculate hash of content for change detection"""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def load_previous_results(self) -> List[MonitoringResult]:
        """Load previous monitoring results"""
        if not os.path.exists(RESULTS_FILE):
            return []
        
        try:
            with open(RESULTS_FILE, 'r') as f:
                data = json.load(f)
                results = []
                for item in data:
                    # Handle backward compatibility with old data
                    if 'user_query' not in item:
                        item['user_query'] = ''
                    if 'monitoring_focus' not in item:
                        item['monitoring_focus'] = ''
                    results.append(MonitoringResult(**item))
                return results
        except Exception as e:
            print(f"ERROR: Error loading previous results: {e}")
            return []
    
    def save_results(self, results: List[MonitoringResult]):
        """Save monitoring results to file"""
        try:
            data = [
                {
                    "timestamp": result.timestamp,
                    "urls": result.urls,
                    "content": result.content,
                    "summary": result.summary,
                    "content_hash": result.content_hash,
                    "user_query": getattr(result, 'user_query', ''),
                    "monitoring_focus": getattr(result, 'monitoring_focus', '')
                }
                for result in results
            ]
            
            with open(RESULTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"ERROR: Error saving results: {e}")
    
    def detect_changes(self, current_result: MonitoringResult, 
                      previous_results: List[MonitoringResult]) -> Dict[str, Any]:
        """Detect changes between current and previous results"""
        if not previous_results:
            return {"is_first_run": True, "changes": []}
        
        latest_previous = previous_results[-1]
        changes = []
        
        # Check if content hash changed
        if current_result.content_hash != latest_previous.content_hash:
            changes.append({
                "type": "content_change",
                "description": "Website content has changed",
                "previous_hash": latest_previous.content_hash,
                "current_hash": current_result.content_hash
            })
            
            # Generate detailed diff if OpenAI is available
            if self.openai_client:
                diff = self.generate_change_analysis(current_result, latest_previous, 
                                                   current_result.user_query, current_result.monitoring_focus)
                changes.append({
                    "type": "detailed_analysis",
                    "description": diff
                })
        
        return {
            "is_first_run": False,
            "has_changes": len(changes) > 0,
            "changes": changes,
            "previous_check": latest_previous.timestamp
        }
    
    def generate_change_analysis(self, current: MonitoringResult, 
                               previous: MonitoringResult, user_query: str = "", monitoring_focus: str = "") -> str:
        """Generate user-focused change analysis using GPT-4.1-mini"""
        try:
            # Add user context if available
            user_context = ""
            if user_query:
                user_context = f"""
USER'S MONITORING INTENT: "{user_query}"
FOCUS AREA: {monitoring_focus}

IMPORTANT: Focus your analysis on changes that matter to the user's specific monitoring goals."""

            prompt = f"""{user_context}

Compare these website monitoring results and identify changes relevant to the user's interests:

PREVIOUS (from {previous.timestamp}):
{json.dumps(previous.content, indent=2)[:2000]}

CURRENT (from {current.timestamp}):
{json.dumps(current.content, indent=2)[:2000]}

Provide a focused change analysis:

1. **Changes Relevant to User's Intent**: What changed that impacts their monitoring goals?
2. **Impact Assessment**: How significant are these changes for the user?
3. **Action Items**: What should the user do or watch for based on these changes?

Focus on changes that matter for:
- Job monitoring: New positions, requirements changes, application deadlines
- Product monitoring: Feature updates, pricing changes, availability
- News monitoring: Breaking developments, policy changes, announcements
- Market monitoring: Trends, competitive moves, opportunities

Keep analysis under 250 words and actionable."""
            
            response = self.openai_client.responses.create(
                model="gpt-4.1-mini",
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            
            return response.output_text.strip()
            
        except Exception as e:
            return f"Change analysis failed: {str(e)}"
    
    def run_monitoring_cycle(self, urls: List[str] = None, user_query: str = ""):
        """Run a complete monitoring cycle"""
        print(f"\nStarting monitoring cycle at {datetime.now()}")
        
        # Get URLs to monitor and analyze user intent
        monitoring_focus = ""
        if not urls:
            if user_query:
                # Analyze user query to understand monitoring focus
                analysis = self.analyze_user_query(user_query)
                monitoring_focus = analysis.get('monitoring_focus', 'general updates')
                urls = self.get_search_urls_from_gpt(user_query)
            else:
                urls = ["https://vercept.com/careers"]  # Default
                monitoring_focus = "job opportunities"
        
        print(f"Monitoring URLs: {urls}")
        print(f"Focus: {monitoring_focus}")
        
        # Extract content
        content = self.extract_content_from_urls(urls)
        
        # Generate user-focused summary
        summary = self.generate_summary_with_gpt(content, user_query, monitoring_focus)
        
        # Create result
        current_result = MonitoringResult(
            timestamp=datetime.now().isoformat(),
            urls=urls,
            content=content,
            summary=summary,
            content_hash=self.calculate_content_hash(content),
            user_query=user_query,
            monitoring_focus=monitoring_focus
        )
        
        # Load previous results and detect changes
        previous_results = self.load_previous_results()
        change_info = self.detect_changes(current_result, previous_results)
        
        # Save results
        all_results = previous_results + [current_result]
        # Keep only last 30 days of results
        cutoff_date = datetime.now() - timedelta(days=30)
        all_results = [
            r for r in all_results 
            if datetime.fromisoformat(r.timestamp) > cutoff_date
        ]
        self.save_results(all_results)
        
        # Report results
        self.report_results(current_result, change_info)
        
        return current_result, change_info
    
    def report_results(self, result: MonitoringResult, change_info: Dict[str, Any]):
        """Report monitoring results to user"""
        print("\n" + "="*60)
        print("MONITORING REPORT")
        print("="*60)
        print(f"Timestamp: {result.timestamp}")
        print(f"URLs monitored: {len(result.urls)}")
        
        if change_info["is_first_run"]:
            print("This is the first monitoring run")
        elif change_info["has_changes"]:
            print("CHANGES DETECTED!")
            for change in change_info["changes"]:
                print(f"   - {change['description']}")
        else:
            print("No changes detected")
            print(f"   Last check: {change_info['previous_check']}")
        
        print(f"\nSummary:\n{result.summary}")
        print("="*60)
    
    def start_scheduler(self, urls: List[str], user_query: str = ""):
        """Start the daily monitoring scheduler"""
        print("\nSetting up daily monitoring schedule...")
        
        # Schedule daily monitoring at 9 AM
        schedule.every().day.at("09:00").do(
            self.run_monitoring_cycle, urls=urls, user_query=user_query
        )
        
        print("Daily monitoring scheduled for 9:00 AM")
        print("Running initial monitoring cycle...")
        
        # Run initial cycle
        self.run_monitoring_cycle(urls, user_query)
        
        print("\nMonitoring started. Press Ctrl+C to stop...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

def main():
    """Main function to run the demo"""
    print("Welcome to SiteWatch Demo!")
    print("This tool monitors websites for changes and provides AI-powered summaries.")
    
    if not OPENAI_API_KEY:
        print("\nWarning: OPENAI_API_KEY environment variable not set.")
        print("   Some features (GPT summaries, change analysis) will be limited.")
        print("   To enable full functionality, set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
    
    demo = SiteWatchDemo()
    
    while True:
        print("\n" + "="*50)
        print("Choose an option:")
        print("1. Single monitoring run (with custom query)")
        print("2. Start daily monitoring schedule")
        print("3. View previous results")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            user_query = input("\nEnter your search query (or press Enter for default): ").strip()
            demo.run_monitoring_cycle(user_query=user_query)
            
        elif choice == "2":
            user_query = input("\nEnter search query for daily monitoring: ").strip()
            urls = demo.get_search_urls_from_gpt(user_query) if user_query else None
            demo.start_scheduler(urls or [], user_query)
            
        elif choice == "3":
            results = demo.load_previous_results()
            if results:
                print(f"\nFound {len(results)} previous results:")
                for i, result in enumerate(results[-5:], 1):  # Show last 5
                    print(f"{i}. {result.timestamp} - {len(result.urls)} URLs")
            else:
                print("\nNo previous results found")
                
        elif choice == "4":
            print("\nGoodbye!")
            break
            
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()
