from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Farm2Fork Delivery Execution Service"
    app_version: str = "0.1.0"
    database_url: str = "postgresql://postgres:password@db:5432/farm2fork"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    customer_module_base_url: str = "http://customer-service:8000"
    customer_module_customer_lookup_path: str = "/api/customers/{customer_id}"
    customer_module_timeout_seconds: float = 5.0
    geocoding_base_url: str = "https://nominatim.openstreetmap.org"
    geocoding_lookup_path: str = "/search"
    geocoding_timeout_seconds: float = 10.0
    geocoding_user_agent: str = "farm2fork-delivery-execution/0.1"
    geocoding_default_country: str = "Canada"
    driver_service_base_url: str = "http://driver-service:8000"
    driver_service_drivers_path: str = "/api/drivers"
    driver_service_timeout_seconds: float = 5.0
    driver_service_enable_dev_fallback: bool = False
    frontend_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    valhalla_base_url: str = "http://valhalla:8002"
    valhalla_timeout_seconds: float = 10.0
    valhalla_enable_routing: bool = False 

    @property
    def frontend_allowed_origins_list(self) -> list[str]:
        """Return normalized browser origins allowed to call the API directly."""

        return [origin.strip() for origin in self.frontend_allowed_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
