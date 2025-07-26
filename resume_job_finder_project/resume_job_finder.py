import os
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import webbrowser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from resume_parser import ResumeParser
from job_matcher import JobMatcher
from google_drive_connector import GoogleDriveConnector, setup_google_drive

class ResumeJobFinder:
    """Main application for resume-based job finding"""
    
    def __init__(self):
        self.resume_parser = ResumeParser()
        self.job_matcher = JobMatcher()
        self.google_drive = GoogleDriveConnector()
        self.results_dir = Path("job_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def process_resume_and_find_jobs(self, resume_path: str, max_jobs: int = 20) -> Dict:
        """Main function to process resume and find relevant jobs"""
        print("🚀 Starting Resume Job Finder...")
        print("=" * 50)
        
        # Step 1: Parse resume
        print("📄 Step 1: Parsing your resume...")
        try:
            resume_data = self.resume_parser.parse_resume(resume_path)
            print("✅ Resume parsed successfully!")
            self._display_resume_summary(resume_data)
        except Exception as e:
            print(f"❌ Error parsing resume: {e}")
            return {"error": str(e)}
        
        # Step 2: Find relevant jobs
        print("\n🔍 Step 2: Finding relevant jobs...")
        try:
            jobs = self.job_matcher.find_relevant_jobs(resume_data, max_jobs)
            print(f"✅ Found {len(jobs)} relevant jobs!")
        except Exception as e:
            print(f"❌ Error finding jobs: {e}")
            return {"error": str(e)}
        
        # Step 3: Get direct job links
        print("\n🔗 Step 3: Extracting direct job links...")
        try:
            jobs_with_links = self.job_matcher.get_direct_job_links(jobs)
            print("✅ Direct links extracted!")
        except Exception as e:
            print(f"❌ Error extracting links: {e}")
            jobs_with_links = jobs
        
        # Step 4: Generate results
        results = {
            "resume_data": resume_data,
            "jobs": jobs_with_links,
            "timestamp": datetime.now().isoformat(),
            "total_jobs": len(jobs_with_links),
            "direct_links": len([j for j in jobs_with_links if j.get('is_direct', False)])
        }
        
        # Step 5: Save and display results
        self._save_results(results, resume_path)
        self._display_results(results)
        
        return results
    
    def _display_resume_summary(self, resume_data: Dict):
        """Display a summary of parsed resume data"""
        # Use the new comprehensive print function
        self.parser.print_parsed_resume(resume_data)
    
    def _display_results(self, results: Dict):
        """Display job search results"""
        jobs = results.get('jobs', [])
        
        print("\n🎯 Job Search Results:")
        print("=" * 50)
        print(f"📊 Total Jobs Found: {results['total_jobs']}")
        print(f"🔗 Direct Links: {results['direct_links']}")
        print(f"⏰ Search Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if not jobs:
            print("❌ No relevant jobs found. Try adjusting your search criteria.")
            return
        
        # Group jobs by source
        jobs_by_source = {}
        for job in jobs:
            source = job.get('source', 'Unknown')
            if source not in jobs_by_source:
                jobs_by_source[source] = []
            jobs_by_source[source].append(job)
        
        # Display jobs by source
        for source, source_jobs in jobs_by_source.items():
            print(f"📋 {source} ({len(source_jobs)} jobs):")
            print("-" * 40)
            
            for i, job in enumerate(source_jobs[:5], 1):  # Show top 5 per source
                relevance = job.get('relevance_score', 0)
                is_direct = job.get('is_direct', False)
                skills_match = job.get('skills_match_percentage', 0)
                matched_skills = job.get('matched_skills', [])
                
                print(f"{i}. {job['title']}")
                print(f"   🏢 {job['company']}")
                if job.get('location'):
                    print(f"   📍 {job['location']}")
                print(f"   ⭐ Relevance: {relevance:.1f}")
                print(f"   🎯 Skills Match: {skills_match:.1f}% ({len(matched_skills)}/{job.get('total_skills_required', 0)} skills)")
                if matched_skills:
                    print(f"   ✅ Matched Skills: {', '.join(matched_skills[:5])}{'...' if len(matched_skills) > 5 else ''}")
                print(f"   🔗 {'Direct Link' if is_direct else 'Job Board Link'}")
                print()
        
        # Show top recommendations
        top_jobs = sorted(jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)[:5]
        print("🏆 Top Recommendations:")
        print("-" * 30)
        
        for i, job in enumerate(top_jobs, 1):
            skills_match = job.get('skills_match_percentage', 0)
            matched_skills = job.get('matched_skills', [])
            print(f"{i}. {job['title']} at {job['company']}")
            print(f"   Relevance: {job.get('relevance_score', 0):.1f}")
            print(f"   Skills Match: {skills_match:.1f}% ({len(matched_skills)}/{job.get('total_skills_required', 0)} skills)")
            if job.get('direct_url'):
                print(f"   Link: {job['direct_url']}")
            print()
    
    def _save_results(self, results: Dict, resume_path: str):
        """Save results to file"""
        resume_name = Path(resume_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results as JSON
        json_file = self.results_dir / f"job_results_{resume_name}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save summary as text
        txt_file = self.results_dir / f"job_summary_{resume_name}_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_summary_text(results))
        
        print(f"\n💾 Results saved to:")
        print(f"   📄 Detailed: {json_file}")
        print(f"   📝 Summary: {txt_file}")
    
    def _generate_summary_text(self, results: Dict) -> str:
        """Generate a text summary of results"""
        jobs = results.get('jobs', [])
        
        summary = f"""
RESUME JOB FINDER RESULTS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
- Total Jobs Found: {results['total_jobs']}
- Direct Links: {results['direct_links']}
- Resume: {results.get('resume_data', {}).get('name', 'Unknown')}

TOP RECOMMENDATIONS:
"""
        
        # Top 10 jobs by relevance
        top_jobs = sorted(jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)[:10]
        
        for i, job in enumerate(top_jobs, 1):
            summary += f"""
{i}. {job['title']}
   Company: {job['company']}
   Location: {job.get('location', 'Not specified')}
   Source: {job.get('source', 'Unknown')}
   Relevance Score: {job.get('relevance_score', 0)}/20
   Direct Link: {'Yes' if job.get('is_direct', False) else 'No'}
   URL: {job.get('direct_url', job.get('url', 'Not available'))}
"""
        
        return summary
    
    def open_job_links(self, results: Dict, max_links: int = 5):
        """Open job links in browser"""
        jobs = results.get('jobs', [])
        if not jobs:
            print("❌ No jobs to open.")
            return
        
        # Get top jobs with direct links
        direct_jobs = [j for j in jobs if j.get('is_direct', False)]
        if not direct_jobs:
            direct_jobs = jobs  # Fallback to all jobs
        
        # Sort by relevance and take top ones
        top_jobs = sorted(direct_jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)[:max_links]
        
        print(f"\n🌐 Opening top {len(top_jobs)} job links in browser...")
        
        for i, job in enumerate(top_jobs, 1):
            url = job.get('direct_url', job.get('url'))
            if url:
                print(f"{i}. Opening: {job['title']} at {job['company']}")
                try:
                    webbrowser.open(url)
                except Exception as e:
                    print(f"   ❌ Failed to open: {e}")
    
    def send_results_email(self, results: Dict, email: str, resume_name: str = "Your Resume"):
        """Send results via email"""
        try:
            # Email configuration
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not all([smtp_username, smtp_password]):
                print("❌ Email settings not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
                return False
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = email
            msg['Subject'] = f"Job Search Results for {resume_name}"
            
            # Email body
            body = self._generate_email_body(results, resume_name)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Results sent to {email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def _generate_email_body(self, results: Dict, resume_name: str) -> str:
        """Generate HTML email body"""
        jobs = results.get('jobs', [])
        top_jobs = sorted(jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)[:10]
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .job {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .job-title {{ font-weight: bold; color: #2c3e50; }}
                .company {{ color: #7f8c8d; }}
                .link {{ color: #3498db; text-decoration: none; }}
                .score {{ background-color: #e8f5e8; padding: 2px 6px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🎯 Job Search Results for {resume_name}</h2>
                <p><strong>Total Jobs Found:</strong> {results['total_jobs']}</p>
                <p><strong>Direct Links:</strong> {results['direct_links']}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h3>🏆 Top Recommendations</h3>
        """
        
        for i, job in enumerate(top_jobs, 1):
            url = job.get('direct_url', job.get('url', ''))
            html += f"""
            <div class="job">
                <div class="job-title">{i}. {job['title']}</div>
                <div class="company">🏢 {job['company']}</div>
                <div>📍 {job.get('location', 'Location not specified')}</div>
                <div>📊 Source: {job.get('source', 'Unknown')}</div>
                <div>⭐ Relevance: <span class="score">{job.get('relevance_score', 0)}/20</span></div>
                <div>🔗 <a href="{url}" class="link">View Job</a></div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def get_resume_recommendations(self, resume_data: Dict) -> List[str]:
        """Get recommendations for improving the resume"""
        recommendations = []
        
        # Check for missing information
        if not resume_data.get('skills'):
            recommendations.append("🔧 Add technical skills section with specific technologies")
        
        if not resume_data.get('job_titles'):
            recommendations.append("💼 Include clear job titles and roles")
        
        if not resume_data.get('years_experience'):
            recommendations.append("⏰ Specify years of experience")
        
        if not resume_data.get('summary'):
            recommendations.append("📝 Add a professional summary or objective")
        
        if not resume_data.get('education'):
            recommendations.append("🎓 Include education information")
        
        # Check for skill variety
        skills = resume_data.get('skills', {})
        if skills:
            total_skills = sum(len(skill_list) for skill_list in skills.values())
            if total_skills < 5:
                recommendations.append("🛠️ Add more technical skills to increase job matches")
        
        # Check for experience details
        experience = resume_data.get('experience', [])
        if len(experience) < 2:
            recommendations.append("🏢 Include more work experience details")
        
        # General recommendations
        recommendations.extend([
            "📊 Use action verbs and quantify achievements",
            "🎯 Tailor resume for specific job types",
            "📱 Ensure resume is ATS-friendly (simple formatting)",
            "🔍 Include relevant keywords for your target roles",
            "📈 Highlight measurable results and impact"
        ])
        
        return recommendations

def main():
    """Main function to run the Resume Job Finder"""
    print("🎯 Resume Job Finder")
    print("=" * 50)
    
    # Choose resume source
    print("📄 Choose resume source:")
    print("1. Google Drive")
    print("2. Local file path")
    print("3. Setup Google Drive (first time)")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    resume_path = None
    
    if choice == "1":
        # Google Drive option
        resume_path = get_resume_from_google_drive()
    elif choice == "2":
        # Local file option
        resume_path = input("📄 Enter the path to your resume file (PDF, DOCX, or TXT): ").strip()
    elif choice == "3":
        # Setup Google Drive
        setup_google_drive()
        print("\nAfter setting up Google Drive, run the application again and choose option 1.")
        return
    else:
        print("❌ Invalid choice.")
        return
    
    if not resume_path:
        print("❌ No resume file specified.")
        return
    
    # Create job finder instance
    finder = ResumeJobFinder()
    
    # Process resume and find jobs
    results = finder.process_resume_and_find_jobs(resume_path)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Show resume recommendations
    print("\n💡 Resume Improvement Recommendations:")
    print("-" * 40)
    recommendations = finder.get_resume_recommendations(results['resume_data'])
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    # Ask user what to do next
    print("\n" + "=" * 50)
    print("What would you like to do next?")
    print("1. Open top job links in browser")
    print("2. Send results via email")
    print("3. View saved results")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        max_links = int(input("How many links to open? (default 5): ") or "5")
        finder.open_job_links(results, max_links)
    
    elif choice == "2":
        email = input("Enter your email address: ").strip()
        if email:
            finder.send_results_email(results, email)
    
    elif choice == "3":
        print(f"\n📁 Results saved in: {finder.results_dir}")
    
    # Clean up temporary files
    print("\n🧹 Cleaning up temporary files...")
    finder.google_drive.cleanup_temp_files()
    
    print("\n✅ Thank you for using Resume Job Finder!")

def get_resume_from_google_drive() -> str:
    """Get resume file from Google Drive"""
    finder = ResumeJobFinder()
    
    print("\n🔍 Searching Google Drive for resume files...")
    
    # Try to authenticate
    if not finder.google_drive.authenticate():
        print("❌ Google Drive authentication failed.")
        return None
    
    # List resume files
    files = finder.google_drive.list_resume_files()
    
    if not files:
        print("❌ No resume files found in Google Drive.")
        print("💡 Make sure your resume files contain 'resume', 'cv', 'curriculum', or 'profile' in the filename.")
        return None
    
    # Let user choose a file
    print(f"\n📋 Select a resume file (1-{len(files)}):")
    
    try:
        choice = int(input("Enter file number: ").strip())
        if choice < 1 or choice > len(files):
            print("❌ Invalid choice.")
            return None
        
        selected_file = files[choice - 1]
        print(f"📥 Downloading: {selected_file['name']}")
        
        # Download the file
        local_path = finder.google_drive.download_file(
            selected_file['id'], 
            selected_file['name']
        )
        
        if local_path:
            print(f"✅ Resume downloaded successfully!")
            return local_path
        else:
            print("❌ Failed to download resume.")
            return None
            
    except ValueError:
        print("❌ Please enter a valid number.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    main() 