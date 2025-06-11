from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from .database import Base
import datetime
import json
from contextlib import contextmanager

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(String, primary_key=True)
    name = Column(String, default='New Chat')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    messages = relationship('Message', back_populates='session', cascade='all, delete-orphan')
    sources = relationship('Source', back_populates='session', cascade='all, delete-orphan')

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    role = Column(String)
    content = Column(Text)
    ai_type = Column(String, nullable=True)
    message_sources = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    session = relationship('Session', back_populates='messages')
    
    def set_sources(self, sources_list):
        """Store sources as JSON"""
        if sources_list is None:
            self.message_sources = None
        else:
            self.message_sources = json.dumps(sources_list)
    
    def get_sources(self):
        """Get sources from JSON"""
        if not self.message_sources:
            return []
        try:
            return json.loads(self.message_sources)
        except (json.JSONDecodeError, TypeError):
            return []

class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    name = Column(String)
    content = Column(Text)
    source_metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    document_type = Column(String, default='document')
    session = relationship('Session', back_populates='sources')
    
    def set_metadata(self, metadata_dict):
        """Store metadata as JSON"""
        if metadata_dict is None:
            self.source_metadata = None
        else:
            self.source_metadata = json.dumps(metadata_dict)
    
    def get_metadata(self):
        """Get metadata from JSON"""
        if not self.source_metadata:
            return {}
        try:
            return json.loads(self.source_metadata)
        except (json.JSONDecodeError, TypeError):
            return {}

class UsageStat(Base):
    __tablename__ = 'usage_stats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_type = Column(String)
    count = Column(Integer, default=0)

# Import engine from database.py to use the correct database configuration
from .database import engine, SessionLocal

Base.metadata.create_all(engine)

@contextmanager
def get_db_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
