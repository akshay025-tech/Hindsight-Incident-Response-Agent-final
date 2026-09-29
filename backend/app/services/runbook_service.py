"""Runbook service - load and match runbooks."""
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

RUNBOOKS_PATH = os.path.join(os.path.dirname(__file__), "../data/runbooks.json")


class RunbookService:
    def __init__(self):
        self._runbooks: List[Dict[str, Any]] = []
        self._load_runbooks()

    def _load_runbooks(self):
        try:
            path = os.path.abspath(RUNBOOKS_PATH)
            with open(path, "r", encoding="utf-8") as f:
                self._runbooks = json.load(f)
            logger.info(f"Loaded {len(self._runbooks)} runbooks")
        except Exception as e:
            logger.error(f"Failed to load runbooks: {e}")
            self._runbooks = []

    def get_all(self) -> List[Dict[str, Any]]:
        return self._runbooks

    def get_by_id(self, runbook_id: str) -> Optional[Dict[str, Any]]:
        for rb in self._runbooks:
            if rb.get("id") == runbook_id:
                return rb
        return None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        name_lower = name.lower()
        for rb in self._runbooks:
            if rb.get("name", "").lower() == name_lower:
                return rb
        return None

    def match_runbooks(
        self,
        service: str,
        symptoms: List[str],
        hypotheses: List[str],
        historical_runbooks: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Match runbooks based on service, symptoms, and hypotheses.
        If historical_runbooks provided (from Hindsight), prioritize those.
        """
        scored: List[tuple] = []
        symptom_text = " ".join(symptoms).lower()
        hypothesis_text = " ".join(hypotheses).lower()
        service_lower = service.lower()

        for rb in self._runbooks:
            score = 0
            applicable_services = [s.lower() for s in rb.get("applicable_services", [])]
            applicable_symptoms = [s.lower() for s in rb.get("applicable_symptoms", [])]

            # Service match
            for svc in applicable_services:
                if svc in service_lower or service_lower in svc:
                    score += 3
                    break

            # Symptom match
            for sym in applicable_symptoms:
                if sym in symptom_text or sym in hypothesis_text:
                    score += 2

            # Historical boost
            if historical_runbooks:
                for hist_rb in historical_runbooks:
                    if hist_rb.lower() in rb.get("name", "").lower():
                        score += 10  # Strong historical evidence
                        rb = {**rb, "historically_successful": True, "previously_successful": hist_rb}

            if score > 0:
                scored.append((score, rb))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [rb for _, rb in scored[:4]]


_runbook_service: Optional[RunbookService] = None


def get_runbook_service() -> RunbookService:
    global _runbook_service
    if _runbook_service is None:
        _runbook_service = RunbookService()
    return _runbook_service
