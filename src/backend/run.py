#!/usr/bin/env python3
"""
Simple run script for SiteWatch backend
"""

import uvicorn
import os

if __name__ == "__main__":
    # Set environment variables if not set
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY environment variable not set.")
        print("Some features will be limited without an OpenAI API key.")
    
    print("Starting SiteWatch backend on http://localhost:8081")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True
    ) 