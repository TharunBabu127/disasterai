"""
Repository layer for data access.
Provides clean interface for CRUD operations on disasters and volunteers.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
import random

from .database import get_db_session, Disaster, Volunteer, SystemLog
from config import geographic, disaster, resources, api_config


class DisasterRepository:
    """Repository for disaster incidents"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session if session else get_db_session()

    def create(self, location: str, disaster_type: str, population: int, assessment: dict) -> Disaster:
        """Create new disaster record"""
        disaster_record = Disaster.from_assessment(
            location=location,
            disaster_type=disaster_type,
            population=population,
            assessment=assessment
        )
        self.session.add(disaster_record)
        self.session.commit()

        # Log the event
        self._log_event("disaster_created", f"New {disaster_type} incident at {location}", {
            "disaster_id": disaster_record.id,
            "risk_score": assessment.get("risk_score")
        })

        return disaster_record

    def get_all(self) -> List[Disaster]:
        """Get all disasters, most recent first"""
        return self.session.query(Disaster).order_by(desc(Disaster.created_at)).all()

    def get_by_id(self, disaster_id: int) -> Optional[Disaster]:
        """Get disaster by ID"""
        return self.session.query(Disaster).filter(Disaster.id == disaster_id).first()

    def get_by_risk_level(self, risk_level: str) -> List[Disaster]:
        """Get disasters filtered by risk level"""
        return self.session.query(Disaster).filter(
            Disaster.risk_level == risk_level
        ).order_by(desc(Disaster.risk_score)).all()

    def get_critical(self) -> List[Disaster]:
        """Get all critical risk disasters"""
        return self.get_by_risk_level("Critical")

    def delete(self, disaster_id: int) -> bool:
        """Delete disaster by ID"""
        disaster = self.get_by_id(disaster_id)
        if disaster:
            self.session.delete(disaster)
            self.session.commit()
            self._log_event("disaster_deleted", f"Disaster #{disaster_id} deleted", {"disaster_id": disaster_id})
            return True
        return False

    def clear_completed(self) -> int:
        """Delete all completed disasters - returns count of deleted records"""
        # For our use case, we don't actually mark as completed, but this could be used
        # if we add a status field
        count = self.session.query(Disaster).filter(
            Disaster.risk_level == "Low"
        ).count()
        # Actually, let's not auto-delete - that would lose data
        # Instead, just return 0 and let UI handle filtering
        return 0

    def _log_event(self, event_type: str, message: str, metadata: dict = None):
        """Log system event"""
        log = SystemLog(
            event_type=event_type,
            message=message,
            metadata=metadata or {}
        )
        self.session.add(log)
        self.session.commit()

    def close(self):
        """Close session"""
        self.session.close()


class VolunteerRepository:
    """Repository for volunteer records"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session if session else get_db_session()

    def create(self, name: str, skill: str, region: str, status: str = "Available") -> Volunteer:
        """Create new volunteer"""
        volunteer = Volunteer(
            name=name,
            skill=skill,
            region=region,
            status=status
        )
        self.session.add(volunteer)
        self.session.commit()

        # Log the event
        self._log_event("volunteer_registered", f"{name} registered with skill {skill}", {
            "volunteer_id": volunteer.id,
            "skill": skill,
            "region": region
        })

        return volunteer

    def get_all(self) -> List[Volunteer]:
        """Get all volunteers"""
        return self.session.query(Volunteer).order_by(Volunteer.registered_at).all()

    def get_by_skill(self, skill: str) -> List[Volunteer]:
        """Get volunteers with specific skill"""
        return self.session.query(Volunteer).filter(
            Volunteer.skill == skill
        ).filter(Volunteer.status == "Available").all()

    def get_by_region(self, region: str) -> List[Volunteer]:
        """Get volunteers from specific region"""
        return self.session.query(Volunteer).filter(
            Volunteer.region.ilike(f"%{region}%")
        ).all()

    def update_status(self, volunteer_id: int, status: str) -> Optional[Volunteer]:
        """Update volunteer status"""
        volunteer = self.session.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
        if volunteer:
            volunteer.status = status
            self.session.commit()
            return volunteer
        return None

    def delete(self, volunteer_id: int) -> bool:
        """Delete volunteer"""
        volunteer = self.session.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
        if volunteer:
            self.session.delete(volunteer)
            self.session.commit()
            self._log_event("volunteer_removed", f"Volunteer #{volunteer_id} removed", {"volunteer_id": volunteer_id})
            return True
        return False

    def get_available_count(self) -> int:
        """Count of available volunteers"""
        return self.session.query(Volunteer).filter(Volunteer.status == "Available").count()

    def _log_event(self, event_type: str, message: str, metadata: dict = None):
        """Log system event"""
        log = SystemLog(
            event_type=event_type,
            message=message,
            metadata=metadata or {}
        )
        self.session.add(log)
        self.session.commit()

    def close(self):
        """Close session"""
        self.session.close()


class StatisticsRepository:
    """Repository for statistical queries"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session if session else get_db_session()

    def get_total_incidents(self) -> int:
        """Total number of disasters"""
        return self.session.query(Disaster).count()

    def get_incidents_by_risk_level(self) -> Dict[str, int]:
        """Count incidents grouped by risk level"""
        from sqlalchemy import func
        results = self.session.query(
            Disaster.risk_level,
            func.count(Disaster.id)
        ).group_by(Disaster.risk_level).all()
        return dict(results)

    def get_total_population_affected(self) -> int:
        """Sum of affected population"""
        return self.session.query(func.coalesce(func.sum(Disaster.population), 0)).scalar() or 0

    def get_total_resources_needed(self) -> Dict[str, int]:
        """Calculate total resources needed across all incidents"""
        disasters = self.session.query(Disaster.resources_needed).all()
        totals = {}
        for d in disasters:
            resources = d[0] or {}
            for key, value in resources.items():
                totals[key] = totals.get(key, 0) + value
        return totals

    def get_average_risk_score(self) -> float:
        """Average risk score across all disasters"""
        from sqlalchemy import func
        avg = self.session.query(func.avg(Disaster.risk_score)).scalar()
        return round(avg or 0, 1)

    def get_incidents_over_time(self, days: int = 7) -> List[Dict]:
        """Get incident counts over time"""
        from sqlalchemy import func, cast, Date
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        results = self.session.query(
            cast(Disaster.created_at, Date),
            func.count(Disaster.id)
        ).filter(
            Disaster.created_at >= cutoff
        ).group_by(cast(Disaster.created_at, Date)).order_by(cast(Disaster.created_at, Date)).all()

        return [{"date": str(date), "count": count} for date, count in results]

    def get_priority_zones(self) -> List[Dict]:
        """Get all unique priority zones with incident counts"""
        from sqlalchemy import func
        # This is simplified - in production you'd normalize zones to a separate table
        disasters = self.session.query(Disaster.priority_zones).all()
        zone_counts = {}
        for d in disasters:
            if d[0]:
                for zone in d[0]:
                    zone_counts[zone] = zone_counts.get(zone, 0) + 1
        return [{"zone": zone, "incident_count": count} for zone, count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True)]

    def close(self):
        """Close session"""
        self.session.close()