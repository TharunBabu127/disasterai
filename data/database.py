"""
Database models and initialization for DisasterAI.
Uses SQLAlchemy ORM for data persistence.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import db_config

Base = declarative_base()


class Disaster(Base):
    """Model for storing disaster incidents"""
    __tablename__ = "disasters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    type = Column(String(50), nullable=False)
    location = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=False)
    risk_level = Column(String(20), nullable=False)
    risk_score = Column(Integer, nullable=False)
    population = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    estimated_response_time_hours = Column(Integer, nullable=False)
    immediate_threats = Column(JSON, default=list)  # List of strings
    recommended_actions = Column(JSON, default=list)  # List of strings
    resources_needed = Column(JSON, default=dict)  # Dict with resource quantities
    priority_zones = Column(JSON, default=list)  # List of zone names
    geo_valid = Column(Boolean, default=True)
    geo_warning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%d %b %Y, %H:%M:%S") if self.timestamp else None,
            "type": self.type,
            "location": self.location,
            "severity": self.severity,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "population": self.population,
            "coords": (self.latitude, self.longitude),
            "assessment": {
                "immediate_threats": self.immediate_threats,
                "recommended_actions": self.recommended_actions,
                "resources_needed": self.resources_needed,
                "estimated_response_time_hours": self.estimated_response_time_hours,
                "priority_zones": self.priority_zones,
                "geo_valid": self.geo_valid,
                "geo_warning": self.geo_warning,
            }
        }

    @property
    def assessment_dict(self) -> dict:
        """Return assessment dict for backward compatibility"""
        return {
            "immediate_threats": self.immediate_threats,
            "recommended_actions": self.recommended_actions,
            "resources_needed": self.resources_needed,
            "estimated_response_time_hours": self.estimated_response_time_hours,
            "priority_zones": self.priority_zones,
            "geo_valid": self.geo_valid,
            "geo_warning": self.geo_warning,
        }

    @classmethod
    def from_assessment(cls, location: str, disaster_type: str, population: int, assessment: dict):
        """Create Disaster instance from assessment result"""
        coords = assessment.get("coords", (0.0, 0.0))
        return cls(
            type=disaster_type,
            location=location,
            severity=assessment.get("severity", "Medium"),
            risk_level=assessment.get("risk_level", "Medium"),
            risk_score=assessment.get("risk_score", 50),
            population=population,
            latitude=coords[0],
            longitude=coords[1],
            estimated_response_time_hours=assessment.get("estimated_response_time_hours", 12),
            immediate_threats=assessment.get("immediate_threats", []),
            recommended_actions=assessment.get("recommended_actions", []),
            resources_needed=assessment.get("resources_needed", {}),
            priority_zones=assessment.get("priority_zones", []),
            geo_valid=assessment.get("geo_valid", True),
            geo_warning=assessment.get("geo_warning")
        )


class Volunteer(Base):
    """Model for storing volunteer information"""
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    skill = Column(String(100), nullable=False)
    region = Column(String(200), nullable=False)
    status = Column(String(50), default="Available")
    registered_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "skill": self.skill,
            "region": self.region,
            "status": self.status,
            "registered_at": self.registered_at.strftime("%d %b %Y, %H:%M:%S") if self.registered_at else None
        }


class ResourceAllocation(Base):
    """Model for tracking resource allocations over time"""
    __tablename__ = "resource_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    disaster_id = Column(Integer, nullable=False)  # Reference to disaster
    resource_type = Column(String(50), nullable=False)  # e.g., "medical_kits", "food_packages"
    quantity = Column(Integer, nullable=False)
    allocated_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "disaster_id": self.disaster_id,
            "resource_type": self.resource_type,
            "quantity": self.quantity,
            "allocated_at": self.allocated_at.strftime("%d %b %Y, %H:%M:%S") if self.allocated_at else None
        }


class SystemLog(Base):
    """Model for audit logs and system events"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)  # e.g., "disaster_created", "resource_allocated"
    message = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "message": self.message,
            "metadata": self.metadata,
            "created_at": self.created_at.strftime("%d %b %Y, %H:%M:%S") if self.created_at else None
        }


# Database connection management
class Database:
    """Singleton database manager"""
    _instance = None
    _engine = None
    _Session = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize database connection"""
        self._engine = create_engine(db_config.DATABASE_URL, echo=db_config.ECHO_SQL)
        self._Session = sessionmaker(bind=self._engine)

        # Create all tables if they don't exist
        Base.metadata.create_all(self._engine)

    def get_session(self):
        """Get a new database session"""
        return self._Session()

    @property
    def engine(self):
        return self._engine


# Convenience functions
def get_db_session():
    """Get database session (for use with context managers)"""
    return Database().get_session()


def init_database():
    """Initialize database - create tables"""
    db = Database()
    return db.engine