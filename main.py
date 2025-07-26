import os
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool
from job_tool import JobScraperQueryEngine

# ✅ Set OpenAI key
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# ✅ LLM (using GPT-3.5-turbo for cost efficiency)
llm = OpenAI(model="gpt-3.5-turbo", temperature=0)

# ✅ Create your custom query engine
job_query_engine = JobScraperQueryEngine()

response = job_query_engine.query("Amazon")
print(response)

# ✅ Register tool with required metadata
job_scraper_tool = QueryEngineTool(
    query_engine=job_query_engine,
    metadata=job_query_engine.metadata   # <-- EXPLICIT metadata passing
)


# ✅ Create agent
agent = ReActAgent.from_tools(
    tools=[job_scraper_tool],
    llm=llm,
    verbose=True,
    system_prompt="""
You are a job tracking assistant. Use the JobScraperTool to find job listings from official company websites. 
Always provide short, readable summaries of job titles and source URLs.
"""
)

# ✅ Run the agent
response = agent.query("Get me new jobs from Amazon, Microsoft, and Salesforce.")
print("\n🔔 Job Notification:\n", response)
