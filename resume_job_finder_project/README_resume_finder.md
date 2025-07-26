# Resume Job Finder 🎯

An intelligent AI-powered system that analyzes your resume and finds relevant job opportunities with direct links to company career pages.

## 🌟 Features

### 📄 **Smart Resume Parsing**
- Supports PDF, DOCX, and TXT formats
- Extracts skills, experience, education, and contact information
- Uses NLP to understand resume content
- Identifies job titles, technologies, and experience levels

### 🔍 **Intelligent Job Matching**
- Searches multiple job sources (Indeed, LinkedIn, company career pages)
- Matches resume skills with job requirements
- Ranks jobs by relevance score
- Filters by experience level and location

### 🔗 **Direct Job Links**
- Extracts direct links to company career pages
- Bypasses job board redirects
- Provides actual application URLs
- Reduces application friction

### 📊 **Comprehensive Results**
- Detailed job analysis and ranking
- Resume improvement recommendations
- Email notifications with job summaries
- Browser integration for easy application

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd sitewatch-mcp

# Install dependencies
pip install -r requirements.txt

# Install spaCy language model
python -m spacy download en_core_web_sm
```

### 2. Configuration

Create a `.env` file in the root directory:

```env
# OpenAI API Key (for advanced analysis)
OPENAI_API_KEY=your_openai_api_key_here

# Email settings (optional, for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Usage

```bash
# Run the main application
python resume_job_finder.py
```

Follow the prompts to:
1. Upload your resume
2. Review parsed information
3. Get job recommendations
4. Open direct job links
5. Receive email notifications

## 📁 Project Structure

```
sitewatch-mcp/
├── resume_job_finder.py      # Main application
├── resume_parser.py          # Resume parsing and analysis
├── job_matcher.py            # Job search and matching
├── job_tool.py              # Existing job scraping tool
├── sitewatch_monitor.py     # Existing monitoring system
├── requirements.txt         # Dependencies
├── README_resume_finder.md  # This file
└── job_results/            # Generated results
    ├── job_results_*.json   # Detailed results
    └── job_summary_*.txt    # Text summaries
```

## 🔧 How It Works

### 1. **Resume Analysis**
```python
from resume_parser import ResumeParser

parser = ResumeParser()
resume_data = parser.parse_resume("path/to/resume.pdf")

# Extracted information:
# - Skills and technologies
# - Work experience and companies
# - Education and certifications
# - Contact information
# - Job titles and roles
```

### 2. **Job Matching**
```python
from job_matcher import JobMatcher

matcher = JobMatcher()
jobs = matcher.find_relevant_jobs(resume_data, max_jobs=20)

# Features:
# - Multi-source job search
# - Relevance scoring
# - Direct link extraction
# - Duplicate removal
```

### 3. **Results Processing**
```python
from resume_job_finder import ResumeJobFinder

finder = ResumeJobFinder()
results = finder.process_resume_and_find_jobs("resume.pdf")

# Output:
# - Ranked job recommendations
# - Direct application links
# - Resume improvement tips
# - Email notifications
```

## 📊 Resume Improvement Recommendations

The system analyzes your resume and provides specific recommendations:

### 🔧 **Technical Skills**
- Add specific programming languages
- Include frameworks and tools
- Mention cloud platforms and databases
- List relevant certifications

### 💼 **Experience Optimization**
- Use action verbs and metrics
- Quantify achievements
- Include relevant keywords
- Highlight leadership roles

### 📝 **Format and Structure**
- Ensure ATS-friendly formatting
- Use clear section headers
- Keep consistent formatting
- Include contact information

### 🎯 **Content Enhancement**
- Add professional summary
- Include relevant projects
- Mention industry-specific skills
- Highlight transferable skills

## 🔍 Job Search Sources

The system searches multiple sources for comprehensive results:

### **Job Boards**
- **Indeed**: General job listings
- **LinkedIn**: Professional network jobs
- **Glassdoor**: Company reviews and jobs
- **ZipRecruiter**: Aggregated listings

### **Company Career Pages**
- Direct company websites
- Career portals
- Job application systems
- Internal referral programs

### **Specialized Platforms**
- GitHub Jobs (for developers)
- Stack Overflow Jobs
- AngelList (for startups)
- Remote job platforms

## 📧 Email Notifications

Configure email settings to receive job alerts:

```python
# Example email configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

Email features:
- HTML-formatted job summaries
- Direct application links
- Relevance scores
- Company information

## 🛠️ Advanced Features

### **Custom Job Sources**
Add your own job sources by modifying `job_matcher.py`:

```python
def add_custom_source(self, source_name, search_url, parser_function):
    """Add custom job source"""
    self.custom_sources[source_name] = {
        'url': search_url,
        'parser': parser_function
    }
```

### **Resume Templates**
Create resume templates for different industries:

```python
def create_resume_template(self, industry, experience_level):
    """Generate resume template"""
    # Industry-specific formatting and sections
    pass
```

### **Job Application Tracking**
Track your applications and follow-ups:

```python
def track_application(self, job_id, application_date, status):
    """Track job application status"""
    pass
```

## 🔒 Privacy and Security

- **Local Processing**: Resume parsing happens locally
- **Secure Storage**: Results stored locally only
- **No Data Sharing**: Your resume data stays private
- **Optional Cloud**: Email notifications only if configured

## 🐛 Troubleshooting

### **Common Issues**

1. **Resume Not Parsing**
   - Ensure file format is supported (PDF, DOCX, TXT)
   - Check file is not corrupted
   - Verify file permissions

2. **No Jobs Found**
   - Check internet connection
   - Verify search terms are relevant
   - Try different resume formats

3. **Email Not Sending**
   - Verify SMTP settings
   - Check app password for Gmail
   - Ensure firewall allows SMTP

4. **Links Not Opening**
   - Check browser settings
   - Verify URL accessibility
   - Try manual copy-paste

### **Performance Optimization**

- Use SSD storage for faster file processing
- Increase timeout for slow connections
- Limit concurrent requests to avoid rate limiting
- Use VPN for geo-restricted content

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **spaCy** for NLP processing
- **BeautifulSoup** for web scraping
- **OpenAI** for advanced text analysis
- **Job boards** for providing job data

## 📞 Support

For questions, issues, or feature requests:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the documentation

---

**Happy job hunting! 🎯✨** 