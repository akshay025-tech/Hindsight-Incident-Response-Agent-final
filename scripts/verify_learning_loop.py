"""End-to-end verification script for Hindsight learning loop."""
import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.database import create_tables, SessionLocal, IncidentDB, ApprovalDB, PostmortemDB
from app.agents.incident_agent import get_incident_agent
from app.services.postmortem_service import get_postmortem_service
from app.services.hindsight_service import get_hindsight_service
from app.models.incident import Severity, IncidentStatus


async def run_verification():
    create_tables()
    db = SessionLocal()
    agent = get_incident_agent()
    pm_service = get_postmortem_service()
    hindsight = get_hindsight_service()

    # Clear previous test data for clean slate
    db.query(ApprovalDB).filter(ApprovalDB.incident_id.in_(["IR-001", "IR-002"])).delete(synchronize_session=False)
    db.query(PostmortemDB).filter(PostmortemDB.incident_id.in_(["IR-001", "IR-002"])).delete(synchronize_session=False)
    db.query(IncidentDB).filter(IncidentDB.id.in_(["IR-001", "IR-002"])).delete(synchronize_session=False)
    db.commit()

    passed = {}

    try:
        # 1. Create Incident A
        inc_a = IncidentDB(
            id="IR-001",
            title="High CPU & Memory Degradation",
            service="api-gateway",
            severity=Severity.HIGH.value,
            status=IncidentStatus.OPEN.value,
            description="API Gateway experiencing memory leak following v2.14.0 deployment.",
            symptoms=["CPU continuously increasing", "memory increasing", "recent deployment"],
            metrics={"cpu_percent": 94, "memory_percent": 88},
            logs=["WARN [WorkerPool] thread starvation", "WARN [GC] Full GC 1400ms"],
            deployment={"recent": True, "version": "v2.14.0"},
        )
        db.add(inc_a)
        db.commit()
        passed["Incident A"] = inc_a.id == "IR-001"

        # 2. Analyze Incident A
        inc_a_dict = {
            "id": inc_a.id,
            "title": inc_a.title,
            "service": inc_a.service,
            "severity": inc_a.severity,
            "description": inc_a.description,
            "symptoms": inc_a.symptoms,
            "metrics": inc_a.metrics,
            "logs": inc_a.logs,
            "deployment": inc_a.deployment,
        }
        res_a = await agent.analyze_incident(inc_a_dict)
        inc_a.analysis_result = res_a.model_dump()
        inc_a.status = IncidentStatus.MITIGATED.value
        inc_a.resolution_summary = "Rollback deployment + restart service"
        db.commit()

        # 3. Generate Postmortem A & Retain in Hindsight
        pm_a = await pm_service.generate_postmortem(
            db=db,
            incident_id="IR-001",
            operator_feedback="Resolved swiftly after rolling back bad build.",
        )
        passed["Postmortem A"] = pm_a is not None and "IR-001" in pm_a.incident_id
        passed["Hindsight Retain"] = pm_a.retained_in_hindsight is True

        # 4. Create Incident B (similar symptoms, slightly different metrics)
        inc_b = IncidentDB(
            id="IR-002",
            title="High CPU & Memory Exhaustion",
            service="api-gateway",
            severity=Severity.HIGH.value,
            status=IncidentStatus.OPEN.value,
            description="API Gateway alerting with sustained 91% CPU post-deployment of v2.15.1.",
            symptoms=["CPU increasing", "memory increasing", "recent deployment"],
            metrics={"cpu_percent": 91, "memory_percent": 86},
            logs=["WARN [WorkerPool] backlog exceeding threshold", "WARN [GC] GC overhead limit"],
            deployment={"recent": True, "version": "v2.15.1"},
        )
        db.add(inc_b)
        db.commit()
        passed["Incident B"] = inc_b.id == "IR-002"

        # 5. Analyze Incident B (Hindsight Recall)
        inc_b_dict = {
            "id": inc_b.id,
            "title": inc_b.title,
            "service": inc_b.service,
            "severity": inc_b.severity,
            "description": inc_b.description,
            "symptoms": inc_b.symptoms,
            "metrics": inc_b.metrics,
            "logs": inc_b.logs,
            "deployment": inc_b.deployment,
        }
        res_b = await agent.analyze_incident(inc_b_dict)

        # 6. Verify Hindsight recall and learning loop criteria
        passed["Hindsight Recall"] = res_b.historical_memory_found and len(res_b.historical_memories) > 0

        # Check that previous root cause was recalled
        recalled_text = " ".join([m.text for m in res_b.historical_memories])
        passed["Previous Root Cause"] = "memory leak" in recalled_text.lower() or "root cause" in recalled_text.lower()

        # Check that previous resolution was recalled
        passed["Previous Resolution"] = "rollback" in recalled_text.lower() or "resolution" in recalled_text.lower()

        # Check that previous runbook was recalled / matched
        passed["Previous Runbook"] = any("memory leak" in rb.lower() for rb in res_b.recommended_runbooks)

        # Check that recommendation for Incident B was influenced by history
        has_hist_rec = any(
            r.get("historical_support") == "IR-001" or "rollback" in r.get("action", "").lower()
            for r in res_b.recommended_actions
        )
        passed["Historical Recommendation"] = has_hist_rec

    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

    print("\n==================================================")
    print("HINDSIGHT LEARNING LOOP VERIFICATION")
    print("==================================================\n")

    all_ok = True
    checks = [
        "Incident A",
        "Postmortem A",
        "Hindsight Retain",
        "Incident B",
        "Hindsight Recall",
        "Previous Root Cause",
        "Previous Resolution",
        "Previous Runbook",
        "Historical Recommendation",
    ]

    for check in checks:
        status_str = "PASS" if passed.get(check, False) else "FAIL"
        if status_str != "PASS":
            all_ok = False
        print(f"{check}: {status_str}")

    print("\n" + ("OVERALL: PASS" if all_ok else "OVERALL: FAIL"))
    print("==================================================\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    code = asyncio.run(run_verification())
    sys.exit(code)
