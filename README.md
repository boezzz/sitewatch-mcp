# SiteWatch

An intelligent chatbot that discovers, monitors, and analyzes web content for meaningful changes on any topic.

## Core Mission

SiteWatch is your autonomous research assistant. Instead of manually searching for sources and repeatedly checking them for updates, you can assign SiteWatch a topic. It will **discover** relevant sources, **monitor** them continuously, and **alert** you only when meaningful changes occur.

  - **Conversational Discovery**: Simply ask SiteWatch to find sources for any topic, from "breakthroughs in quantum computing" to "official news from my competitor."
  - **Intelligent Monitoring**: It goes beyond simple file changes. SiteWatch analyzes content to differentiate between minor edits (like fixing a typo or changing an ad) and significant updates (like a new product announcement or a press release).
  - **Scheduled Analysis**: Define how often SiteWatch should check its sources, from minutes to days.
  - **Instant Alerts**: Receive email notifications the moment a significant change is detected, so you're always the first to know.

## Quick Start

### 1\. Install

```bash
git clone
cd sitewatch
pip install -r requirements.txt
```

### 2\. Configure

Create a `.env` file in the root directory. This is where you'll store your secrets and settings.

```env
# How often SiteWatch should check sources (in seconds)
CHECK_INTERVAL=3600

# Web Search API for the 'discover' command
# (e.g., Google Custom Search API, SerpAPI, etc.)
SEARCH_API_KEY=your_search_api_key_here

# Email notifications (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_google_app_password
NOTIFICATION_EMAIL=alerts_recipient@yourdomain.com
```

### 3\. Run

```bash
python main.py
```

## Interacting with SiteWatch

Start the program to enter the chat interface.

```
> discover sources for "breakthroughs in quantum computing"
SiteWatch has identified 5 high-relevance sources:
1. https://www.quantamagazine.org/tag/quantum-computing/
2. https://www.technologyreview.com/tag/quantum-computers/
3. https://phys.org/physics-news/quantum-physics/
...

> monitor 1
✓ Now monitoring: Quanta Magazine - Quantum Computing

> status
Currently monitoring 1 source:
- [UNCHANGED] Quanta Magazine - Quantum Computing (Last checked: 2m ago)

> # ... some time later ...
> status
Currently monitoring 1 source:
- [CHANGE DETECTED!] Quanta Magazine - Quantum Computing (Last checked: 1m ago)
```

## SiteWatch's Process

1.  **Discover**: The user provides a topic via the `discover` command. SiteWatch uses a web search API to identify a list of the most relevant and authoritative URLs.
2.  **Ingest & Baseline**: When you ask SiteWatch to `monitor` a URL, it performs an initial scrape of the site's main content, creating a clean "baseline" snapshot.
3.  **Monitor**: At the interval defined by `CHECK_INTERVAL`, SiteWatch re-scrapes the content of each target website.
4.  **Analyze & Alert**: It compares the newly scraped content against the stored baseline. Using text analysis algorithms, it determines if the changes are significant. If they are, it updates the baseline and sends an email notification.

## Chat Commands

  - `discover sources for "<topic>"`: Finds relevant URLs for any subject.
  - `monitor <url | number>`: Begins monitoring a new URL or a numbered result from a `discover` search.
  - `list`: Shows all sources currently being monitored.
  - `status`: Reports the current status of all monitored sources, highlighting any changes.
  - `stop <url>`: Stops monitoring a specific source.
  - `help`: Displays this list of commands.
  - `quit`: Shuts down SiteWatch.

## File Structure

```
sitewatch/
├── main.py              # The main application loop and chat interface
├── requirements.txt     # Project dependencies
├── .env                 # Your configuration and API keys
└── src/
    ├── monitor.py       # The core monitoring logic for scheduling and change analysis
    ├── scraper.py       # Fetches and cleans web content (SiteWatch's 'eyes')
    ├── search.py        # Handles the 'discover' command using a search API
    ├── database.py      # Stores content baselines and historical snapshots
    └── notifications.py # Manages and sends email alerts
```

## Example Missions

### Mission: Track a Competitor

```
> discover sources for "official news from OpenAI"
SiteWatch has identified 4 high-relevance sources:
1. https://openai.com/blog
2. https://openai.com/index/
...

> monitor 1
✓ Now monitoring: OpenAI Blog

> monitor 2
✓ Now monitoring: OpenAI Index
```

### Mission: Follow Legislative Changes

```
> discover sources for "US federal AI regulation bills"
SiteWatch has identified 6 high-relevance sources:
1. https://www.congress.gov/search?q={"source":"legislation","search":"AI"}
2. https://www.eff.org/issues/ai
...

> monitor https://www.congress.gov/search?q={"source":"legislation","search":"AI"}
✓ Now monitoring: Congress.gov - AI Bills
```

## Troubleshooting

**The `discover` command finds no results?**

  - Ensure your `SEARCH_API_KEY` in the `.env` file is valid and has not exceeded its quota.
  - Check your internet connection.
  - Try rephrasing your topic with broader or more specific terms.

**Not receiving email alerts?**

  - Verify your `SMTP_*` settings in `.env` are correct. For Gmail, you will need to generate an "App Password".
  - Check your spam folder.
  - Look for SMTP connection errors in the console output.

**Errors during monitoring?**

  - Some websites use advanced techniques to block automated scrapers. The console log may show an HTTP error (e.g., `403 Forbidden`).
  - Make sure all dependencies are correctly installed via `pip install -r requirements.txt`.

## Requirements

  - Python 3.8+
  - An active internet connection
  - A Search API Key for the `discover` functionality (e.g., Google Custom Search, SerpApi)
  - (Optional) An email account for SMTP notifications.

## License

This project is licensed under the MIT License - see the LICENSE file for details.