"""
EVENTOS Automated Test Suite Runner
Runs all unit and integration test suites and generates a comprehensive coverage report.
"""

import sys
import os
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db

TEST_MODULES = [
    "tests.test_pipeline",
    "tests.test_risk_engine",
    "tests.test_forecasting",
    "tests.test_orchestration",
    "tests.test_approval_and_execution",
    "tests.test_feedback_loop",
    "tests.test_provider_network",
    "tests.test_crowd_data_hardening",
    "tests.test_multi_zone",
    "tests.test_unified_state",
    "tests.test_whatsapp_webhook",
    "tests.test_whatsapp_meta_cloud",
    "tests.test_api_hardening",
    "tests.test_database_integrity",
    "tests.test_integration_adapters",
    "tests.test_mumbai_data_foundation",
    "tests.test_weather_digital_twin",
    "tests.test_whatsapp_operational_telemetry",
    "tests.test_cctv_cv_engine",
    "tests.test_telegram_provider_pulse",
]


def run_all_suites():
    print("=" * 80)
    print(" EVENTOS COMPLETE BACKEND TEST SUITE RUNNER")
    print("=" * 80)
    init_db()

    total_tests = 0
    total_failures = 0
    total_errors = 0
    results_summary = []

    start_time = time.time()

    loader = unittest.TestLoader()

    for module_name in TEST_MODULES:
        print(f"\n>> Running: {module_name} ...", flush=True)
        try:
            suite = loader.loadTestsFromName(module_name)
            runner = unittest.TextTestRunner(verbosity=1)
            result = runner.run(suite)

            tests_run = result.testsRun
            fails = len(result.failures)
            errs = len(result.errors)

            total_tests += tests_run
            total_failures += fails
            total_errors += errs

            status = "PASS" if (fails == 0 and errs == 0) else "FAIL"
            results_summary.append({
                "module": module_name,
                "tests": tests_run,
                "failures": fails,
                "errors": errs,
                "status": status
            })
        except Exception as e:
            print(f"FAILED TO LOAD/RUN {module_name}: {e}")
            total_errors += 1
            results_summary.append({
                "module": module_name,
                "tests": 0,
                "failures": 0,
                "errors": 1,
                "status": "LOAD_ERROR"
            })

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print(" TEST SUITE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"{'Module Name':<38} | {'Tests':<6} | {'Failures':<8} | {'Errors':<6} | {'Status':<6}")
    print("-" * 80)

    for r in results_summary:
        print(f"{r['module']:<38} | {r['tests']:<6} | {r['failures']:<8} | {r['errors']:<6} | {r['status']:<6}")

    print("=" * 80)
    print(f"Total Tests Run: {total_tests}")
    print(f"Total Failures:  {total_failures}")
    print(f"Total Errors:    {total_errors}")
    print(f"Elapsed Time:    {elapsed:.2f}s")
    print("=" * 80)

    if total_failures == 0 and total_errors == 0:
        print("\nALL TEST SUITES PASSED CLEANLY (100% SUCCESS)\n")
        return 0
    else:
        print(f"\nTEST SUITE COMPLETED WITH FAILURES ({total_failures} failures, {total_errors} errors)\n")
        return 1


if __name__ == "__main__":
    exit_code = run_all_suites()
    sys.exit(exit_code)
