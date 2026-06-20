"""Provider selection and fallback orchestration for transcription."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

from src.core.logging import get_logger
from .provider_base import TranscriptionProvider

logger = get_logger(__name__)


@dataclass
class ProviderPolicy:
    """Policy configuration for provider selection."""
    name: str
    priority: int
    max_latency_ms: int
    min_confidence: float
    bandwidth_requirement_kbps: Optional[int]
    supports_streaming: bool
    supports_offline: bool
    cost_per_minute: Optional[float]
    languages: List[str]


class FallbackOrchestrator:
    """Manages provider selection and fallback strategies."""

    def __init__(self, default_policy: Optional[Dict[str, Any]] = None):
        """
        Initialize fallback orchestrator.

        Args:
            default_policy: Default fallback policy configuration
        """
        self.default_policy = default_policy or {}
        self.provider_policies: Dict[str, ProviderPolicy] = {}
        self._network_status = {"available": True, "bandwidth_kbps": 1000}
        self._provider_health: Dict[str, Dict[str, Any]] = {}

    def register_provider_policy(self, provider_name: str, policy: ProviderPolicy) -> None:
        """
        Register a provider with its policy configuration.

        Args:
            provider_name: Provider name
            policy: Provider policy configuration
        """
        self.provider_policies[provider_name] = policy
        self._provider_health[provider_name] = {
            "healthy": True,
            "last_check": datetime.utcnow().isoformat(),
            "error_count": 0,
            "avg_latency_ms": 0,
        }

    async def select_provider(
        self,
        metadata: Dict[str, Any],
        primary_providers: List[TranscriptionProvider],
        offline_providers: List[TranscriptionProvider],
    ) -> Optional[TranscriptionProvider]:
        """
        Select the best provider based on policy and conditions.

        Args:
            metadata: Job metadata including language, bandwidth, etc.
            primary_providers: List of available primary providers
            offline_providers: List of available offline providers

        Returns:
            Selected provider or None if none suitable
        """
        # Combine all available providers
        all_providers = primary_providers + offline_providers

        # Filter by language support
        language = metadata.get("language", "en-US")
        suitable_providers = [
            p for p in all_providers
            if self._supports_language(p, language)
        ]

        if not suitable_providers:
            logger.warning(f"No providers support language: {language}")
            return None

        # Check network status and filter accordingly
        if not self._network_status["available"]:
            # Network unavailable - only offline providers
            suitable_providers = [
                p for p in suitable_providers
                if p.supports_offline()
            ]
            logger.info("Network unavailable, using offline providers only")
        else:
            # Network available - check bandwidth requirements
            bandwidth = self._network_status["bandwidth_kbps"]
            suitable_providers = [
                p for p in suitable_providers
                if self._meets_bandwidth_requirement(p, bandwidth)
            ]

        if not suitable_providers:
            logger.warning("No providers meet current network conditions")
            return None

        # Sort by policy priority and health
        ranked_providers = self._rank_providers(suitable_providers, metadata)

        # Select the best provider
        selected = ranked_providers[0] if ranked_providers else None

        if selected:
            logger.info(f"Selected provider: {selected.name} (mode: {selected.mode})")
        else:
            logger.error("No suitable provider found")

        return selected

    async def check_provider_health(self, provider: TranscriptionProvider) -> Dict[str, Any]:
        """
        Check health status of a provider.

        Args:
            provider: Provider to check

        Returns:
            Health status information
        """
        health = self._provider_health.get(provider.name, {
            "healthy": True,
            "last_check": datetime.utcnow().isoformat(),
            "error_count": 0,
            "avg_latency_ms": 0,
        })

        # Perform health check (mock implementation)
        try:
            start_time = datetime.utcnow()
            
            # Simple ping/health check - would be provider-specific
            await asyncio.wait_for(self._ping_provider(provider), timeout=5.0)
            
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Update health status
            health["healthy"] = True
            health["last_check"] = datetime.utcnow().isoformat()
            health["avg_latency_ms"] = (health["avg_latency_ms"] + latency_ms) // 2
            
            if latency_ms > 5000:  # 5 second threshold
                health["error_count"] += 1

        except Exception as e:
            health["healthy"] = False
            health["last_check"] = datetime.utcnow().isoformat()
            health["error_count"] += 1
            health["last_error"] = str(e)
            logger.warning(f"Provider {provider.name} health check failed: {e}")

        self._provider_health[provider.name] = health
        return health

    def update_network_status(self, available: bool, bandwidth_kbps: Optional[int] = None) -> None:
        """
        Update network status for provider selection.

        Args:
            available: Whether network is available
            bandwidth_kbps: Current bandwidth in kbps
        """
        self._network_status["available"] = available
        if bandwidth_kbps is not None:
            self._network_status["bandwidth_kbps"] = bandwidth_kbps

        logger.info(f"Network status updated: available={available}, bandwidth={bandwidth_kbps}kbps")

    def get_provider_recommendations(
        self,
        metadata: Dict[str, Any],
        primary_providers: List[TranscriptionProvider],
        offline_providers: List[TranscriptionProvider],
    ) -> List[Dict[str, Any]]:
        """
        Get provider recommendations with reasoning.

        Args:
            metadata: Job metadata
            primary_providers: Available primary providers
            offline_providers: List of available offline providers

        Returns:
            List of ranked provider recommendations
        """
        recommendations = []
        all_providers = primary_providers + offline_providers

        for provider in all_providers:
            recommendation = {
                "provider": provider.name,
                "mode": provider.mode,
                "supports_streaming": provider.supports_streaming(),
                "supports_offline": provider.supports_offline(),
                "health": self._provider_health.get(provider.name, {}),
                "policy": self.provider_policies.get(provider.name),
                "recommendation_reason": [],
                "suitable": True,
            }

            # Check language support
            language = metadata.get("language", "en-US")
            if not self._supports_language(provider, language):
                recommendation["suitable"] = False
                recommendation["recommendation_reason"].append(f"Does not support {language}")

            # Check bandwidth requirements
            if self._network_status["available"]:
                bandwidth = self._network_status["bandwidth_kbps"]
                if not self._meets_bandwidth_requirement(provider, bandwidth):
                    recommendation["suitable"] = False
                    recommendation["recommendation_reason"].append(f"Insufficient bandwidth (requires {self._get_bandwidth_requirement(provider)}kbps)")

            # Check network availability for cloud providers
            if not self._network_status["available"] and not provider.supports_offline():
                recommendation["suitable"] = False
                recommendation["recommendation_reason"].append("Network unavailable and provider is cloud-only")

            # Add positive reasons
            if recommendation["suitable"]:
                if provider.supports_streaming():
                    recommendation["recommendation_reason"].append("Supports real-time streaming")
                if provider.supports_offline():
                    recommendation["recommendation_reason"].append("Works offline")
                if recommendation["health"].get("healthy", False):
                    recommendation["recommendation_reason"].append("Currently healthy")

            recommendations.append(recommendation)

        # Sort by suitability and priority
        recommendations.sort(key=lambda x: (
            not x["suitable"],
            -self.provider_policies.get(x["provider"], ProviderPolicy("", 0, 0, 0, None, False, False, None, [])).priority
        ))

        return recommendations

    def _supports_language(self, provider: TranscriptionProvider, language: str) -> bool:
        """Check if provider supports the given language."""
        policy = self.provider_policies.get(provider.name)
        if not policy:
            return True  # Assume support if no policy defined

        return language in policy.languages or not policy.languages

    def _meets_bandwidth_requirement(self, provider: TranscriptionProvider, available_bandwidth: int) -> bool:
        """Check if available bandwidth meets provider requirements."""
        policy = self.provider_policies.get(provider.name)
        if not policy or policy.bandwidth_requirement_kbps is None:
            return True  # No requirement

        return available_bandwidth >= policy.bandwidth_requirement_kbps

    def _get_bandwidth_requirement(self, provider: TranscriptionProvider) -> Optional[int]:
        """Get bandwidth requirement for provider."""
        policy = self.provider_policies.get(provider.name)
        return policy.bandwidth_requirement_kbps if policy else None

    def _rank_providers(
        self,
        providers: List[TranscriptionProvider],
        metadata: Dict[str, Any],
    ) -> List[TranscriptionProvider]:
        """Rank providers by policy priority and health."""
        def get_score(provider: TranscriptionProvider) -> tuple:
            policy = self.provider_policies.get(provider.name)
            health = self._provider_health.get(provider.name, {})

            # Higher priority is better
            priority = policy.priority if policy else 0

            # Healthy is better
            healthy = 1 if health.get("healthy", True) else 0

            # Lower latency is better
            latency = -health.get("avg_latency_ms", 0)

            # Prefer streaming if requested
            streaming_bonus = 1 if (metadata.get("prefer_streaming", False) and provider.supports_streaming()) else 0

            return (-priority, -healthy, latency, -streaming_bonus)

        return sorted(providers, key=get_score)

    async def _ping_provider(self, provider: TranscriptionProvider) -> None:
        """Ping provider for health check (mock implementation)."""
        # In production, this would be provider-specific health checks
        await asyncio.sleep(0.1)  # Simulate network latency
