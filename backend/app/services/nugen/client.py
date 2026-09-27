"""
Nugen AI HTTP Client for Domain-Aligned Model Inference and Alignment.
Zero credential leakage: NUGEN_API_KEY is never logged, printed, or exposed.
Includes timeout handling, retries, and clean degraded-mode exceptions.
"""

import httpx
import logging
import time
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger("eventos.nugen.client")


class NugenClientError(Exception):
    """Base exception for Nugen API interactions."""
    pass


class NugenClient:
    """
    HTTP client for Nugen Intelligence API (https://api.nugen.in).
    Interacts with:
    - /api/v3/models/base (List foundation base models)
    - /api/v3/alignment (Manage domain alignment projects)
    - /api/v3/chat/completions or /v1/chat/completions (Domain model inference)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model_id: Optional[str] = None,
        base_model: Optional[str] = None,
        timeout: float = 12.0
    ):
        self.api_key = api_key or settings.nugen_api_key
        self.api_url = (api_url or settings.nugen_api_url or "https://api.nugen.in").rstrip("/")
        self.model_id = model_id or settings.nugen_model_id or "nugen-aligned-eventos-v1"
        self.base_model = base_model or settings.nugen_base_model or "nugen-base-v1"
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Returns True only if a valid Nugen API key is set."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EVENTOS-ControlTower/0.2.0 (Nugen-Domain-Aligned)"
        }
        if self.is_configured:
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"
        return headers

    async def health_check(self) -> Dict[str, Any]:
        """
        Pings Nugen API to verify connectivity, latency, and model availability.
        Returns health status dictionary without leaking credentials.
        """
        if not self.is_configured:
            return {
                "configured": False,
                "connected": False,
                "status": "NOT_CONFIGURED",
                "model_id": self.model_id,
                "base_model": self.base_model,
                "latency_ms": None,
                "instruction": "Configure NUGEN_API_KEY in .env to activate live Nugen cloud inference."
            }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.api_url}/api/v3/models/base",
                    headers=self._get_headers()
                )
                latency = round((time.time() - start_time) * 1000, 1)

                if resp.status_code == 200:
                    return {
                        "configured": True,
                        "connected": True,
                        "status": "CONNECTED",
                        "model_id": self.model_id,
                        "base_model": self.base_model,
                        "latency_ms": latency,
                        "instruction": None
                    }
                elif resp.status_code in [401, 403]:
                    logger.warning(f"[NUGEN] Authentication failure on health check (HTTP {resp.status_code})")
                    return {
                        "configured": True,
                        "connected": False,
                        "status": "AUTH_FAILED",
                        "model_id": self.model_id,
                        "base_model": self.base_model,
                        "latency_ms": latency,
                        "instruction": "Invalid NUGEN_API_KEY. Verify credentials at https://nugen.in."
                    }
                else:
                    return {
                        "configured": True,
                        "connected": False,
                        "status": f"HTTP_{resp.status_code}",
                        "model_id": self.model_id,
                        "base_model": self.base_model,
                        "latency_ms": latency,
                        "instruction": "Nugen upstream service returned non-200 status."
                    }
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 1)
            logger.warning(f"[NUGEN] Health check failed: {type(e).__name__}")
            return {
                "configured": True,
                "connected": False,
                "status": "UNREACHABLE",
                "model_id": self.model_id,
                "base_model": self.base_model,
                "latency_ms": latency,
                "instruction": f"Could not reach Nugen API at {self.api_url}. Network error."
            }

    async def list_base_models(self) -> List[Dict[str, Any]]:
        """Queries upstream for supported foundation models."""
        if not self.is_configured:
            return [{"id": self.base_model, "name": "Nugen Base Operations Foundation", "status": "AVAILABLE"}]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.api_url}/api/v3/models/base",
                headers=self._get_headers()
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("models", data if isinstance(data, list) else [])
            return [{"id": self.base_model, "status": "AVAILABLE"}]

    async def create_alignment_project(
        self,
        project_name: str,
        base_model: str,
        target_model_id: str,
        target_score: float = 0.95,
        dataset_items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Dispatches an alignment task to the Nugen platform."""
        if not self.is_configured:
            return {
                "id": f"local-{project_name}",
                "status": "LOCAL_ALIGNED",
                "target_model_id": target_model_id,
                "target_score": target_score
            }

        payload = {
            "project_name": project_name,
            "base_model": base_model,
            "target_model_id": target_model_id,
            "target_score": target_score,
            "domain": "event_operations",
            "dataset_records_count": len(dataset_items or [])
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.api_url}/api/v3/alignment",
                json=payload,
                headers=self._get_headers()
            )
            if resp.status_code in [200, 201, 202]:
                return resp.json()
            return {
                "id": f"align-{target_model_id}",
                "status": "REGISTERED",
                "note": f"Upstream response HTTP {resp.status_code}"
            }

    async def infer(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        Executes inference against the domain-aligned Nugen model.
        Returns parsed JSON dictionary output.
        """
        if not self.is_configured:
            raise NugenClientError("Nugen API key not configured. Cannot perform live inference.")

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        # Try v3 completions first, then v1 completions fallback
        endpoints = [
            f"{self.api_url}/api/v3/chat/completions",
            f"{self.api_url}/v1/chat/completions"
        ]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            last_error = None
            for ep in endpoints:
                try:
                    resp = await client.post(ep, json=payload, headers=self._get_headers())
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        import json
                        return json.loads(content)
                    elif resp.status_code in [401, 403]:
                        raise NugenClientError("Nugen API authentication failed: invalid credentials.")
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:120]}"
                except NugenClientError:
                    raise
                except Exception as ex:
                    last_error = str(ex)

            raise NugenClientError(f"Nugen inference failed across endpoints: {last_error}")


_nugen_client: Optional[NugenClient] = None


def get_nugen_client() -> NugenClient:
    """Returns singleton instance of NugenClient."""
    global _nugen_client
    if _nugen_client is None:
        _nugen_client = NugenClient()
    return _nugen_client
