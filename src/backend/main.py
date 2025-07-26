#!/usr/bin/env python3
"""
SiteWatch Backend - FastAPI application for website monitoring
"""

import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
import uvicorn

from database import init_db, get_db
from models import ChatMessage, MonitoringJob, MonitoringResult
from services.monitoring import MonitoringService
from services.scheduler import SchedulerService
from api.websocket import ConnectionManager
from api.routes import router

# Global services
monitoring_service = None
scheduler_service = None
connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global monitoring_service, scheduler_service
    
    # Startup
    await init_db()
    monitoring_service = MonitoringService()
    scheduler_service = SchedulerService(monitoring_service, connection_manager)
    
    # Start scheduler
    asyncio.create_task(scheduler_service.start())
    
    yield
    
    # Shutdown
    if scheduler_service:
        await scheduler_service.stop()

app = FastAPI(
    title="SiteWatch API",
    description="Website monitoring with AI-powered analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "user_message":
                try:
                    # Save user message
                    async with get_db() as db:
                        chat_message = ChatMessage(
                            content=message_data["content"],
                            sender="user",
                            timestamp=datetime.now()
                        )
                        db.add(chat_message)
                        await db.commit()
                    
                    # Broadcast user message
                    await connection_manager.broadcast({
                        "type": "chat_message",
                        "message": {
                            "id": chat_message.id,
                            "content": chat_message.content,
                            "sender": "user",
                            "timestamp": chat_message.timestamp.isoformat()
                        }
                    })
                    
                    # Process monitoring request
                    if monitoring_service:
                        result = await monitoring_service.process_user_query(
                            message_data["content"], connection_manager
                        )
                        
                except Exception as e:
                    print(f"Error processing user message: {e}")
                    # Send error message back to user
                    await connection_manager.send_personal_message({
                        "type": "chat_message",
                        "message": {
                            "content": f"Sorry, there was an error processing your message: {str(e)}",
                            "sender": "system",
                            "timestamp": datetime.now().isoformat()
                        }
                    }, websocket)
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "SiteWatch Backend API", "status": "running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True
    ) 