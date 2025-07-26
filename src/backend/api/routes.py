"""
REST API routes for SiteWatch
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from sqlalchemy import select, desc
from datetime import datetime

from database import get_db
from models import ChatMessage, MonitoringJob, MonitoringResult

router = APIRouter()

@router.get("/chat/messages")
async def get_chat_messages(limit: int = 50):
    """Get recent chat messages"""
    try:
        async with get_db() as db:
            stmt = select(ChatMessage).order_by(desc(ChatMessage.timestamp)).limit(limit)
            result = await db.execute(stmt)
            messages = result.scalars().all()
            
            return [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "job_id": msg.job_id
                }
                for msg in reversed(messages)  # Reverse to get chronological order
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs")
async def get_monitoring_jobs():
    """Get all monitoring jobs"""
    try:
        async with get_db() as db:
            stmt = select(MonitoringJob).order_by(desc(MonitoringJob.created_at))
            result = await db.execute(stmt)
            jobs = result.scalars().all()
            
            return [
                {
                    "id": job.id,
                    "name": job.name,
                    "query": job.query,
                    "urls": job.urls,
                    "monitoring_focus": job.monitoring_focus,
                    "schedule_cron": job.schedule_cron,
                    "is_active": job.is_active,
                    "created_at": job.created_at.isoformat(),
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "next_run": job.next_run.isoformat() if job.next_run else None
                }
                for job in jobs
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/results")
async def get_job_results(job_id: int, limit: int = 10):
    """Get results for a specific monitoring job"""
    try:
        async with get_db() as db:
            stmt = select(MonitoringResult).where(
                MonitoringResult.job_id == job_id
            ).order_by(desc(MonitoringResult.timestamp)).limit(limit)
            
            result = await db.execute(stmt)
            results = result.scalars().all()
            
            return [
                {
                    "id": res.id,
                    "timestamp": res.timestamp.isoformat(),
                    "summary": res.summary,
                    "has_changes": res.has_changes,
                    "change_analysis": res.change_analysis
                }
                for res in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/toggle")
async def toggle_job_status(job_id: int):
    """Toggle job active status"""
    try:
        async with get_db() as db:
            job = await db.get(MonitoringJob, job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            job.is_active = not job.is_active
            await db.commit()
            
            return {
                "id": job.id,
                "name": job.name,
                "is_active": job.is_active
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int):
    """Delete a monitoring job"""
    try:
        async with get_db() as db:
            job = await db.get(MonitoringJob, job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            await db.delete(job)
            await db.commit()
            
            return {"message": "Job deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    """Get application statistics"""
    try:
        async with get_db() as db:
            # Count total jobs
            jobs_stmt = select(MonitoringJob)
            jobs_result = await db.execute(jobs_stmt)
            total_jobs = len(jobs_result.scalars().all())
            
            # Count active jobs
            active_jobs_stmt = select(MonitoringJob).where(MonitoringJob.is_active == True)
            active_jobs_result = await db.execute(active_jobs_stmt)
            active_jobs = len(active_jobs_result.scalars().all())
            
            # Count total results
            results_stmt = select(MonitoringResult)
            results_result = await db.execute(results_stmt)
            total_results = len(results_result.scalars().all())
            
            # Count messages
            messages_stmt = select(ChatMessage)
            messages_result = await db.execute(messages_stmt)
            total_messages = len(messages_result.scalars().all())
            
            return {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "total_monitoring_results": total_results,
                "total_chat_messages": total_messages
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 