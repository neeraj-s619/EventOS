"""
Phase 2: Risk Engine Complete Coverage Tests

Tests all 5 risk levels (NORMAL, WATCH, WARNING, CRITICAL, OVERLOAD)
Tests risk recovery transitions
Tests multi-zone with different risk levels
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.risk import RiskEngine
from app.services.forecasting import DemandForecaster
from app.models.database import (
    EventDB, ZoneDB, ZoneCrowdStateDB, ProviderDB, ProviderTypeEnum,
    RiskLevelEnum
)
from datetime import datetime


def create_test_event(db):
    """Create a basic event for testing."""
    event = EventDB(
        name="Risk Test Event",
        start_date=datetime(2026, 1, 10),
        end_date=datetime(2026, 1, 15),
        expected_visitors=100000,
        operational_thresholds={
            "crowd_warning": 70.0,
            "crowd_critical": 85.0,
            "movement_warning": 80.0,
            "movement_critical": 95.0
        },
        schedule=[]
    )
    db.add(event)
    db.flush()
    return event


def create_zone(db, event_id, name, zone_type, capacity, crowd, inflow, outflow, providers=None):
    """Create a zone with specific crowd state."""
    zone = ZoneDB(
        event_id=event_id,
        name=name,
        zone_type=zone_type,
        capacity=capacity,
        current_crowd=crowd,
        inflow_per_minute=inflow,
        outflow_per_minute=outflow,
        density=crowd / capacity if capacity > 0 else 0,
    )
    db.add(zone)
    db.flush()
    
    # Add crowd state
    crowd_state = ZoneCrowdStateDB(
        zone_id=zone.zone_id,
        people_count=crowd,
        inflow_per_minute=inflow,
        outflow_per_minute=outflow,
        density=crowd / capacity if capacity > 0 else 0,
        movement_direction="N",
        movement_speed=1.0,
        source="test"
    )
    db.add(crowd_state)
    db.flush()
    
    if providers:
        for p in providers:
            p.zone_id = zone.zone_id
            p.event_id = event_id
            db.add(p)
    
    return zone


def test_risk_levels():
    """Test all 5 risk levels with deterministic scenarios."""
    print("=" * 60)
    print("PHASE 2: RISK ENGINE - ALL 5 LEVELS")
    print("=" * 60)
    
    init_db()
    db = next(get_db())
    risk_engine = RiskEngine(db)
    forecaster = DemandForecaster(db)
    
    try:
        event = create_test_event(db)
        print(f"\nEvent: {event.event_id}")
        
        # Define test cases: (name, capacity, crowd, inflow, outflow, expected_current, expected_predicted)
        test_cases = [
            # NORMAL: < 70% utilization
            ("NORMAL - Low crowd", 100000, 50000, 100, 150, "normal", "normal"),
            
            # WATCH: 70-85% utilization
            ("WATCH - 75% util", 100000, 75000, 100, 150, "watch", "watch"),
            
            # WARNING: 85-95% utilization
            ("WARNING - 90% util", 100000, 90000, 2000, 500, "warning", "overload"),
            
            # CRITICAL: 95-100% utilization
            ("CRITICAL - 98% util", 100000, 98000, 3000, 500, "critical", "overload"),
            
            # OVERLOAD: > 100% utilization
            ("OVERLOAD - 110% util", 100000, 110000, 4000, 500, "overload", "overload"),
        ]
        
        results = []
        for name, cap, crowd, inflow, outflow, exp_current, exp_predicted in test_cases:
            zone = create_zone(db, event.event_id, name, "venue", cap, crowd, inflow, outflow)
            db.refresh(zone)
            
            # Run risk assessment
            risk = risk_engine.assess_zone_risk(zone.zone_id)
            
            passed = (risk['current_risk'] == exp_current and 
                     risk['predicted_risk'] == exp_predicted)
            status = "PASS" if passed else "FAIL"
            
            print(f"\n  {name}:")
            print(f"    Crowd: {crowd:,}/{cap:,} ({risk['current_utilization']:.1f}%)")
            print(f"    Inflow: {inflow}/min, Outflow: {outflow}/min, Net: {risk['factors']['net_flow']:.0f}/min")
            print(f"    Current: {risk['current_risk']} (expected: {exp_current})")
            print(f"    Predicted: {risk['predicted_risk']} (expected: {exp_predicted})")
            print(f"    Status: {status}")
            
            results.append({
                "name": name,
                "passed": passed,
                "current": risk['current_risk'],
                "predicted": risk['predicted_risk'],
                "expected_current": exp_current,
                "expected_predicted": exp_predicted
            })
        
        # Summary
        passed_count = sum(1 for r in results if r['passed'])
        print(f"\n{'='*60}")
        print(f"RISK LEVELS: {passed_count}/{len(results)} PASSED")
        print(f"{'='*60}")
        
        return passed_count == len(results)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_risk_recovery():
    """Test risk recovery transitions."""
    print("\n" + "=" * 60)
    print("PHASE 2: RISK RECOVERY TRANSITIONS")
    print("=" * 60)
    
    init_db()
    db = next(get_db())
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Start with WARNING level
        zone = create_zone(db, event.event_id, "Recovery Zone", "venue", 
                          100000, 90000, 2000, 500)
        db.refresh(zone)
        
        risk_before = risk_engine.assess_zone_risk(zone.zone_id)
        print(f"\nInitial state: {risk_before['current_risk']} (util={risk_before['current_utilization']:.1f}%)")
        assert risk_before['current_risk'] in ['warning', 'critical', 'overload']
        
        # Simulate intervention: reduce inflow, increase outflow
        zone.inflow_per_minute = 200
        zone.outflow_per_minute = 800
        zone.current_crowd = 85000
        zone.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(zone)
        
        # Add new crowd state
        crowd_state = ZoneCrowdStateDB(
            zone_id=zone.zone_id,
            people_count=85000,
            inflow_per_minute=200,
            outflow_per_minute=800,
            density=0.85,
            movement_direction="S",
            movement_speed=1.5,
            source="test_recovery"
        )
        db.add(crowd_state)
        db.commit()
        
        risk_after = risk_engine.assess_zone_risk(zone.zone_id)
        print(f"After intervention: {risk_after['current_risk']} (util={risk_after['current_utilization']:.1f}%)")
        
        # Check improvement
        risk_levels = {'normal': 0, 'watch': 1, 'warning': 2, 'critical': 3, 'overload': 4}
        improved = risk_levels[risk_after['current_risk']] <= risk_levels[risk_before['current_risk']]
        
        print(f"Risk improved or maintained: {improved}")
        print(f"Status: {'PASS' if improved else 'FAIL'}")
        
        # Test further recovery to NORMAL
        zone.inflow_per_minute = 50
        zone.outflow_per_minute = 100
        zone.current_crowd = 60000
        zone.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(zone)
        
        crowd_state2 = ZoneCrowdStateDB(
            zone_id=zone.zone_id,
            people_count=60000,
            inflow_per_minute=50,
            outflow_per_minute=100,
            density=0.6,
            movement_direction="S",
            movement_speed=2.0,
            source="test_recovery2"
        )
        db.add(crowd_state2)
        db.commit()
        
        risk_normal = risk_engine.assess_zone_risk(zone.zone_id)
        print(f"Further recovery: {risk_normal['current_risk']} (util={risk_normal['current_utilization']:.1f}%)")
        
        fully_recovered = risk_normal['current_risk'] == 'normal'
        print(f"Fully recovered to NORMAL: {fully_recovered}")
        print(f"Status: {'PASS' if fully_recovered else 'FAIL'}")
        
        return improved and fully_recovered
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_multi_zone_different_risks():
    """Test multiple zones with different risk levels simultaneously."""
    print("\n" + "=" * 60)
    print("PHASE 2: MULTI-ZONE DIFFERENT RISK LEVELS")
    print("=" * 60)
    
    init_db()
    db = next(get_db())
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: CRITICAL
        zone_a = create_zone(db, event.event_id, "Zone A Critical", "venue",
                            50000, 48000, 3000, 500)
        
        # Zone B: WARNING  
        zone_b = create_zone(db, event.event_id, "Zone B Warning", "hospitality",
                            30000, 27000, 1000, 200)
        
        # Zone C: NORMAL
        zone_c = create_zone(db, event.event_id, "Zone C Normal", "transport",
                            20000, 5000, 100, 150)
        
        # Zone D: WATCH
        zone_d = create_zone(db, event.event_id, "Zone D Watch", "mixed",
                            25000, 19000, 200, 150)
        
        db.commit()
        
        # Assess all
        zones = [zone_a, zone_b, zone_c, zone_d]
        expected_risks = ['critical', 'warning', 'normal', 'watch']
        actual_risks = []
        
        for zone, expected in zip(zones, expected_risks):
            db.refresh(zone)
            risk = risk_engine.assess_zone_risk(zone.zone_id)
            actual_risks.append(risk['current_risk'])
            print(f"\n  {zone.name}: {risk['current_risk']} (expected: {expected}) "
                  f"util={risk['current_utilization']:.1f}%")
        
        # Get summary
        summary = risk_engine.get_risk_summary(event.event_id)
        print(f"\nEvent summary:")
        print(f"  Overall: {summary['overall_risk']}")
        print(f"  Distribution: {summary['risk_distribution']}")
        print(f"  Critical zones: {len(summary['critical_zones'])}")
        
        all_match = all(a == e for a, e in zip(actual_risks, expected_risks))
        print(f"\nAll zones match expected: {all_match}")
        print(f"Status: {'PASS' if all_match else 'FAIL'}")
        
        return all_match
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_one_critical_others_normal():
    """Test one critical zone while others remain normal."""
    print("\n" + "=" * 60)
    print("PHASE 2: ONE CRITICAL, OTHERS NORMAL")
    print("=" * 60)
    
    init_db()
    db = next(get_db())
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: CRITICAL (high utilization, high inflow)
        zone_a = create_zone(db, event.event_id, "Zone A Critical", "venue",
                            50000, 49000, 4000, 500)
        
        # Zone B: NORMAL
        zone_b = create_zone(db, event.event_id, "Zone B Normal", "hospitality",
                            30000, 10000, 100, 150)
        
        # Zone C: NORMAL  
        zone_c = create_zone(db, event.event_id, "Zone C Normal", "transport",
                            20000, 3000, 50, 80)
        
        db.commit()
        
        # Assess risk for all zones in the event
        risk_engine.assess_event_risk(event.event_id)
        
        summary = risk_engine.get_risk_summary(event.event_id)
        
        print(f"Overall risk: {summary['overall_risk']}")
        print(f"Critical zones count: {len(summary['critical_zones'])}")
        print(f"Risk distribution: {summary['risk_distribution']}")
        
        # Should have exactly 1 critical zone
        one_critical = (len(summary['critical_zones']) == 1 and 
                       summary['critical_zones'][0]['zone_id'] == zone_a.zone_id)
        
        print(f"\nExactly one critical zone (Zone A): {one_critical}")
        print(f"Status: {'PASS' if one_critical else 'FAIL'}")
        
        return one_critical
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


import unittest


class TestRiskEngineSuite(unittest.TestCase):
    def test_risk_levels(self):
        self.assertTrue(test_risk_levels())

    def test_risk_recovery(self):
        self.assertTrue(test_risk_recovery())

    def test_multi_zone_different_risks(self):
        self.assertTrue(test_multi_zone_different_risks())

    def test_one_critical_others_normal(self):
        self.assertTrue(test_one_critical_others_normal())


if __name__ == "__main__":
    results = []
    results.append(("Risk Levels", test_risk_levels()))
    results.append(("Risk Recovery", test_risk_recovery()))
    results.append(("Multi-Zone Risks", test_multi_zone_different_risks()))
    results.append(("One Critical Others Normal", test_one_critical_others_normal()))
    
    print("\n" + "=" * 60)
    print("PHASE 2 SUMMARY")
    print("=" * 60)
    for name, passed in results:
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    sys.exit(0 if all_passed else 1)