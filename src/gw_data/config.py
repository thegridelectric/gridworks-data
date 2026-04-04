from typing import Optional
from pydantic import ConfigDict, SecretStr
from pydantic_settings import BaseSettings

DEFAULT_ENV_FILE = ".env"

class Settings(BaseSettings):
    db_url: SecretStr = SecretStr(
        "postgresql+psycopg://gw_admin@localhost:5432/gridworks"
    )
    log_level: str = "INFO"
    log_dir: str = "~/.local/state/gridworks/gw_data/log"
    db_echo: bool = False

    model_config = ConfigDict(
        env_prefix="gw_data_",
        env_nested_delimiter="__",
        extra="ignore",
    )