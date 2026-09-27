from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.database import (
    ZoneDB, ProviderDB, ProviderTypeEnum, ProviderStatusEnum, OrchestrationRecommendationDB,
    RiskAssessmentDB, RiskLevelEnum, ActionExecutionDB, EventDB
)
from app.services.risk import RiskEngine


class OrchestrationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.risk_engine = RiskEngine(db)
    
    def generate_recommendations(self, event_id: str) -> List[Dict]:
        risk_summary = self.risk_engine.get_risk_summary(event_id)
        recommendations = []
        
        for critical_zone_info in risk_summary["critical_zones"]:
            zone_id = critical_zone_info["zone_id"]
            zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
            if not zone:
                continue
            
            zone_recommendations = self._generate_zone_recommendations(zone)
            recommendations.extend(zone_recommendations)
        
        return recommendations
    
    def _generate_zone_recommendations(self, zone: ZoneDB) -> List[Dict]:
        recommendations = []
        
        if zone.risk_level in [RiskLevelEnum.WARNING, RiskLevelEnum.CRITICAL, RiskLevelEnum.OVERLOAD]:
            redirect_rec = self._recommend_demand_redirect(zone)
            if redirect_rec:
                recommendations.append(redirect_rec)
            
            transport_rec = self._recommend_transport_increase(zone)
            if transport_rec:
                recommendations.append(transport_rec)
            
            venue_rec = self._recommend_venue_action(zone)
            if venue_rec:
                recommendations.append(venue_rec)
        
        return recommendations
    
    def _recommend_demand_redirect(self, zone: ZoneDB) -> Optional[Dict]:
        event_zones = self.db.query(ZoneDB).filter(
            ZoneDB.event_id == zone.event_id,
            ZoneDB.zone_id != zone.zone_id
        ).all()
        
        target_zones = []
        for z in event_zones:
            if z.utilization < 70 and z.capacity > z.current_crowd:
                spare = z.capacity - z.current_crowd
                target_zones.append({"zone_id": z.zone_id, "name": z.name, "spare_capacity": spare})
        
        if not target_zones:
            return None
        
        target_zones.sort(key=lambda x: x["spare_capacity"], reverse=True)
        best_target = target_zones[0]
        
        transport_available = self._check_transport_between_zones(zone.zone_id, best_target["zone_id"], event_id=zone.event_id)
        
        return {
            "type": "demand_redirect",
            "priority": "high",
            "source_zone_id": zone.zone_id,
            "target_zone_id": best_target["zone_id"],
            "description": f"Redirect incoming demand from {zone.name} to {best_target['name']} (spare capacity: {best_target['spare_capacity']})",
            "actions": [
                {
                    "action": "redirect_flow",
                    "source_zone": zone.zone_id,
                    "target_zone": best_target["zone_id"],
                    "percentage": 30
                },
                {
                    "action": "update_signage",
                    "zones": [zone.zone_id, best_target["zone_id"]]
                }
            ],
            "required_providers": self._get_providers_for_redirect(zone.zone_id, best_target["zone_id"], event_id=zone.event_id),
            "transport_available": transport_available,
            "estimated_impact": "Reduce inflow by 30-40%"
        }
    
    def _recommend_transport_increase(self, zone: ZoneDB) -> Optional[Dict]:
        transport_providers = self.db.query(ProviderDB).filter(
            ProviderDB.zone_id == zone.zone_id,
            ProviderDB.type == ProviderTypeEnum.TRANSPORT,
            ProviderDB.status.in_([ProviderStatusEnum.ACTIVE, "ACTIVE", "active"])
        ).all()
        
        available_transport = [p for p in transport_providers if p.capacity.get("available", 0) > 0]
        
        if not available_transport:
            return None
        
        total_available = sum(p.capacity.get("available", 0) for p in available_transport)
        
        return {
            "type": "increase_transport",
            "priority": "high",
            "zone_id": zone.zone_id,
            "description": f"Deploy additional transport from {zone.name} (available capacity: {total_available})",
            "actions": [
                {
                    "action": "deploy_transport",
                    "zone_id": zone.zone_id,
                    "providers": [p.provider_id for p in available_transport[:3]],
                    "additional_capacity": min(total_available, 500)
                }
            ],
            "required_providers": [p.provider_id for p in available_transport[:3]],
            "estimated_impact": f"Increase outflow by {min(total_available, 500)} people/min"
        }
    
    def _recommend_venue_action(self, zone: ZoneDB) -> Optional[Dict]:
        venue_providers = self.db.query(ProviderDB).filter(
            ProviderDB.zone_id == zone.zone_id,
            ProviderDB.type == ProviderTypeEnum.VENUE,
            ProviderDB.status.in_([ProviderStatusEnum.ACTIVE, "ACTIVE", "active"])
        ).all()
        
        actions = []
        for venue in venue_providers:
            if venue.capacity.get("available", 0) > 1000:
                actions.append({
                    "action": "open_additional_gates",
                    "venue_id": venue.provider_id,
                    "gates": 2
                })
            elif venue.utilization > 90:
                actions.append({
                    "action": "restrict_entry",
                    "venue_id": venue.provider_id,
                    "reason": "Overcapacity"
                })
        
        if not actions:
            return None
        
        return {
            "type": "venue_action",
            "priority": "medium",
            "zone_id": zone.zone_id,
            "description": f"Venue capacity management for {zone.name}",
            "actions": actions,
            "required_providers": [a["venue_id"] for a in actions],
            "estimated_impact": "Improve venue flow and safety"
        }
    
    def _check_transport_between_zones(self, source_zone_id: str, target_zone_id: str, event_id: Optional[str] = None) -> bool:
        query = self.db.query(ProviderDB).filter(
            ProviderDB.type == ProviderTypeEnum.TRANSPORT,
            ProviderDB.status.in_([ProviderStatusEnum.ACTIVE, "ACTIVE", "active"])
        )
        if event_id:
            transport_providers = query.filter(ProviderDB.event_id == event_id).all()
        else:
            transport_providers = query.filter(ProviderDB.zone_id.in_([source_zone_id, target_zone_id])).all()
        
        return any(p.capacity.get("available", 0) > 50 for p in transport_providers)
    
    def _get_providers_for_redirect(self, source_zone_id: str, target_zone_id: str, event_id: Optional[str] = None) -> List[str]:
        providers = []
        
        query = self.db.query(ProviderDB).filter(
            ProviderDB.type == ProviderTypeEnum.TRANSPORT,
            ProviderDB.status.in_([ProviderStatusEnum.ACTIVE, "ACTIVE", "active"])
        )
        if event_id:
            transport = query.filter(ProviderDB.event_id == event_id).all()
        else:
            transport = query.filter(ProviderDB.zone_id.in_([source_zone_id, target_zone_id])).all()
            
        providers.extend([p.provider_id for p in transport if p.capacity.get("available", 0) > 0])
        
        venue = self.db.query(ProviderDB).filter(
            ProviderDB.zone_id == target_zone_id,
            ProviderDB.type == ProviderTypeEnum.VENUE,
            ProviderDB.status.in_([ProviderStatusEnum.ACTIVE, "ACTIVE", "active"])
        ).first()
        if venue:
            providers.append(venue.provider_id)
        
        return list(dict.fromkeys(providers))
    
    def create_recommendation_record(self, event_id: str, zone_id: str, recommendation: Dict, trigger_risk_id: Optional[int] = None) -> OrchestrationRecommendationDB:
        rec = OrchestrationRecommendationDB(
            event_id=event_id,
            zone_id=zone_id,
            trigger_risk_id=trigger_risk_id,
            recommendation_type=recommendation["type"],
            description=recommendation["description"],
            actions=recommendation["actions"],
            target_zone_id=recommendation.get("target_zone_id"),
            required_providers=recommendation.get("required_providers", []),
            status="pending"
        )
        
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec
    
    def approve_recommendation(self, recommendation_id: int, approved_by: str) -> OrchestrationRecommendationDB:
        rec = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == recommendation_id
        ).first()
        
        if not rec:
            raise ValueError("Recommendation not found")
        
        if rec.status == "approved":
            raise ValueError("Recommendation already approved")
        if rec.status == "rejected":
            raise ValueError("Cannot approve a rejected recommendation")
        if rec.status == "expired":
            raise ValueError("Cannot approve an expired recommendation")
        
        rec.status = "approved"
        rec.approved_by = approved_by
        rec.approved_at = datetime.utcnow()
        
        providers_to_dispatch = list(rec.required_providers) if rec.required_providers else []
        if not providers_to_dispatch:
            for action in rec.actions:
                if "venue_id" in action and action["venue_id"]:
                    providers_to_dispatch.append(action["venue_id"])
                elif "providers" in action and isinstance(action["providers"], list):
                    providers_to_dispatch.extend(action["providers"])
        
        providers_to_dispatch = list(dict.fromkeys(providers_to_dispatch))
        
        if providers_to_dispatch:
            for provider_id in providers_to_dispatch:
                for action in rec.actions:
                    execution = ActionExecutionDB(
                        recommendation_id=recommendation_id,
                        provider_id=provider_id,
                        action_type=action.get("action", "unknown"),
                        parameters=action,
                        status="dispatched"
                    )
                    self.db.add(execution)
        else:
            for action in rec.actions:
                execution = ActionExecutionDB(
                    recommendation_id=recommendation_id,
                    provider_id=None,
                    action_type=action.get("action", "unknown"),
                    parameters=action,
                    status="dispatched"
                )
                self.db.add(execution)
        
        self.db.commit()
        self.db.refresh(rec)

        # Dispatch staff action alert to Telegram Staff Bot
        try:
            from app.services.telegram.service import TelegramService
            tg_svc = TelegramService(self.db)
            tg_svc.dispatch_staff_action_alert(
                recommendation_id=rec.id,
                description=rec.description,
                target_zone=rec.target_zone_id or rec.zone_id,
                approved_by=approved_by
            )
        except Exception:
            pass

        return rec
    
    def reject_recommendation(self, recommendation_id: int, rejected_by: str, reason: str) -> OrchestrationRecommendationDB:
        rec = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == recommendation_id
        ).first()
        
        if not rec:
            raise ValueError("Recommendation not found")
        
        if rec.status == "rejected":
            raise ValueError("Recommendation already rejected")
        if rec.status == "approved":
            raise ValueError("Cannot reject an approved recommendation")
        if rec.status == "expired":
            raise ValueError("Cannot reject an expired recommendation")
        
        rec.status = "rejected"
        rec.approved_by = rejected_by
        rec.approved_at = datetime.utcnow()
        rec.description += f" | REJECTED: {reason}"
        
        self.db.commit()
        self.db.refresh(rec)
        return rec

    def start_action_execution(self, execution_id: int) -> ActionExecutionDB:
        execution = self.db.query(ActionExecutionDB).filter(ActionExecutionDB.id == execution_id).first()
        if not execution:
            raise ValueError("Action execution not found")
        execution.status = "executing"
        
        rec = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == execution.recommendation_id
        ).first()
        if rec and rec.status == "approved":
            rec.status = "executing"
            
        self.db.commit()
        self.db.refresh(execution)
        return execution
        
    def complete_action_execution(self, execution_id: int, response_data: Optional[Dict] = None) -> ActionExecutionDB:
        execution = self.db.query(ActionExecutionDB).filter(ActionExecutionDB.id == execution_id).first()
        if not execution:
            raise ValueError("Action execution not found")
        execution.status = "executed"
        execution.completed_at = datetime.utcnow()
        execution.response = response_data or {"status": "success"}
        
        rec = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == execution.recommendation_id
        ).first()
        if rec:
            all_execs = self.db.query(ActionExecutionDB).filter(
                ActionExecutionDB.recommendation_id == rec.id
            ).all()
            if all_execs and all(ex.status == "executed" for ex in all_execs):
                rec.status = "executed"
                rec.executed_at = datetime.utcnow()
                
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def fail_action_execution(self, execution_id: int, error_reason: str) -> ActionExecutionDB:
        execution = self.db.query(ActionExecutionDB).filter(ActionExecutionDB.id == execution_id).first()
        if not execution:
            raise ValueError("Action execution not found")
        execution.status = "failed"
        execution.completed_at = datetime.utcnow()
        execution.response = {"status": "failed", "error": error_reason}
        
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def expire_recommendation(self, recommendation_id: int) -> OrchestrationRecommendationDB:
        rec = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == recommendation_id
        ).first()
        if not rec:
            raise ValueError("Recommendation not found")
        if rec.status == "pending":
            rec.status = "expired"
            self.db.commit()
            self.db.refresh(rec)
        return rec