"""
Scheduler service for running monitoring jobs
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from croniter import croniter

from database import get_db
from models import MonitoringJob
from services.monitoring import MonitoringService

class SchedulerService:
    def __init__(self, monitoring_service: MonitoringService, connection_manager):
        self.monitoring_service = monitoring_service
        self.connection_manager = connection_manager
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        print("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        print("Scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._check_and_run_jobs()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_and_run_jobs(self):
        """Check for jobs that need to run and execute them"""
        try:
            async with get_db() as db:
                from sqlalchemy import select
                
                # Get active jobs that are due to run
                now = datetime.now()
                stmt = select(MonitoringJob).where(
                    MonitoringJob.is_active == True,
                    MonitoringJob.next_run <= now
                )
                
                result = await db.execute(stmt)
                jobs_to_run = result.scalars().all()
                
                for job in jobs_to_run:
                    print(f"Running scheduled job: {job.name}")
                    
                    # Run the monitoring job
                    await self.monitoring_service.run_monitoring_for_job(
                        job.id, self.connection_manager
                    )
                    
                    # Calculate next run time
                    next_run = self._calculate_next_run(job.schedule_cron, now)
                    job.next_run = next_run
                    
                    await db.commit()
                    
        except Exception as e:
            print(f"Error checking and running jobs: {e}")
    
    def _calculate_next_run(self, cron_expression: str, from_time: datetime) -> datetime:
        """Calculate next run time from cron expression"""
        try:
            cron = croniter(cron_expression, from_time)
            return cron.get_next(datetime)
        except Exception as e:
            print(f"Error parsing cron expression {cron_expression}: {e}")
            # Default to next day at 9 AM
            next_day = from_time.replace(hour=9, minute=0, second=0, microsecond=0)
            if next_day <= from_time:
                next_day += timedelta(days=1)
            return next_day 