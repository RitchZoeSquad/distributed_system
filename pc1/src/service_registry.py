from enum import Enum
from typing import Dict

class ServiceType(Enum):
    BUSINESS_SEARCH = "business_search"  # PC1
    SERP = "serp"                       # PC2
    PHONE = "phone"                     # PC3
    DOMAIN_EMAIL = "domain_email"       # PC4
    LEAK_CHECK = "leak_check"           # PC4
    SHODAN = "shodan"                   # PC4
    MONITORING = "monitoring"           # PC5

class ServiceRegistry:
    SERVICES = {
        ServiceType.BUSINESS_SEARCH: {"host": "pc1", "port": 8000},
        ServiceType.SERP: {"host": "pc2", "port": 8000},
        ServiceType.PHONE: {"host": "pc3", "port": 8000},
        ServiceType.DOMAIN_EMAIL: {"host": "pc4", "port": 8000},
        ServiceType.LEAK_CHECK: {"host": "pc4", "port": 8001},
        ServiceType.SHODAN: {"host": "pc4", "port": 8002},
        ServiceType.MONITORING: {"host": "pc5", "port": 9090}
    }

    @classmethod
    def get_service_url(cls, service_type: ServiceType) -> str:
        service = cls.SERVICES.get(service_type)
        if not service:
            raise ValueError(f"Unknown service type: {service_type}")
        return f"http://{service['host']}:{service['port']}" 