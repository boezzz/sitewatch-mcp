"""
Database models for SiteWatch
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ChatMessage(Base):
    """Chat messages between user and system"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    sender = Column(String(10), nullable=False)  # 'user' or 'system'
    timestamp = Column(DateTime, default=datetime.utcnow)
    job_id = Column(Integer, ForeignKey("monitoring_jobs.id"), nullable=True)
    
    # Relationship
    job = relationship("MonitoringJob", back_populates="messages")

class MonitoringJob(Base):
    """Scheduled monitoring jobs"""
    __tablename__ = "monitoring_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    query = Column(Text, nullable=False)
    urls = Column(JSON, nullable=False)  # List of URLs to monitor
    monitoring_focus = Column(String(100), nullable=False)
    schedule_cron = Column(String(50), default="0 9 * * *")  # Daily at 9 AM
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    
    # Relationships
    results = relationship("MonitoringResult", back_populates="job")
    messages = relationship("ChatMessage", back_populates="job")

class MonitoringResult(Base):
    """Results from monitoring runs"""
    __tablename__ = "monitoring_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("monitoring_jobs.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    content = Column(JSON, nullable=False)  # Extracted content
    summary = Column(Text, nullable=False)
    content_hash = Column(String(32), nullable=False)
    has_changes = Column(Boolean, default=False)
    change_analysis = Column(Text, nullable=True)
    
    # Relationship
    job = relationship("MonitoringJob", back_populates="results") 