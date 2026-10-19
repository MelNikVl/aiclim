from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_mode: Literal["demo", "live"] = "demo"
    qloo_api_key: SecretStr = SecretStr("")
    # Restrict outbound requests to the documented event host. No user URLs.
    qloo_base_url: Literal["https://hackathon.api.qloo.com"] = "https://hackathon.api.qloo.com"
    qloo_global_request_limit: int = Field(default=500, ge=1, le=10000)
    qloo_scenario_request_limit: int = Field(default=10, ge=1, le=10)
    qloo_timeout_seconds: float = Field(default=8, ge=0.1, le=20)
    rate_limit_per_minute: int = Field(default=40, ge=1, le=200)
    app_secret: SecretStr = SecretStr("")
    llm_provider: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_live_key(self):
        if self.data_mode == "live" and not self.qloo_api_key.get_secret_value().strip():
            raise ValueError("DATA_MODE=live requires a server-side QLOO_API_KEY")
        if self.app_secret.get_secret_value() and len(self.app_secret.get_secret_value()) < 32:
            raise ValueError("APP_SECRET must contain at least 32 characters")
        return self
