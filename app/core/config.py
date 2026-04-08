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
    geocoding_base_url: str = "http://geocoding-service:8000"
    geocoding_lookup_path: str = "/api/geocode"
    geocoding_timeout_seconds: float = 5.0
    driver_service_base_url: str = "http://driver-service:8000"
    driver_service_drivers_path: str = "/api/drivers"
    driver_service_timeout_seconds: float = 5.0
    driver_service_enable_dev_fallback: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
