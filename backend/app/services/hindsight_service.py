"""Hindsight service - the ONLY place that talks to Hindsight."""
import logging
from typing import Any, Dict, List, Optional
import re

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HindsightService:
    """
    Wraps all Hindsight operations.
    Gracefully degrades if Hindsight is unavailable.
    Includes in-memory fallback memory bank for offline hackathon simulation.
    """

    def __init__(self):
        self._client = None
        self._available = False
        self._fallback_memories: List[Dict[str, Any]] = []
        self._init_client()

    def _init_client(self):
        """Initialize the Hindsight client."""
        if not settings.hindsight_api_key:
            logger.warning("HINDSIGHT_API_KEY not set - Hindsight running in local fallback mode")
            self._available = False
            return

        try:
            from hindsight_client import Hindsight
            self._client = Hindsight(
                base_url=settings.hindsight_base_url,
                api_key=settings.hindsight_api_key,
                timeout=30.0,
            )
            self._available = True
            logger.info(f"Hindsight client initialized: {settings.hindsight_base_url}")
        except ImportError:
            logger.error("hindsight-client package not installed")
            self._available = False
        except Exception as e:
            logger.error(f"Failed to initialize Hindsight client: {e}")
            self._available = False

    def _ensure_bank_exists(self):
        """Ensure the memory bank exists, create it if not."""
        if not self._client:
            return
        try:
            self._client.create_bank(
                bank_id=settings.hindsight_bank_id,
                name="Incident Response Team",
                mission=(
                    "You are a memory bank for an incident response team. "
                    "You store and recall past incidents, their root causes, "
                    "resolution steps, and which runbooks succeeded. "
                    "Help the team learn from history to resolve future incidents faster."
                ),
            )
            logger.info(f"Ensured Hindsight bank exists: {settings.hindsight_bank_id}")
        except Exception as e:
            # Bank may already exist - that's fine
            logger.debug(f"Bank creation (may already exist): {e}")

    def _sync_fallback_with_db(self):
        """Ensure local fallback bank includes retained postmortems from database."""
        try:
            from app.database import SessionLocal, PostmortemDB
            db = SessionLocal()
            try:
                pms = db.query(PostmortemDB).filter(PostmortemDB.retained_in_hindsight == True).all()
                existing_ids = {m.get("id") for m in self._fallback_memories}
                for pm in pms:
                    if pm.incident_id not in existing_ids:
                        retention_text = (
                            f"INCIDENT POSTMORTEM {pm.incident_id}:\n"
                            f"Root cause: {pm.root_cause}\n"
                            f"Resolution: {pm.resolution}\n"
                            f"Runbook: {pm.runbook_used or 'API Gateway Memory Leak Recovery'}\n"
                            f"What worked: {'; '.join(pm.what_worked or [])}\n"
                        )
                        self._fallback_memories.append({
                            "id": pm.incident_id,
                            "text": retention_text,
                            "context": f"Postmortem for {pm.incident_id}",
                            "metadata": {"incident_id": pm.incident_id, "root_cause": pm.root_cause},
                        })
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"Could not sync fallback memories from DB: {e}")


    async def health_check(self) -> Dict[str, Any]:
        """Check Hindsight connectivity."""
        self._sync_fallback_with_db()
        if not self._client or not self._available:
            return {
                "connected": False,
                "bank_id": settings.hindsight_bank_id,
                "provider": "Hindsight",
                "message": "Local fallback active (set HINDSIGHT_API_KEY for cloud sync)",
                "retained_count": len(self._fallback_memories),
            }
        try:
            version = self._client.get_version()
            return {
                "connected": True,
                "bank_id": settings.hindsight_bank_id,
                "provider": "Hindsight",
                "base_url": settings.hindsight_base_url,
                "api_version": getattr(version, "api_version", "unknown"),
            }
        except Exception as e:
            logger.warning(f"Hindsight health check failed: {e}")
            return {
                "connected": False,
                "bank_id": settings.hindsight_bank_id,
                "provider": "Hindsight",
                "message": str(e),
                "retained_count": len(self._fallback_memories),
            }

    async def recall_similar_incidents(self, query: str) -> Dict[str, Any]:
        """
        Recall similar historical incidents from Hindsight.
        Uses real client when connected, or fallback memory bank when offline.
        """
        if self._client and self._available:
            try:
                self._ensure_bank_exists()
                result = await self._client.arecall(
                    bank_id=settings.hindsight_bank_id,
                    query=query,
                    budget="mid",
                )

                memories = []
                for item in (result.results or []):
                    mem = {
                        "text": getattr(item, "text", ""),
                        "type": getattr(item, "type", None),
                        "context": getattr(item, "context", None),
                        "id": getattr(item, "id", None),
                    }
                    memories.append(mem)

                logger.info(f"Hindsight cloud recall returned {len(memories)} memories")
                return {
                    "available": True,
                    "memories": memories,
                    "count": len(memories),
                }
            except Exception as e:
                logger.error(f"Hindsight cloud recall failed: {e}. Checking local memories.")

        # Offline / Fallback recall mechanism
        self._sync_fallback_with_db()
        query_words = set(re.findall(r"\w+", query.lower()))
        matched = []
        for mem in self._fallback_memories:
            text = mem.get("text", "").lower()
            score = sum(1 for w in query_words if len(w) > 3 and w in text)
            if score > 0:
                matched.append((score, mem))

        matched.sort(key=lambda x: x[0], reverse=True)
        results = [m for _, m in matched]

        logger.info(f"Fallback recall matched {len(results)} local memories")
        return {
            "available": True if results else False,
            "message": "Recalled from local operational memory bank",
            "memories": results,
            "count": len(results),
        }

    async def reflect_on_incidents(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Reflect on historical incidents using Hindsight reasoning."""
        if self._client and self._available:
            try:
                self._ensure_bank_exists()
                kwargs = {
                    "bank_id": settings.hindsight_bank_id,
                    "query": query,
                    "budget": "mid",
                }
                if context:
                    kwargs["context"] = context

                result = await self._client.areflect(**kwargs)
                text = getattr(result, "text", None)
                logger.info(f"Hindsight reflect completed: {len(text or '')} chars")
                return {
                    "available": True,
                    "text": text,
                }
            except Exception as e:
                logger.error(f"Hindsight cloud reflect failed: {e}")

        # Local fallback reflection
        if self._fallback_memories:
            sample = self._fallback_memories[0].get("text", "")
            return {
                "available": True,
                "text": f"Historical reflection confirms recurring pattern: {sample[:200]}...",
            }

        return {
            "available": False,
            "message": "No historical memory available to reflect on yet",
            "text": None,
        }

    async def retain_incident_learning(
        self,
        incident_id: str,
        content: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Retain incident learning in Hindsight after postmortem.
        """
        # Always save to local fallback bank as well
        local_entry = {
            "id": incident_id,
            "text": content,
            "context": context,
            "metadata": metadata or {},
        }
        # Avoid duplicate entries in local fallback
        self._fallback_memories = [m for m in self._fallback_memories if m.get("id") != incident_id]
        self._fallback_memories.append(local_entry)

        if self._client and self._available:
            try:
                self._ensure_bank_exists()
                kwargs = {
                    "bank_id": settings.hindsight_bank_id,
                    "content": content,
                    "document_id": incident_id,
                }
                if context:
                    kwargs["context"] = context
                if metadata:
                    kwargs["metadata"] = metadata

                await self._client.aretain(**kwargs)
                logger.info(f"Retained incident learning for {incident_id} in Hindsight cloud")
                return {
                    "available": True,
                    "retained": True,
                    "incident_id": incident_id,
                }
            except Exception as e:
                logger.error(f"Hindsight cloud retain failed for {incident_id}: {e}")

        logger.info(f"Retained incident learning for {incident_id} in local fallback store")
        return {
            "available": True,
            "retained": True,
            "incident_id": incident_id,
            "mode": "local_fallback",
        }


# Singleton instance
_hindsight_service: Optional[HindsightService] = None


def get_hindsight_service() -> HindsightService:
    global _hindsight_service
    if _hindsight_service is None:
        _hindsight_service = HindsightService()
    return _hindsight_service
