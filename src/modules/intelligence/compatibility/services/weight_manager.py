"""Weight configuration manager for job family scoring."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models import (
    WeightConfiguration,
    JobFamilyEnum,
    SignalQualityEnum
)


class WeightManager:
    """Manages weight configurations for different job families."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent.parent / "config"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration files
        self.weights_file = self.storage_path / "job_family_weights.json"
        self.presets_file = self.storage_path / "scoring_presets.json"
        
        # Load configurations
        self.configurations = self._load_configurations()
        self.presets = self._load_presets()
        
        # Initialize default configurations if needed
        self._initialize_default_configurations()
    
    def _load_configurations(self) -> Dict[str, WeightConfiguration]:
        """Load weight configurations from storage."""
        if not self.weights_file.exists():
            return {}
        
        try:
            with open(self.weights_file, 'r') as f:
                data = json.load(f)
            
            configurations = {}
            for config_id, config_data in data.items():
                # Convert datetime strings back to datetime objects
                if config_data.get("created_at"):
                    config_data["created_at"] = datetime.fromisoformat(config_data["created_at"])
                
                # Convert job family string to enum
                if config_data.get("job_family"):
                    config_data["job_family"] = JobFamilyEnum(config_data["job_family"])
                
                # Convert quality enums
                if config_data.get("quality_multipliers"):
                    quality_multipliers = {}
                    for quality, multiplier in config_data["quality_multipliers"].items():
                        quality_multipliers[SignalQualityEnum(quality)] = multiplier
                    config_data["quality_multipliers"] = quality_multipliers
                
                configurations[config_id] = WeightConfiguration(**config_data)
            
            return configurations
        except Exception as e:
            print(f"Error loading configurations: {e}")
            return {}
    
    def _load_presets(self) -> Dict[str, Dict[str, Any]]:
        """Load scoring presets from storage."""
        if not self.presets_file.exists():
            return {}
        
        try:
            with open(self.presets_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading presets: {e}")
            return {}
    
    def _save_configurations(self):
        """Save configurations to storage."""
        data = {}
        for config_id, config in self.configurations.items():
            data[config_id] = config.model_dump()
        
        with open(self.weights_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _initialize_default_configurations(self):
        """Initialize default weight configurations for all job families."""
        default_configs_created = 0
        
        for job_family in JobFamilyEnum:
            # Check if configuration already exists
            existing_config = self.get_configuration(job_family)
            if existing_config:
                continue
            
            # Create default configuration based on job family
            default_config = self._create_default_configuration(job_family)
            self.configurations[default_config.config_id] = default_config
            default_configs_created += 1
        
        if default_configs_created > 0:
            self._save_configurations()
            print(f"Created {default_configs_created} default weight configurations")
    
    def _create_default_configuration(self, job_family: JobFamilyEnum) -> WeightConfiguration:
        """Create default weight configuration for a job family."""
        
        # Define domain weights based on job family
        domain_weights = self._get_default_domain_weights(job_family)
        
        # Define quality multipliers (same for all families)
        quality_multipliers = {
            SignalQualityEnum.HIGH: 1.0,
            SignalQualityEnum.MEDIUM: 0.8,
            SignalQualityEnum.LOW: 0.6,
            SignalQualityEnum.UNKNOWN: 0.4
        }
        
        # Define minimum requirements based on job family
        minimum_domain_scores = self._get_default_minimum_scores(job_family)
        
        # Business context description
        business_context = self._get_business_context(job_family)
        
        return WeightConfiguration(
            config_id=f"config_{job_family.value}_default",
            job_family=job_family,
            business_context=business_context,
            domain_weights=domain_weights,
            quality_multipliers=quality_multipliers,
            minimum_domain_scores=minimum_domain_scores,
            created_by="weight_manager",
            created_at=datetime.utcnow(),
            is_active=True,
            version="1.0"
        )
    
    def _get_default_domain_weights(self, job_family: JobFamilyEnum) -> Dict[str, float]:
        """Get default domain weights for a job family."""
        
        # Define weight patterns for different job families
        weight_patterns = {
            JobFamilyEnum.TECHNOLOGY: {
                "knowledge": 0.2,
                "skills": 0.4,  # Technical skills are most important
                "abilities": 0.3,
                "habits": 0.1
            },
            JobFamilyEnum.HEALTHCARE: {
                "knowledge": 0.35,  # Medical knowledge is critical
                "skills": 0.25,
                "abilities": 0.3,
                "habits": 0.1
            },
            JobFamilyEnum.FINANCE: {
                "knowledge": 0.3,
                "skills": 0.25,
                "abilities": 0.35,  # Analytical abilities are key
                "habits": 0.1
            },
            JobFamilyEnum.EDUCATION: {
                "knowledge": 0.3,
                "skills": 0.2,
                "abilities": 0.3,
                "habits": 0.2  # Teaching habits are important
            },
            JobFamilyEnum.SALES: {
                "knowledge": 0.15,
                "skills": 0.3,
                "abilities": 0.4,  # Communication and persuasion abilities
                "habits": 0.15
            },
            JobFamilyEnum.OTHER: {
                "knowledge": 0.25,
                "skills": 0.25,
                "abilities": 0.25,
                "habits": 0.25  # Default balanced weights
            }
        }
        
        return weight_patterns.get(job_family, {
            "knowledge": 0.25,
            "skills": 0.25,
            "abilities": 0.25,
            "habits": 0.25  # Default balanced weights
        })
    
    def _get_default_minimum_scores(self, job_family: JobFamilyEnum) -> Dict[str, float]:
        """Get default minimum scores for a job family."""
        
        # Define minimum score requirements
        minimum_patterns = {
            JobFamilyEnum.TECHNOLOGY: {
                "skills": 0.6,  # Must have decent technical skills
                "abilities": 0.5
            },
            JobFamilyEnum.HEALTHCARE: {
                "knowledge": 0.7,  # High knowledge requirements
                "abilities": 0.6
            },
            JobFamilyEnum.FINANCE: {
                "knowledge": 0.6,
                "abilities": 0.65  # Strong analytical abilities needed
            },
            JobFamilyEnum.EDUCATION: {
                "knowledge": 0.6,
                "abilities": 0.6
            }
        }
        
        return minimum_patterns.get(job_family, {})
    
    def _get_business_context(self, job_family: JobFamilyEnum) -> str:
        """Get business context description for a job family."""
        
        contexts = {
            JobFamilyEnum.TECHNOLOGY: "Technology roles requiring strong technical skills, problem-solving abilities, and continuous learning habits.",
            JobFamilyEnum.HEALTHCARE: "Healthcare roles requiring extensive medical knowledge, patient care skills, and professional ethics.",
            JobFamilyEnum.FINANCE: "Finance roles requiring strong analytical abilities, financial knowledge, and attention to detail.",
            JobFamilyEnum.EDUCATION: "Education roles requiring subject matter expertise, teaching skills, and patience.",
            JobFamilyEnum.SALES: "Sales roles requiring strong communication abilities, product knowledge, and relationship-building habits.",
            JobFamilyEnum.OTHER: f"Roles in the job family."
        }
        
        return contexts.get(job_family, f"Roles in the {job_family.value} job family.")
    
    def get_configuration(self, job_family: JobFamilyEnum, 
                         config_id: Optional[str] = None) -> WeightConfiguration:
        """Get weight configuration for a job family."""
        
        # If specific config ID provided, try to get it
        if config_id:
            config = self.configurations.get(config_id)
            if config and config.job_family == job_family and config.is_active:
                return config
        
        # Get active configuration for job family
        for config in self.configurations.values():
            if config.job_family == job_family and config.is_active:
                return config
        
        # Fallback to default configuration
        return self._create_default_configuration(job_family)
    
    def create_configuration(self, job_family: JobFamilyEnum,
                           domain_weights: Dict[str, float],
                           business_context: str,
                           quality_multipliers: Optional[Dict[SignalQualityEnum, float]] = None,
                           minimum_domain_scores: Optional[Dict[str, float]] = None,
                           created_by: str = "user") -> WeightConfiguration:
        """Create a new weight configuration."""
        
        # Validate weights sum to 1.0
        total_weight = sum(domain_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Domain weights must sum to 1.0, got {total_weight}")
        
        # Use default quality multipliers if not provided
        if quality_multipliers is None:
            quality_multipliers = {
                SignalQualityEnum.HIGH: 1.0,
                SignalQualityEnum.MEDIUM: 0.8,
                SignalQualityEnum.LOW: 0.6,
                SignalQualityEnum.UNKNOWN: 0.4
            }
        
        config = WeightConfiguration(
            config_id=f"config_{job_family.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            job_family=job_family,
            business_context=business_context,
            domain_weights=domain_weights,
            quality_multipliers=quality_multipliers,
            minimum_domain_scores=minimum_domain_scores or {},
            created_by=created_by,
            created_at=datetime.utcnow(),
            is_active=True,
            version="1.0"
        )
        
        # Store configuration
        self.configurations[config.config_id] = config
        self._save_configurations()
        
        return config
    
    def update_configuration(self, config_id: str,
                           domain_weights: Optional[Dict[str, float]] = None,
                           business_context: Optional[str] = None,
                           quality_multipliers: Optional[Dict[SignalQualityEnum, float]] = None,
                           minimum_domain_scores: Optional[Dict[str, float]] = None,
                           updated_by: str = "user") -> Optional[WeightConfiguration]:
        """Update an existing weight configuration."""
        
        config = self.configurations.get(config_id)
        if not config:
            return None
        
        # Update fields if provided
        if domain_weights:
            total_weight = sum(domain_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError(f"Domain weights must sum to 1.0, got {total_weight}")
            config.domain_weights = domain_weights
        
        if business_context:
            config.business_context = business_context
        
        if quality_multipliers:
            config.quality_multipliers = quality_multipliers
        
        if minimum_domain_scores:
            config.minimum_domain_scores = minimum_domain_scores
        
        # Update version and metadata
        config.version = str(float(config.version) + 0.1)
        config.created_at = datetime.utcnow()  # Update as last modified
        
        # Save updated configuration
        self._save_configurations()
        
        return config
    
    def deactivate_configuration(self, config_id: str, deactivated_by: str = "user") -> bool:
        """Deactivate a weight configuration."""
        
        config = self.configurations.get(config_id)
        if not config:
            return False
        
        config.is_active = False
        self._save_configurations()
        
        return True
    
    def get_all_configurations(self, job_family: Optional[JobFamilyEnum] = None,
                             active_only: bool = True) -> List[WeightConfiguration]:
        """Get all weight configurations, optionally filtered by job family."""
        
        configurations = []
        
        for config in self.configurations.values():
            if job_family and config.job_family != job_family:
                continue
            
            if active_only and not config.is_active:
                continue
            
            configurations.append(config)
        
        # Sort by creation date (newest first)
        configurations.sort(key=lambda x: x.created_at, reverse=True)
        
        return configurations
    
    def get_configuration_stats(self, job_family: Optional[JobFamilyEnum] = None) -> Dict[str, Any]:
        """Get statistics about weight configurations."""
        
        configurations = self.get_all_configurations(job_family, active_only=False)
        
        stats = {
            "total_configurations": len(configurations),
            "active_configurations": len([c for c in configurations if c.is_active]),
            "inactive_configurations": len([c for c in configurations if not c.is_active]),
            "job_families": {},
            "average_version": 0.0,
            "most_recent_update": None
        }
        
        if not configurations:
            return stats
        
        # Job family distribution
        family_counts = {}
        for config in configurations:
            family = config.job_family.value
            family_counts[family] = family_counts.get(family, 0) + 1
        
        stats["job_families"] = family_counts
        
        # Average version
        versions = [float(c.version) for c in configurations]
        stats["average_version"] = sum(versions) / len(versions)
        
        # Most recent update
        most_recent = max(configurations, key=lambda x: x.created_at)
        stats["most_recent_update"] = most_recent.created_at.isoformat()
        
        return stats
    
    def export_configuration(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Export a configuration for backup or sharing."""
        
        config = self.configurations.get(config_id)
        if not config:
            return None
        
        export_data = {
            "configuration": config.model_dump(),
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": "weight_manager"
        }
        
        return export_data
    
    def import_configuration(self, export_data: Dict[str, Any], 
                           imported_by: str = "user") -> Optional[WeightConfiguration]:
        """Import a configuration from export data."""
        
        try:
            config_data = export_data.get("configuration")
            if not config_data:
                return None
            
            # Create new configuration with imported data
            config = WeightConfiguration(**config_data)
            
            # Generate new ID to avoid conflicts
            config.config_id = f"imported_{config.job_family.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            config.created_at = datetime.utcnow()
            config.version = "1.0"  # Reset version for import
            
            # Store imported configuration
            self.configurations[config.config_id] = config
            self._save_configurations()
            
            return config
            
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return None
