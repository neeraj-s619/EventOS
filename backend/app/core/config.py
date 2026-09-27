from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os


class Settings(BaseSettings):
    app_name: str = "EVENTOS"
    app_version: str = "0.2.0"
    debug: bool = True
    
    database_url: str = "sqlite:///./eventos.db"
    
    # WhatsApp Cloud API & Integration Configuration
    whatsapp_enabled: bool = False
    whatsapp_mode: str = "sandbox"  # "disabled", "sandbox", "cloud"
    whatsapp_api_url: str = "https://graph.facebook.com"
    whatsapp_api_version: str = "v20.0"
    whatsapp_access_token: Optional[str] = None
    whatsapp_token: Optional[str] = None  # Backward-compatible alias
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    whatsapp_verify_token: str = "eventos_webhook_verify_token"
    whatsapp_app_secret: Optional[str] = None
    whatsapp_webhook_path: str = "/api/v1/whatsapp/webhook"
    whatsapp_auto_confirm: bool = False  # false = 2-step confirmation; true = direct auto-update
    
    # Telegram Operations Network Configuration (Two Bots Architecture)
    telegram_enabled: bool = True
    telegram_bot_token: Optional[str] = None  # Legacy / fallback staff bot token
    telegram_visitor_bot_token: Optional[str] = None
    telegram_visitor_bot_username: str = "eventos_visitor_bot"
    telegram_staff_bot_token: Optional[str] = None
    telegram_staff_bot_username: str = "hckathn_bot"
    telegram_mode: str = "polling"  # "polling", "webhook", "disabled"
    telegram_webhook_url: Optional[str] = None
    telegram_webhook_secret: Optional[str] = None
    telegram_poll_interval: float = 2.0
    telegram_webhook_path: str = "/api/v1/telegram/webhook"
    telegram_bot_username: str = "hckathn_bot"
    
    simulation_enabled: bool = True
    simulation_interval_seconds: int = 30
    
    forecast_horizon_minutes: int = 30
    forecast_interval_minutes: int = 10
    
    risk_thresholds: dict = {
        "normal_max": 70.0,
        "watch_max": 85.0,
        "warning_max": 95.0,
        "critical_max": 100.0
    }

    # Nugen Domain-Aligned AI Configuration (HackCelestial 3.0 Task 2)
    nugen_api_key: Optional[str] = None
    nugen_model_id: str = "nugen-aligned-eventos-v1"
    nugen_base_model: str = "nugen-base-v1"
    nugen_api_url: str = "https://api.nugen.in"
    nugen_enabled: bool = True
    nugen_mode: str = "auto"  # "auto" (live if key present, else degraded), "live", "mock", "degraded"
    nugen_timeout_seconds: float = 12.0
    nugen_temperature: float = 0.2
    nugen_alignment_name: str = "eventos_domain_alignment_v1"

    def is_nugen_configured(self) -> bool:
        return bool(self.nugen_enabled and self.nugen_api_key and len(self.nugen_api_key.strip()) > 5)

    def get_nugen_mode(self) -> str:
        if not self.nugen_enabled:
            return "degraded"
        mode = (self.nugen_mode or "auto").lower()
        if mode == "mock":
            return "mock"
        if mode == "live" or (mode == "auto" and self.is_nugen_configured()):
            return "live"
        return "degraded"

    def get_access_token(self) -> Optional[str]:
        return self.whatsapp_access_token or self.whatsapp_token

    def get_verify_token(self) -> str:
        return self.whatsapp_verify_token or "eventos_webhook_verify_token"

    def get_effective_mode(self) -> str:
        """
        Determines current operational mode:
        - 'disabled': explicitly disabled
        - 'cloud': enabled with valid access token and phone number ID
        - 'sandbox': development / test mode with simulated webhook receiver
        """
        mode = (self.whatsapp_mode or "sandbox").lower()
        if mode == "disabled" or (not self.whatsapp_enabled and mode not in ["sandbox", "cloud"]):
            return "disabled"
        if mode == "cloud":
            if self.get_access_token() and self.whatsapp_phone_number_id:
                return "cloud"
            return "cloud_unconfigured"
        return "sandbox"

    def is_cloud_ready(self) -> bool:
        return bool((self.whatsapp_enabled or self.whatsapp_mode == "cloud") and self.get_access_token() and self.whatsapp_phone_number_id)

    def get_staff_bot_token(self) -> Optional[str]:
        """Returns configured Staff / Ops Bot token, falling back to legacy TELEGRAM_BOT_TOKEN."""
        return self.telegram_staff_bot_token or self.telegram_bot_token

    def get_visitor_bot_token(self) -> Optional[str]:
        """Returns configured Visitor Bot token."""
        return self.telegram_visitor_bot_token

    def is_staff_bot_configured(self) -> bool:
        t = self.get_staff_bot_token()
        return bool(self.telegram_enabled and t and len(t.strip()) > 5)

    def is_visitor_bot_configured(self) -> bool:
        t = self.get_visitor_bot_token()
        return bool(self.telegram_enabled and t and len(t.strip()) > 5)

    def is_telegram_configured(self) -> bool:
        return bool(self.is_staff_bot_configured() or self.is_visitor_bot_configured())

    def get_telegram_mode(self) -> str:
        if not self.telegram_enabled:
            return "disabled"
        if not self.is_telegram_configured():
            return "sandbox"
        mode = (self.telegram_mode or "polling").lower()
        if mode in ["webhook", "polling"]:
            return mode
        return "polling"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()