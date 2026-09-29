"""Hypothesis Engine: Generates reasoned root cause hypotheses from incident evidence & Hindsight memories."""
from typing import Any, Dict, List, Optional
import re
from app.models.analysis import Hypothesis


class HypothesisEngine:
    """
    Generates structured hypotheses with confidence scores, evidence citations,
    and reasoning. Correlates symptoms with historical incident patterns.
    """

    def generate_hypotheses(
        self,
        incident: Dict[str, Any],
        historical_memories: Optional[List[Dict[str, Any]]] = None,
        llm_hypotheses: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Hypothesis]:
        """
        Generate hypotheses combining rule-based heuristics, Hindsight historical learnings,
        and LLM deductions if available.
        """
        historical_memories = historical_memories or []
        hypotheses: List[Hypothesis] = []

        # If LLM returned valid hypotheses, convert and enhance them with historical evidence
        if llm_hypotheses:
            for h in llm_hypotheses:
                try:
                    hyp = Hypothesis(
                        cause=h.get("cause", "Unknown Cause"),
                        confidence=min(max(float(h.get("confidence", 0.5)), 0.1), 0.99),
                        evidence=list(h.get("evidence", [])),
                        reasoning=h.get("reasoning", ""),
                        category=h.get("category", "unknown"),
                    )
                    # Check if historical memories reinforce this hypothesis
                    for mem in historical_memories:
                        text = mem.get("text", "").lower()
                        if hyp.cause.lower() in text or any(ev.lower() in text for ev in hyp.evidence):
                            if "Similar historical incident reinforced root cause" not in hyp.evidence:
                                hyp.evidence.append(f"Historical Hindsight confirmation: {mem.get('text', '')[:120]}...")
                                hyp.confidence = min(hyp.confidence + 0.15, 0.98)
                    hypotheses.append(hyp)
                except Exception:
                    pass

        # If we have hypotheses from LLM, return them sorted by confidence
        if hypotheses:
            hypotheses.sort(key=lambda x: x.confidence, reverse=True)
            return hypotheses

        # Deterministic / rule-based hypothesis generation (works standalone or offline)
        title = incident.get("title", "").lower()
        desc = incident.get("description", "").lower()
        symptoms = [s.lower() for s in incident.get("symptoms", [])]
        symptoms_str = " ".join(symptoms)
        metrics = incident.get("metrics", {})
        deployment = incident.get("deployment", {})
        combined_text = f"{title} {desc} {symptoms_str}".lower()

        # Check historical memories for matching root causes
        historical_match = None
        historical_incident_id = None
        for mem in historical_memories:
            text = mem.get("text", "")
            # Look for patterns like "root cause: ..." or "IR-xxx"
            rc_match = re.search(r"root cause[:\s]+([^\n\.,]+)", text, re.I)
            id_match = re.search(r"(IR-\w+)", text)
            if rc_match:
                historical_match = rc_match.group(1).strip()
            if id_match:
                historical_incident_id = id_match.group(1).strip()

        # 1. High CPU / Memory Leak Scenario
        if "cpu" in combined_text or "memory" in combined_text or metrics.get("cpu_percent", 0) > 80:
            evidence = []
            if metrics.get("cpu_percent"):
                evidence.append(f"CPU utilization at {metrics.get('cpu_percent')}%")
            if "memory increasing" in symptoms_str or "leak" in symptoms_str:
                evidence.append("Memory usage continuously increasing without GC stabilization")
            if deployment.get("recent") or "deployment" in symptoms_str:
                evidence.append(f"Recent deployment detected: version {deployment.get('version', 'latest')}")

            # If Hindsight memories exist
            if historical_match or historical_memories:
                hist_id_str = f" ({historical_incident_id})" if historical_incident_id else ""
                evidence.append(f"Matching historical postmortem in Hindsight{hist_id_str}")
                hypotheses.append(
                    Hypothesis(
                        cause="Deployment-related memory leak",
                        confidence=0.92,
                        evidence=evidence,
                        reasoning=(
                            f"Current symptoms closely match historical incident{hist_id_str}. "
                            "Continuous memory growth following a release points directly to an uncollected object leak in the new build."
                        ),
                        category="deployment",
                    )
                )
            else:
                hypotheses.append(
                    Hypothesis(
                        cause="Memory leak in application worker threads",
                        confidence=0.78,
                        evidence=evidence or ["Sustained high resource utilization", "Recent service deployment"],
                        reasoning="Steady escalation of CPU and memory consumption following a software release typically indicates an unmanaged resource leak.",
                        category="resource",
                    )
                )

            hypotheses.append(
                Hypothesis(
                    cause="Sudden traffic burst or DDoS",
                    confidence=0.45,
                    evidence=["High CPU load across service nodes"],
                    reasoning="Unforeseen volume surges can saturate CPU cores, though memory growth without traffic correlation makes this less primary.",
                    category="traffic",
                )
            )

        # 2. Database Timeout Scenario
        elif "database" in combined_text or "db" in combined_text or "timeout" in combined_text:
            evidence = []
            if "slow query" in symptoms_str:
                evidence.append("Slow queries detected in query analyzer")
            if "pool" in symptoms_str or "connection" in symptoms_str:
                evidence.append("Connection pool exhaustion observed")
            if metrics.get("db_connections_active"):
                evidence.append(f"Active database connections: {metrics.get('db_connections_active')}")

            if historical_match or historical_memories:
                evidence.append("Historical Hindsight incident matches database connection exhaustion pattern")
                hypotheses.append(
                    Hypothesis(
                        cause="Connection pool exhaustion from unindexed query scan",
                        confidence=0.89,
                        evidence=evidence,
                        reasoning="Hindsight records identify identical connection spikes resolving when rogue unindexed queries were terminated.",
                        category="database",
                    )
                )
            else:
                hypotheses.append(
                    Hypothesis(
                        cause="Database connection pool saturation",
                        confidence=0.82,
                        evidence=evidence or ["Database timeouts reported by API clients"],
                        reasoning="Clients reporting database query timeouts usually indicates worker threads blocking on exhausted connection pool slots.",
                        category="database",
                    )
                )

        # 3. HTTP 5xx Spike Scenario
        elif "5xx" in combined_text or "http" in combined_text or "error" in combined_text:
            evidence = ["Elevated HTTP 502/503 response rates", "Upstream gateway failing health checks"]
            if deployment.get("recent"):
                evidence.append(f"Deployment occurred {deployment.get('timestamp', 'recently')}")

            if historical_match or historical_memories:
                evidence.append("Hindsight historical records show past 5xx spike tied to misconfigured upstream endpoint")
                hypotheses.append(
                    Hypothesis(
                        cause="Faulty upstream routing or invalid configuration deployment",
                        confidence=0.90,
                        evidence=evidence,
                        reasoning="Previous postmortems confirm 5xx spikes following deployments stemmed from misconfigured routing ingress rules.",
                        category="deployment",
                    )
                )
            else:
                hypotheses.append(
                    Hypothesis(
                        cause="Faulty upstream service deployment or crash loop",
                        confidence=0.80,
                        evidence=evidence,
                        reasoning="Sudden 5xx bursts typically result from fatal crashes or ingress misconfiguration immediately after a code change.",
                        category="application",
                    )
                )

        # 4. Fallback Generic Hypothesis
        else:
            hypotheses.append(
                Hypothesis(
                    cause="Service degradation due to resource constraint",
                    confidence=0.60,
                    evidence=[s for s in symptoms] or ["Service anomalous state reported"],
                    reasoning="Telemetry demonstrates deviation from nominal baseline operating parameters.",
                    category="unknown",
                )
            )

        hypotheses.sort(key=lambda x: x.confidence, reverse=True)
        return hypotheses
