from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import statistics

from app.models.database import ZoneDB, ZoneCrowdStateDB, ForecastDB, EventDB


class DemandForecaster:
    def __init__(self, db: Session):
        self.db = db
    
    def forecast_zone_demand(self, zone_id: str, horizon_minutes: int = 30, interval_minutes: int = 10) -> List[Dict]:
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
        if not zone:
            raise ValueError("Zone not found")
        
        recent_states = self.db.query(ZoneCrowdStateDB).filter(
            ZoneCrowdStateDB.zone_id == zone_id
        ).order_by(ZoneCrowdStateDB.timestamp.desc()).limit(10).all()
        
        if not recent_states:
            return self._simple_forecast(zone, horizon_minutes, interval_minutes)
        
        return self._trend_forecast(zone, recent_states, horizon_minutes, interval_minutes)
    
    def _simple_forecast(self, zone: ZoneDB, horizon_minutes: int, interval_minutes: int) -> List[Dict]:
        forecasts = []
        current_crowd = zone.current_crowd
        net_flow = zone.net_flow
        
        for i in range(1, (horizon_minutes // interval_minutes) + 1):
            minutes_ahead = i * interval_minutes
            predicted_crowd = current_crowd + (net_flow * minutes_ahead)
            predicted_crowd = max(0, predicted_crowd)
            
            predicted_utilization = (predicted_crowd / zone.capacity * 100) if zone.capacity > 0 else 0
            
            # Uncertainty propagates wider over time horizon
            uncertainty = int(predicted_crowd * (0.04 + (i * 0.02)))
            
            forecasts.append({
                "horizon_minutes": minutes_ahead,
                "timestamp": datetime.utcnow() + timedelta(minutes=minutes_ahead),
                "predicted_crowd": int(predicted_crowd),
                "predicted_inflow": zone.inflow_per_minute,
                "predicted_outflow": zone.outflow_per_minute,
                "predicted_utilization": predicted_utilization,
                "confidence": 0.6,
                "uncertainty_bound": uncertainty,
                "ci_lower": max(0, int(predicted_crowd - uncertainty)),
                "ci_upper": int(predicted_crowd + uncertainty),
                "model_name": "Flow-Based Linear Extrapolation"
            })
        
        return forecasts
    
    def _trend_forecast(self, zone: ZoneDB, recent_states: List[ZoneCrowdStateDB], horizon_minutes: int, interval_minutes: int) -> List[Dict]:
        if len(recent_states) < 2:
            return self._simple_forecast(zone, horizon_minutes, interval_minutes)
        
        recent_states.reverse()
        
        inflow_values = [s.inflow_per_minute for s in recent_states]
        outflow_values = [s.outflow_per_minute for s in recent_states]
        crowd_values = [s.people_count for s in recent_states]
        
        inflow_trend = self._calculate_trend(inflow_values)
        outflow_trend = self._calculate_trend(outflow_values)
        crowd_trend = self._calculate_trend(crowd_values)
        
        avg_inflow = statistics.mean(inflow_values)
        avg_outflow = statistics.mean(outflow_values)
        current_crowd = crowd_values[-1]
        
        forecasts = []
        for i in range(1, (horizon_minutes // interval_minutes) + 1):
            minutes_ahead = i * interval_minutes
            
            predicted_inflow = avg_inflow + (inflow_trend * minutes_ahead)
            predicted_outflow = avg_outflow + (outflow_trend * minutes_ahead)
            predicted_net_flow = predicted_inflow - predicted_outflow
            
            predicted_crowd = current_crowd + (predicted_net_flow * minutes_ahead)
            predicted_crowd = max(0, predicted_crowd)
            
            predicted_utilization = (predicted_crowd / zone.capacity * 100) if zone.capacity > 0 else 0
            
            confidence = max(0.3, 0.9 - (i * 0.1))
            uncertainty = int(predicted_crowd * (0.03 + (i * 0.025)))
            
            forecasts.append({
                "horizon_minutes": minutes_ahead,
                "timestamp": datetime.utcnow() + timedelta(minutes=minutes_ahead),
                "predicted_crowd": int(predicted_crowd),
                "predicted_inflow": max(0, predicted_inflow),
                "predicted_outflow": max(0, predicted_outflow),
                "predicted_utilization": predicted_utilization,
                "confidence": confidence,
                "uncertainty_bound": uncertainty,
                "ci_lower": max(0, int(predicted_crowd - uncertainty)),
                "ci_upper": int(predicted_crowd + uncertainty),
                "model_name": "Momentum & Dynamic Flow Projection"
            })
        
        return forecasts
    
    def _calculate_trend(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        y = values
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def calculate_time_to_threshold(self, zone: ZoneDB, threshold_utilization: float = 85.0) -> Optional[float]:
        if zone.capacity == 0:
            return None
        
        current_utilization = zone.utilization
        if current_utilization >= threshold_utilization:
            return 0.0
        
        net_flow = zone.net_flow
        if net_flow <= 0:
            return None
        
        threshold_crowd = zone.capacity * (threshold_utilization / 100)
        people_needed = threshold_crowd - zone.current_crowd
        
        if people_needed <= 0:
            return 0.0
        
        return people_needed / net_flow
    
    def save_forecasts(self, event_id: str, zone_id: str, forecasts: List[Dict]) -> List[ForecastDB]:
        saved = []
        for f in forecasts:
            forecast = ForecastDB(
                event_id=event_id,
                zone_id=zone_id,
                horizon_minutes=f["horizon_minutes"],
                predicted_crowd=f["predicted_crowd"],
                predicted_inflow=f["predicted_inflow"],
                predicted_outflow=f["predicted_outflow"],
                predicted_utilization=f["predicted_utilization"],
                confidence=f["confidence"]
            )
            self.db.add(forecast)
            saved.append(forecast)
        
        self.db.commit()
        return saved