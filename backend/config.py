"""This module provides configuration values used by the application."""
import logging
from collections.abc import Mapping, Sequence
from logging import config as lc
from typing import Optional, final

import yaml
from pydantic import field_validator, AnyHttpUrl, EmailStr, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

HtmlContent = str


@final
class DftSettings(BaseSettings):
    """
    BaseSettings subclasses like this one allow values of constants to
    be overridden by environment variables like those defined in env
    files, e.g., ../../.env or by system level environment variables
    (which have higher priority).
    """

    USE_AI: bool

    model_config = SettingsConfigDict(env_file=".env_dft", case_sensitive=True)


# mypy with pydantic v2 doesn't understand that defaults will be picked up from .env file as they had been in v1
dft_settings = DftSettings()  # type: ignore
