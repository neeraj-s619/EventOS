"""
Phase 3: Forecasting Hardening Tests

Tests edge cases for DemandForecaster:
- normal increasing flow
- decreasing flow
- zero net flow
- high positive net flow
- sudden flow increase
- sudden flow decrease
- already near capacity
- already over capacity
- insufficient historical data
- forecast confidence
- PRE-ACTION vs POST-ACTION forecast separation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.forecasting import DemandForecaster
from app.models.database import (
    EventDB, ZoneDB, ZoneCrowdStateDB
)
from datetime import datetime, timedelta


def create_test_event(db):
    """Create a basic event for testing."""
    event = EventDB(
        name="Forecast Test Event",
        start_date=datetime(2026, 1, 10),
        end_date=datetime(2026, 1, 15),
        expected_visitors=100000,
        operational_thresholds={
            "crowd_warning": 70.0,
            "crowd_critical": 85.0,
        },
        schedule=[]
    )
    db.add(event)
    db.flush()
    return event


def create_zone_with_history(db, event_id, name, capacity, history):
    """Create a zone with specific crowd history."""
    zone = ZoneDB(
        event_id=event_id,
        name=name,
        zone_type="venue",
        capacity=capacity,
        current_crowd=history[-1]["crowd"],
        inflow_per_minute=history[-1]["inflow"],
        outflow_per_minute=history[-1]["outflow"],
        density=history[-1]["crowd"] / capacity,
    )
    db.add(zone)
    db.flush()
    
    # Add crowd states in chronological order
    for i, h in enumerate(history):
        crowd_state = ZoneCrowdStateDB(
            zone_id=zone.zone_id,
            people_count=h["crowd"],
            inflow_per_minute=h["inflow"],
            outflow_per_minute=h["outflow"],
            density=h["crowd"] / capacity,
            movement_direction="N",
            movement_speed=1.0,
            source="test",
            timestamp=datetime.utcnow() - timedelta(minutes=(len(history) - i) * 5)
        )
        db.add(crowd_state)
    
    db.flush()
    return zone


def test_normal_increasing_flow():
    """Test normal increasing flow scenario."""
    print("  Testing normal increasing flow...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        # History showing gradual increase
        history = [
            {"crowd": 50000, "inflow": 100, "outflow": 50},
            {"crowd": 50500, "inflow": 150, "outflow": 50},
            {"crowd": 51100, "inflow": 200, "outflow": 50},
            {"crowd": 51800, "inflow": 250, "outflow": 50},
            {"crowd": 52600, "inflow": 300, "outflow": 50},
        ]
        
        zone = create_zone_with_history(db, event.event_id, "Increasing Flow", 
                                        100000, history)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        
        # Check forecasts show continued increase
        assert len(forecasts) == 3
        assert forecasts[0]["predicted_crowd"] > zone.current_crowd
        assert forecasts[1]["predicted_crowd"] > forecasts[0]["predicted_crowd"]
        assert forecasts[2]["predicted_crowd"] > forecasts[1]["predicted_crowd"]
        
        # Check confidence decreases with horizon
        assert forecasts[0]["confidence"] >= forecasts[1]["confidence"] >= forecasts[2]["confidence"]
        
        print(f"    Current: {zone.current_crowd}, +10min: {forecasts[0]['predicted_crowd']}, "
              f"+20min: {forecasts[1]['predicted_crowd']}, +30min: {forecasts[2]['predicted_crowd']}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_decreasing_flow():
    """Test decreasing flow scenario (outflow > inflow)."""
    print("  Testing decreasing flow...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        history = [
            {"crowd": 80000, "inflow": 100, "outflow": 500},
            {"crowd": 79600, "inflow": 100, "outflow": 500},
            {"crowd": 79200, "inflow": 100, "outflow": 500},
            {"crowd": 78800, "inflow": 100, "outflow": 500},
            {"crowd": 78400, "inflow": 100, "outflow": 500},
        ]
        
        zone = create_zone_with_history(db, event.event_id, "Decreasing Flow", 
                                        100000, history)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        
        # Check forecasts show continued decrease
        assert len(forecasts) == 3
        assert forecasts[0]["predicted_crowd"] < zone.current_crowd
        assert forecasts[1]["predicted_crowd"] < forecasts[0]["predicted_crowd"]
        assert forecasts[2]["predicted_crowd"] < forecasts[1]["predicted_crowd"]
        
        print(f"    Current: {zone.current_crowd}, +10min: {forecasts[0]['predicted_crowd']}, "
              f"+20min: {forecasts[1]['predicted_crowd']}, +30min: {forecasts[2]['predicted_crowd']}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_zero_net_flow():
    """Test zero net flow scenario (inflow == outflow)."""
    print("  Testing zero net flow...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        history = [
            {"crowd": 50000, "inflow": 200, "outflow": 200},
            {"crowd": 50000, "inflow": 200, "outflow": 200},
            {"crowd": 50000, "inflow": 200, "outflow": 200},
            {"crowd": 50000, "inflow": 200, "outflow": 200},
            {"crowd": 50000, "inflow": 200, "outflow": 200},
        ]
        
        zone = create_zone_with_history(db, event.event_id, "Zero Net Flow", 
                                        100000, history)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        
        # Check forecasts show stable crowd
        assert len(forecasts) == 3
        for f in forecasts:
            # Should stay roughly the same (within small margin)
            assert abs(f["predicted_crowd"] - zone.current_crowd) < 100
        
        print(f"    Current: {zone.current_crowd}, +10min: {forecasts[0]['predicted_crowd']}, "
              f"+20min: {forecasts[1]['predicted_crowd']}, +30min: {forecasts[2]['predicted_crowd']}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_high_positive_net_flow():
    """Test high positive net flow scenario."""
    print("  Testing high positive net flow...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        history = [
            {"crowd": 60000, "inflow": 3000, "outflow": 500},
            {"crowd": 63500, "inflow": 3500, "outflow": 500},
            {"crowd": 67000, "inflow": 4000, "outflow": 500},
            {"crowd": 71000, "inflow": 4500, "outflow": 500},
            {"crowd": 75500, "inflow": 5000, "outflow": 500},
        ]
        
        zone = create_zone_with_history(db, event.event_id, "High Positive Flow", 
                                        100000, history)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        ttt = forecaster.calculate_time_to_threshold(zone)
        
        # Check rapid increase predicted
        assert len(forecasts) == 3
        assert forecasts[0]["predicted_crowd"] > zone.current_crowd
        assert ttt is not None and ttt < 30  # Should hit threshold soon
        
        print(f"    Current: {zone.current_crowd}, +10min: {forecasts[0]['predicted_crowd']}, "
              f"+20min: {forecasts[1]['predicted_crowd']}, +30min: {forecasts[2]['predicted_crowd']}")
        print(f"    Time to 85% threshold: {ttt:.1f} min")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_sudden_flow_increase():
    """Test sudden flow increase scenario."""
    print("  Testing sudden flow increase...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        # Normal flow then sudden spike
        history = [
            {"crowd": 50000, "inflow": 200, "outflow": 150},
            {"crowd": 50100, "inflow": 250, "outflow": 150},
            {"crowd": 50200, "inflow": 300, "outflow": 150},
            {"crowd": 52000, "inflow": 2000, "outflow": 150},  # Sudden spike
            {"crowd": 56000, "inflow": 4000, "outflow": 150},  # Sustained high
        ]
        
        zone = create_zone_with_history(db, event.event_id, "Sudden Increase", 
                                        100000, history)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        
        # Forecast should capture the trend
        assert len(forecasts) == 3
        assert forecasts[0]["predicted_crowd"] > zone.current_crowd
        
        # Confidence should be lower for longer horizon
        assert forecasts[0]["confidence"] > forecasts[2]["confidence"]
        
        print(f"    Current: {zone.current_crowd}, +10min: {forecasts[0]['predicted_crowd']}, "
              f"+20min: {forecasts[1]['predicted_crowd']}, +30min: {forecasts[2]['predicted_crowd']}")
        print(f"    Confidences: {forecasts[0]['confidence']:.1f}, {forecasts[1]['confidence']:.1f}, {forecasts[2]['confidence']:.1f}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_sudden_flow_decrease():
    """Test sudden flow decrease scenario."""
    print("  Testing sudden flow decrease...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        history = [
            {"crowd": 80000, "inflow": 4000, "outflow": 500},
            {"crowd": 83500, "inflow": 3500, "outflow": 500},
            {"crowd": 86000, "inflow": 2500, "outflow": 500},
            {"crowd": 87000, "inflow": 500, "outflow": 1500},  # Sudden drop
            {"crowd": 86000, "inflow": 200, "outflow": 1000},  # Continued outflow
        ]
        
        zone = create_zone_with_history(db, event.event_id, "Sudden Decrease", 
                                        100000, history)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        
        # Should predict decrease
        assert len(forecasts) == 3
        assert forecasts[0]["predicted_crowd"] < zone.current_crowd
        
        print(f"    Current: {zone.current_crowd}, +10min: {forecasts[0]['predicted_crowd']}, "
              f"+20min: {forecasts[1]['predicted_crowd']}, +30min: {forecasts[2]['predicted_crowd']}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_already_near_capacity():
    """Test zone already near capacity."""
    print("  Testing already near capacity...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        history = [
            {"crowd": 89000, "inflow": 200, "outflow": 150},
            {"crowd": 89200, "inflow": 300, "outflow": 150},
            {"crowd": 89500, "inflow": 400, "outflow": 150},
            {"crowd": 89800, "inflow": 500, "outflow": 150},
            {"crowd": 90000, "inflow": 500, "outflow": 150},
        ]
        
        zone = create_zone_with_history(db, event.event_id, "Near Capacity", 
                                        100000, history)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        ttt = forecaster.calculate_time_to_threshold(zone)
        
        # Should be near capacity and threshold imminent
        assert zone.utilization >= 90
        assert ttt is not None and ttt <= 10
        
        print(f"    Current: {zone.current_crowd} ({zone.utilization:.1f}%)")
        print(f"    Time to 85% threshold: {ttt:.1f} min")
        print(f"    +10min: {forecasts[0]['predicted_crowd']} ({forecasts[0]['predicted_utilization']:.1f}%)")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_already_over_capacity():
    """Test zone already over capacity."""
    print("  Testing already over capacity...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        history = [
            {"crowd": 105000, "inflow": 500, "outflow": 100},
            {"crowd": 106000, "inflow": 500, "outflow": 100},
            {"crowd": 107000, "inflow": 500, "outflow": 100},
            {"crowd": 108000, "inflow": 500, "outflow": 100},
            {"crowd": 109000, "inflow": 500, "outflow": 100},
        ]
        
        zone = create_zone_with_history(db, event.event_id, "Over Capacity", 
                                        100000, history)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        ttt = forecaster.calculate_time_to_threshold(zone)
        
        # Should be over capacity
        assert zone.utilization > 100
        assert ttt == 0.0  # Already at threshold
        
        print(f"    Current: {zone.current_crowd} ({zone.utilization:.1f}%)")
        print(f"    Time to threshold: {ttt}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_insufficient_historical_data():
    """Test with insufficient historical data (falls back to simple forecast)."""
    print("  Testing insufficient historical data...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        # Create zone with only 1 crowd state (insufficient for trend)
        zone = ZoneDB(
            event_id=event.event_id,
            name="Insufficient History",
            zone_type="venue",
            capacity=100000,
            current_crowd=50000,
            inflow_per_minute=200,
            outflow_per_minute=100,
            density=0.5,
        )
        db.add(zone)
        db.flush()
        
        # Only 1 state
        crowd_state = ZoneCrowdStateDB(
            zone_id=zone.zone_id,
            people_count=50000,
            inflow_per_minute=200,
            outflow_per_minute=100,
            density=0.5,
            movement_direction="N",
            movement_speed=1.0,
            source="test"
        )
        db.add(crowd_state)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        
        # Should fall back to simple forecast
        assert len(forecasts) == 3
        # Simple forecast uses current net flow
        expected_net = zone.inflow_per_minute - zone.outflow_per_minute
        assert forecasts[0]["predicted_crowd"] == zone.current_crowd + expected_net * 10
        
        print(f"    Current: {zone.current_crowd}, net flow: {zone.net_flow}/min")
        print(f"    +10min: {forecasts[0]['predicted_crowd']} (simple forecast)")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_no_crowd_states():
    """Test zone with no crowd states at all."""
    print("  Testing no crowd states...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        # Create zone with NO crowd states
        zone = ZoneDB(
            event_id=event.event_id,
            name="No History",
            zone_type="venue",
            capacity=100000,
            current_crowd=50000,
            inflow_per_minute=200,
            outflow_per_minute=100,
            density=0.5,
        )
        db.add(zone)
        db.commit()
        
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        
        # Should use simple forecast
        assert len(forecasts) == 3
        
        print(f"    Current: {zone.current_crowd}, net flow: {zone.net_flow}/min")
        print(f"    +10min: {forecasts[0]['predicted_crowd']} (simple forecast)")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_forecast_confidence():
    """Test forecast confidence decreases with horizon."""
    print("  Testing forecast confidence...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        history = [
            {"crowd": 50000, "inflow": 200, "outflow": 100},
            {"crowd": 50100, "inflow": 200, "outflow": 100},
            {"crowd": 50200, "inflow": 200, "outflow": 100},
            {"crowd": 50300, "inflow": 200, "outflow": 100},
            {"crowd": 50400, "inflow": 200, "outflow": 100},
        ]
        
        zone = create_zone_with_history(db, event.event_id, "Confidence Test", 
                                        100000, history)
        db.commit()
        
        # Test with 30min horizon (3 intervals of 10min)
        forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        
        assert len(forecasts) == 3
        
        # Check confidence decreases with horizon
        c10, c20, c30 = forecasts[0]["confidence"], forecasts[1]["confidence"], forecasts[2]["confidence"]
        assert c10 > c20 > c30
        assert c10 <= 1.0 and c30 >= 0.3
        
        # Test with 60min horizon (6 intervals of 10min)
        forecasts_long = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=60, interval_minutes=10)
        assert len(forecasts_long) == 6
        assert forecasts_long[0]["confidence"] == c10
        assert forecasts_long[-1]["confidence"] < c30
        
        print(f"    10min: {c10:.1f}, 20min: {c20:.1f}, 30min: {c30:.1f}")
        print(f"    40min: {forecasts_long[3]['confidence']:.1f}, 60min: {forecasts_long[5]['confidence']:.1f}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        return False
    finally:
        db.close()


def test_pre_post_action_separation():
    """Test PRE-ACTION vs POST-ACTION forecast separation."""
    print("  Testing PRE-ACTION vs POST-ACTION forecast separation...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    from app.services.risk import RiskEngine
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # PRE-ACTION: High risk zone
        zone = ZoneDB(
            event_id=event.event_id,
            name="PreAction Zone",
            zone_type="venue",
            capacity=100000,
            current_crowd=90000,
            inflow_per_minute=4000,
            outflow_per_minute=500,
            density=0.9,
        )
        db.add(zone)
        db.flush()
        
        # Add pre-action history
        for i in range(5):
            crowd_state = ZoneCrowdStateDB(
                zone_id=zone.zone_id,
                people_count=85000 + i * 1000,
                inflow_per_minute=4000,
                outflow_per_minute=500,
                density=0.85 + i * 0.01,
                movement_direction="N",
                movement_speed=1.0,
                source="pre_action_cctv",
                timestamp=datetime.utcnow() - timedelta(minutes=(5-i) * 5)
            )
            db.add(crowd_state)
        db.commit()
        
        # PRE-ACTION forecast
        pre_forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        pre_risk = risk_engine.assess_zone_risk(zone.zone_id)
        
        print(f"    PRE-ACTION: crowd={zone.current_crowd}, util={zone.utilization:.1f}%")
        print(f"    PRE-ACTION risk: {pre_risk['current_risk']}, predicted: {pre_risk['predicted_risk']}")
        print(f"    PRE-ACTION +10min: {pre_forecasts[0]['predicted_crowd']} ({pre_forecasts[0]['predicted_utilization']:.1f}%)")
        
        # SIMULATE ACTION: Reduce inflow, increase outflow
        zone.inflow_per_minute = 800
        zone.outflow_per_minute = 1200
        zone.current_crowd = 89000
        zone.updated_at = datetime.utcnow()
        db.commit()
        
        # Add post-action observation
        post_state = ZoneCrowdStateDB(
            zone_id=zone.zone_id,
            people_count=89000,
            inflow_per_minute=800,
            outflow_per_minute=1200,
            density=0.89,
            movement_direction="S",
            movement_speed=1.5,
            source="post_action_cctv"
        )
        db.add(post_state)
        db.commit()
        
        # POST-ACTION forecast
        post_forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
        post_risk = risk_engine.assess_zone_risk(zone.zone_id)
        
        print(f"    POST-ACTION: crowd={zone.current_crowd}, inflow={zone.inflow_per_minute}, outflow={zone.outflow_per_minute}")
        print(f"    POST-ACTION risk: {post_risk['current_risk']}, predicted: {post_risk['predicted_risk']}")
        print(f"    POST-ACTION +10min: {post_forecasts[0]['predicted_crowd']} ({post_forecasts[0]['predicted_utilization']:.1f}%)")
        
        # Verify separation - pre and post forecasts should be different
        pre_util_10 = pre_forecasts[0]['predicted_utilization']
        post_util_10 = post_forecasts[0]['predicted_utilization']
        
        # Post action should show lower predicted utilization
        assert post_util_10 < pre_util_10, "Post-action forecast should show improvement"
        
        print(f"    PRE +10min util: {pre_util_10:.1f}%, POST +10min util: {post_util_10:.1f}%")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_time_to_threshold():
    """Test time_to_threshold calculation."""
    print("  Testing time_to_threshold...")
    
    init_db()
    db = next(get_db())
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        
        test_cases = [
            # (crowd, capacity, inflow, outflow, expected_ttt_range)
            (80000, 100000, 1000, 200, (5, 10)),       # 80% util, net +800, need 5000 more = 6.25 min
            (82000, 100000, 500, 100, (5, 10)),        # 82% util, net +400, need 3000 more = 7.5 min
            (84999, 100000, 1000, 1000, None),         # 84.999% util, net 0, no TTT (just under 85%)
            (70000, 100000, -100, 200, None),           # 70% util, negative net flow, no TTT
            (100000, 100000, 500, 100, 0),              # 100% util, at threshold
        ]
        
        for i, (crowd, cap, inflow, outflow, expected_range) in enumerate(test_cases):
            zone = ZoneDB(
                event_id=event.event_id,
                name=f"TTT Test {i}",
                zone_type="venue",
                capacity=cap,
                current_crowd=crowd,
                inflow_per_minute=inflow,
                outflow_per_minute=outflow,
                density=crowd / cap,
            )
            db.add(zone)
            db.commit()
            
            ttt = forecaster.calculate_time_to_threshold(zone)
            
            if expected_range is None:
                assert ttt is None, f"Expected None, got {ttt}"
            elif expected_range == 0:
                assert ttt == 0.0, f"Expected 0, got {ttt}"
            else:
                assert ttt is not None, f"Expected TTT in range {expected_range}, got None"
                assert expected_range[0] <= ttt <= expected_range[1], \
                    f"Expected TTT in {expected_range}, got {ttt}"
            
            print(f"    Crowd: {crowd}, Net flow: {inflow-outflow}/min, TTT: {ttt}")
            db.delete(zone)
            db.commit()
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    results = []
    results.append(("Normal Increasing Flow", test_normal_increasing_flow()))
    results.append(("Decreasing Flow", test_decreasing_flow()))
    results.append(("Zero Net Flow", test_zero_net_flow()))
    results.append(("High Positive Net Flow", test_high_positive_net_flow()))
    results.append(("Sudden Flow Increase", test_sudden_flow_increase()))
    results.append(("Sudden Flow Decrease", test_sudden_flow_decrease()))
    results.append(("Already Near Capacity", test_already_near_capacity()))
    results.append(("Already Over Capacity", test_already_over_capacity()))
    results.append(("Insufficient Historical Data", test_insufficient_historical_data()))
    results.append(("No Crowd States", test_no_crowd_states()))
    results.append(("Forecast Confidence", test_forecast_confidence()))
    results.append(("PRE vs POST Action Separation", test_pre_post_action_separation()))
    results.append(("Time to Threshold", test_time_to_threshold()))
    
    print("\n" + "=" * 60)
    print("PHASE 3 SUMMARY")
    print("=" * 60)
    for name, passed in results:
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    sys.exit(0 if all_passed else 1)