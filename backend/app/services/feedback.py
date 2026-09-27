from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.database import (
    FeedbackLoopDB, OrchestrationRecommendationDB, ZoneDB, ZoneCrowdStateDB,
    RiskAssessmentDB, RiskLevelEnum, EventDB
)
from app.services.risk import RiskEngine


class FeedbackLoop:
    def __init__(self, db: Session):
        self.db = db
        self.risk_engine = RiskEngine(db)
    
    def record_pre_action_state(self, recommendation_id: int) -> FeedbackLoopDB:
        rec = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == recommendation_id
        ).first()
        
        if not rec:
            raise ValueError("Recommendation not found")
        
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == rec.zone_id).first()
        if not zone:
            raise ValueError("Zone not found")
        
        pre_state = {
            "crowd": zone.current_crowd,
            "inflow": zone.inflow_per_minute,
            "outflow": zone.outflow_per_minute,
            "utilization": zone.utilization,
            "risk_level": zone.risk_level.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        feedback = FeedbackLoopDB(
            event_id=rec.event_id,
            zone_id=rec.zone_id,
            recommendation_id=recommendation_id,
            pre_action_state=pre_state,
            post_action_state=None,
            effectiveness_score=None,
            risk_change=None,
            stabilized=False
        )
        
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    async def evaluate_action_effectiveness(self, recommendation_id: int, minutes_after: int = 10) -> Dict:
        feedback = self.db.query(FeedbackLoopDB).filter(
            FeedbackLoopDB.recommendation_id == recommendation_id
        ).first()
        
        if not feedback:
            raise ValueError("Feedback record not found")
        
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == feedback.zone_id).first()
        if not zone:
            raise ValueError("Zone not found")
        
        # Recalculate zone risk to ensure post-action state reflects updated crowd metrics
        self.risk_engine.assess_zone_risk(zone.zone_id)
        self.db.refresh(zone)

        post_state = {
            "crowd": zone.current_crowd,
            "inflow": zone.inflow_per_minute,
            "outflow": zone.outflow_per_minute,
            "utilization": zone.utilization,
            "risk_level": zone.risk_level.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        pre = feedback.pre_action_state
        post = post_state
        
        inflow_change = post["inflow"] - pre["inflow"]
        outflow_change = post["outflow"] - pre["outflow"]
        crowd_change = post["crowd"] - pre["crowd"]
        utilization_change = post["utilization"] - pre["utilization"]
        
        risk_levels = {
            "normal": 0, "watch": 1, "warning": 2, "critical": 3, "overload": 4
        }
        pre_risk_score = risk_levels.get(pre["risk_level"], 0)
        post_risk_score = risk_levels.get(post["risk_level"], 0)
        risk_change = post_risk_score - pre_risk_score
        
        effectiveness = self._calculate_effectiveness(pre, post, risk_change)
        
        stabilized = (
            post["inflow"] <= post["outflow"] * 1.1 and
            post["utilization"] < 85 and
            risk_change <= 0
        )
        
        feedback.post_action_state = post_state
        feedback.effectiveness_score = effectiveness
        feedback.risk_change = risk_change
        feedback.stabilized = stabilized
        
        self.db.commit()
        self.db.refresh(feedback)
        
        if stabilized:
            await self._send_stabilization_alert(feedback)
        
        return {
            "feedback_id": feedback.id,
            "pre_state": pre,
            "post_state": post_state,
            "inflow_change": inflow_change,
            "outflow_change": outflow_change,
            "crowd_change": crowd_change,
            "utilization_change": utilization_change,
            "risk_change": risk_change,
            "effectiveness_score": effectiveness,
            "stabilized": stabilized
        }
    
    def _calculate_effectiveness(self, pre: Dict, post: Dict, risk_change: int) -> float:
        score = 0.0
        
        if risk_change < 0:
            score += 40
        elif risk_change == 0:
            score += 20
        else:
            score -= 20
        
        inflow_reduction = pre["inflow"] - post["inflow"]
        if inflow_reduction > 0:
            score += min(30, (inflow_reduction / max(pre["inflow"], 1)) * 50)
        
        outflow_increase = post["outflow"] - pre["outflow"]
        if outflow_increase > 0:
            score += min(20, (outflow_increase / max(pre["outflow"], 1)) * 30)
        
        util_reduction = pre["utilization"] - post["utilization"]
        if util_reduction > 0:
            score += min(10, util_reduction * 2)
        
        return max(0, min(100, score))
    
    async def _send_stabilization_alert(self, feedback: FeedbackLoopDB):
        from app.services.whatsapp import WhatsAppService
        whatsapp = WhatsAppService(self.db)
        
        event = self.db.query(EventDB).filter(EventDB.event_id == feedback.event_id).first()
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == feedback.zone_id).first()
        
        organizer_phone = None
        if event and hasattr(event, "operational_thresholds") and isinstance(event.operational_thresholds, dict):
            organizer_phone = event.operational_thresholds.get("organizer_whatsapp")
            
        if organizer_phone:
            message = f"✅ *Zone Stabilized*\n\n"
            message += f"*Zone:* {zone.name if zone else feedback.zone_id}\n"
            message += f"*Risk reduced from* {feedback.pre_action_state['risk_level']} *to* {feedback.post_action_state['risk_level']}\n"
            message += f"*Effectiveness Score:* {feedback.effectiveness_score:.0f}/100\n"
            
            await whatsapp.send_message(organizer_phone, message)
    
    def get_feedback_history(self, event_id: str) -> List[Dict]:
        feedbacks = self.db.query(FeedbackLoopDB).filter(
            FeedbackLoopDB.event_id == event_id
        ).order_by(FeedbackLoopDB.timestamp.desc()).all()
        
        return [
            {
                "id": f.id,
                "zone_id": f.zone_id,
                "recommendation_id": f.recommendation_id,
                "timestamp": f.timestamp.isoformat(),
                "pre_state": f.pre_action_state,
                "post_state": f.post_action_state,
                "effectiveness_score": f.effectiveness_score,
                "risk_change": f.risk_change,
                "stabilized": f.stabilized
            }
            for f in feedbacks
        ]
    
    def get_event_effectiveness_summary(self, event_id: str) -> Dict:
        feedbacks = self.db.query(FeedbackLoopDB).filter(
            FeedbackLoopDB.event_id == event_id
        ).all()
        
        if not feedbacks:
            return {"total_actions": 0, "avg_effectiveness": 0, "stabilized_count": 0}
        
        total = len(feedbacks)
        stabilized = sum(1 for f in feedbacks if f.stabilized)
        avg_effectiveness = sum(f.effectiveness_score or 0 for f in feedbacks) / total
        
        risk_improved = sum(1 for f in feedbacks if (f.risk_change or 0) < 0)
        risk_worsened = sum(1 for f in feedbacks if (f.risk_change or 0) > 0)
        
        return {
            "total_actions": total,
            "stabilized_count": stabilized,
            "stabilization_rate": stabilized / total if total > 0 else 0,
            "avg_effectiveness": avg_effectiveness,
            "risk_improved": risk_improved,
            "risk_worsened": risk_worsened,
            "risk_unchanged": total - risk_improved - risk_worsened
        }