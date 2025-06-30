import yaml
import os
from typing import Dict, Optional

class ServiceManager:
    def __init__(self, services_config_path: str = 'config/services.yaml'):
        self.services_config_path = services_config_path
        self.services = self._load_services()
    
    def _load_services(self) -> Dict:
        """Load services configuration from YAML file"""
        try:
            with open(self.services_config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                return config.get('services', {})
        except FileNotFoundError:
            print(f"Warning: Services config file not found at {self.services_config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing services config: {e}")
            return {}
    
    def get_service_duration_minutes(self, service_name: str) -> int:
        """Get the duration in minutes for a given service"""
        # Normalize service name for lookup
        service_key = self._normalize_service_name(service_name)
        
        if service_key in self.services:
            return self.services[service_key].get('duration_minutes', 60)
        
        # Try to find by partial match
        for key, service in self.services.items():
            if service_name.lower() in key.lower() or key.lower() in service_name.lower():
                return service.get('duration_minutes', 60)
        
        # Default duration if service not found
        return 60
    
    def get_service_price(self, service_name: str) -> Optional[float]:
        """Get the price for a given service"""
        service_key = self._normalize_service_name(service_name)
        
        if service_key in self.services:
            return self.services[service_key].get('price')
        
        # Try to find by partial match
        for key, service in self.services.items():
            if service_name.lower() in key.lower() or key.lower() in service_name.lower():
                return service.get('price')
        
        return None
    
    def get_service_info(self, service_name: str) -> Optional[Dict]:
        """Get complete service information"""
        service_key = self._normalize_service_name(service_name)
        
        if service_key in self.services:
            return self.services[service_key]
        
        # Try to find by partial match
        for key, service in self.services.items():
            if service_name.lower() in key.lower() or key.lower() in service_name.lower():
                return service
        
        return None
    
    def get_all_services(self) -> Dict:
        """Get all available services"""
        return self.services
    
    def get_services_summary(self) -> str:
        """Get a formatted string of all services for display"""
        summary_parts = []
        for key, service in self.services.items():
            name = service.get('name', key.title())
            price = service.get('price', 'N/A')
            duration = service.get('duration_minutes', 60)
            summary_parts.append(f"{name} (R${price}, {duration}min)")
        
        return ", ".join(summary_parts)
    
    def _normalize_service_name(self, service_name: str) -> str:
        """Normalize service name for consistent lookup"""
        if not service_name:
            return ""
        
        # Convert to lowercase and remove common variations
        normalized = service_name.lower().strip()
        
        # Map common variations to standard keys
        variations = {
            'corte de cabelo': 'corte',
            'corte': 'corte',
            'barba': 'barba',
            'fazer barba': 'barba',
            'corte + barba': 'combo',
            'combo': 'combo',
            'sobrancelha': 'sobrancelha',
            'sobrancelhas': 'sobrancelha'
        }
        
        return variations.get(normalized, normalized) 