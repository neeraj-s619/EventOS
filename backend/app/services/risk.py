from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.database import ZoneDB, RiskAssessmentDB, RiskLevelEnum, ForecastDB, EventDB
from app.services.forecasting import DemandForecaster
from app.core.config import settings


class RiskEngine:
    def __init__(self, db: Session):
        self.db = db
        self.forecaster = DemandForecaster(db)
        self.thresholds = settings.risk_thresholds
    
    def assess_zone_risk(self, zone_id: str) -> Dict:
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
        if not zone:
            raise ValueError("Zone not found")
        
        current_risk = self._calculate_current_risk(zone)
        predicted_risk = self._calculate_predicted_risk(zone)
        time_to_threshold = self.forecaster.calculate_time_to_threshold(zone)
        
        factors = {
            "current_utilization": zone.utilization,
            "inflow_per_minute": zone.inflow_per_minute,
            "outflow_per_minute": zone.outflow_per_minute,
            "net_flow": zone.net_flow,
            "density": zone.density,
            "capacity": zone.capacity,
            "time_to_threshold_minutes": time_to_threshold
        }
        
        risk_assessment = RiskAssessmentDB(
            event_id=zone.event_id,
            zone_id=zone_id,
            current_risk=current_risk,
            predicted_risk=predicted_risk,
            current_utilization=zone.utilization,
            predicted_utilization=self._get_predicted_utilization(zone),
            time_to_threshold=time_to_threshold,
            factors=factors
        )
        
        self.db.add(risk_assessment)
        
        zone.risk_level = current_risk
        zone.time_to_threshold = time_to_threshold
        zone.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(risk_assessment)
        
        return {
            "zone_id": zone_id,
            "current_risk": current_risk.value,
            "predicted_risk": predicted_risk.value,
            "current_utilization": zone.utilization,
            "predicted_utilization": self._get_predicted_utilization(zone),
            "time_to_threshold_minutes": time_to_threshold,
            "factors": factors,
            "assessment_id": risk_assessment.id
        }
    
    def _calculate_current_risk(self, zone: ZoneDB) -> RiskLevelEnum:
        utilization = zone.utilization
        
        if utilization >= self.thresholds["critical_max"]:
            return RiskLevelEnum.OVERLOAD
        elif utilization >= self.thresholds["warning_max"]:
            return RiskLevelEnum.CRITICAL
        elif utilization >= self.thresholds["watch_max"]:
            return RiskLevelEnum.WARNING
        elif utilization >= self.thresholds["normal_max"]:
            return RiskLevelEnum.WATCH
        else:
            return RiskLevelEnum.NORMAL
    
    def _calculate_predicted_risk(self, zone: ZoneDB) -> RiskLevelEnum:
        predicted_util = self._get_predicted_utilization(zone)
        
        if predicted_util >= self.thresholds["critical_max"]:
            return RiskLevelEnum.OVERLOAD
        elif predicted_util >= self.thresholds["warning_max"]:
            return RiskLevelEnum.CRITICAL
        elif predicted_util >= self.thresholds["watch_max"]:
            return RiskLevelEnum.WARNING
        elif predicted_util >= self.thresholds["normal_max"]:
            return RiskLevelEnum.WATCH
        else:
            return RiskLevelEnum.NORMAL
    
    def _get_predicted_utilization(self, zone: ZoneDB) -> float:
        forecasts = self.forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        if not forecasts:
            return zone.utilization
        
        max_predicted_util = max(f["predicted_utilization"] for f in forecasts)
        return max_predicted_util
    
    def assess_event_risk(self, event_id: str) -> List[Dict]:
        zones = self.db.query(ZoneDB).filter(ZoneDB.event_id == event_id).all()
        results = []
        
        for zone in zones:
            try:
                risk = self.assess_zone_risk(zone.zone_id)
                results.append(risk)
            except Exception as e:
                results.append({"zone_id": zone.zone_id, "error": str(e)})
        
        return results
    
    def get_risk_summary(self, event_id: str) -> Dict:
        zones = self.db.query(ZoneDB).filter(ZoneDB.event_id == event_id).all()
        
        risk_counts = {level.value: 0 for level in RiskLevelEnum}
        critical_zones = []
        
        for zone in zones:
            risk_counts[zone.risk_level.value] += 1
            if zone.risk_level in [RiskLevelEnum.WARNING, RiskLevelEnum.CRITICAL, RiskLevelEnum.OVERLOAD]:
                critical_zones.append({
                    "zone_id": zone.zone_id,
                    "name": zone.name,
                    "risk_level": zone.risk_level.value,
                    "utilization": zone.utilization,
                    "time_to_threshold": zone.time_to_threshold
                })
        
        overall_risk = RiskLevelEnum.NORMAL
        if risk_counts["overload"] > 0:
            overall_risk = RiskLevelEnum.OVERLOAD
        elif risk_counts["critical"] > 0:
            overall_risk = RiskLevelEnum.CRITICAL
        elif risk_counts["warning"] > 0:
            overall_risk = RiskLevelEnum.WARNING
        elif risk_counts["watch"] > 0:
            overall_risk = RiskLevelEnum.WATCH
        
        # Calculate predicted horizon risk and minimum time to breach
        predicted_counts = {level.value: 0 for level in RiskLevelEnum}
        min_ttt = None
        for zone in zones:
            pred_risk = self._calculate_predicted_risk(zone)
            predicted_counts[pred_risk.value] += 1
            if zone.time_to_threshold is not None and zone.time_to_threshold > 0:
                if min_ttt is None or zone.time_to_threshold < min_ttt:
                    min_ttt = zone.time_to_threshold
        
        predicted_overall_risk = RiskLevelEnum.NORMAL
        if predicted_counts["overload"] > 0:
            predicted_overall_risk = RiskLevelEnum.OVERLOAD
        elif predicted_counts["critical"] > 0:
            predicted_overall_risk = RiskLevelEnum.CRITICAL
        elif predicted_counts["warning"] > 0:
            predicted_overall_risk = RiskLevelEnum.WARNING
        elif predicted_counts["watch"] > 0:
            predicted_overall_risk = RiskLevelEnum.WATCH

        risk_order = {RiskLevelEnum.NORMAL: 1, RiskLevelEnum.WATCH: 2, RiskLevelEnum.WARNING: 3, RiskLevelEnum.CRITICAL: 4, RiskLevelEnum.OVERLOAD: 5}
        is_escalating = risk_order.get(predicted_overall_risk, 1) > risk_order.get(overall_risk, 1)

        return {
            "event_id": event_id,
            "overall_risk": overall_risk.value,
            "predicted_overall_risk": predicted_overall_risk.value,
            "forecast_escalation": is_escalating,
            "min_time_to_threshold": min_ttt,
            "risk_distribution": risk_counts,
            "critical_zones": critical_zones,
            "total_zones": len(zones)
        }