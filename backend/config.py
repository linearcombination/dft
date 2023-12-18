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
class Settings(BaseSettings):
    """
    BaseSettings subclasses like this one allow values of constants to
    be overridden by environment variables like those defined in env
    files, e.g., ../../.env or by system level environment variables
    (which have higher priority).
    """

    # REPO_URL_DICT_KEY: str = "../download-scripture?repo_url"
    # ALT_REPO_URL_DICT_KEY: str = "/download-scripture?repo_url"

    # The location where the JSON data file that we use to lookup
    # location of resources is located.
    TRANSLATIONS_JSON_LOCATION: HttpUrl
    # The jsonpath format string for the resource's git repo for a given language, resource type, and book.
    RESOURCE_DOWNLOAD_FORMAT_JSONPATH: str = "$[?code='{}'].contents[?code='{}'].subcontents[?code='{}'].links[?format='Download'].url"
    # All resource types.
    # The jsonpath format string for resource types for a given language.
    # jsonpath for all resource codes.
    # jsonpath format string for all resource codes for a given language.
    RESOURCE_CODES_FOR_LANG_JSONPATH: str = (
        "$[?code='{}'].contents[*].subcontents[*].code"
    )
    # The jsonpath format string for individual USFM files (per bible book) for a given language, resource type, and book.
    INDIVIDUAL_USFM_URL_JSONPATH: str = "$[?code='{}'].contents[?code='{}'].subcontents[?code='{}'].links[?format='usfm'].url"
    # The jsonpath format string for resource URL for a given lanaguage and resource type.
    RESOURCE_URL_LEVEL1_JSONPATH: str = (
        "$[?code='{}'].contents[?code='{}'].links[?format='zip'].url"
    )
    # The jsonpath format string for a given language's name.
    RESOURCE_LANG_NAME_JSONPATH: str = "$[?code='{}'].name"
    # The jsonpath format string to the resource type's name for a given language and resource type.
    RESOURCE_TYPE_NAME_JSONPATH: str = "$[?code='{}'].contents[?code='{}'].name"
    # The jsonpath format string for a zip URL for a given language and resource code.
    RESOURCE_URL_LEVEL2_JSONPATH: str = (
        "$[?code='{}'].contents[*].subcontents[?code='{}'].links[?format='zip'].url"
    )
    USFM_RESOURCE_TYPES: Sequence[str] = [
        "ayt",
        "cuv",
        "f10",
        "nav",
        "reg",
        # "udb", # 2023-06-20 Content team doesn't want this used.
        # "udb-wa", # 2022-05-12 - Content team doesn't want this used.
        "ugnt",
        # "uhb", # parser blows on: AttributeError: 'SingleHTMLRenderer' object has no attribute 'renderCAS'
        "ulb",
        "usfm",
    ]
    # f10 for fr, and udb for many other languages are secondary USFM types,
    # meaning: for those languages that have them those same languages have
    # a primary USFM type such as ulb (there can be other primary USFM types
    # besides ulb such as cuv, reg, nav, etc.). For v1, we only allow use of
    # a primary USFM type since v1 has a requirement that the user is not to
    # choose resource types in the UI, so we use this next list to manage
    # that when we automatically choose the reesource types (from the USFM
    # and TN resource types that translations.json lists as available) for
    # the GL languages and books chosen.
    EN_USFM_RESOURCE_TYPES: Sequence[str] = ["ulb-wa"]
    TN_RESOURCE_TYPES: Sequence[str] = ["tn"]
    EN_TN_RESOURCE_TYPES: Sequence[str] = ["tn-wa"]
    TQ_RESOURCE_TYPES: Sequence[str] = ["tq"]
    EN_TQ_RESOURCE_TYPES: Sequence[str] = ["tq-wa"]
    TW_RESOURCE_TYPES: Sequence[str] = ["tw"]
    EN_TW_RESOURCE_TYPES: Sequence[str] = ["tw-wa"]
    BC_RESOURCE_TYPES: Sequence[str] = ["bc-wa"]

    def logger(self, name: str) -> logging.Logger:
        """
        Return a Logger for scope named by name, e.g., module, that can be
        used for logging.
        """
        with open(self.LOGGING_CONFIG_FILE_PATH, "r") as fin:
            logging_config = yaml.safe_load(fin.read())
            lc.dictConfig(logging_config)
        return logging.getLogger(name)

    API_LOCAL_PORT: int

    LOGGING_CONFIG_FILE_PATH: str = "backend/logging_config.yaml"

    # Location where resource assets will be downloaded.
    RESOURCE_ASSETS_DIR: str = "working/temp"

    # Location where generated PDFs will be written to.
    DOCUMENT_OUTPUT_DIR: str = "working/output"

    # Location where generated PDFs will be written to.
    DOCUMENT_SERVE_DIR: str = "document_output"

    # For options see https://wkhtmltopdf.org/usage/wkhtmltopdf.txt

    # Return the message to show to user on successful generation of
    # PDF.
    # SUCCESS_MESSAGE: str = "Success! Please retrieve your generated document using a GET REST request to /pdf/{document_request_key} or /epub/{document_request_key} or /docx/{document_request_key} (depending on whether you requested PDF, ePub, or Docx result) where document_request_key is the finished_document_request_key in this payload."

    BACKEND_CORS_ORIGINS: list[str]

    # Return the file names, excluding suffix, of files that do not
    # contain content but which may be in the same directory or
    # subdirectories of a resource's acquired files.

    ENGLISH_GIT_REPO_MAP: Mapping[str, str] = {
        "ulb-wa": "https://content.bibletranslationtools.org/WycliffeAssociates/en_ulb",
        "udb-wa": "https://content.bibletranslationtools.org/WycliffeAssociates/en_udb",
        "tn-wa": "https://content.bibletranslationtools.org/WycliffeAssociates/en_tn",
        "tw-wa": "https://content.bibletranslationtools.org/WycliffeAssociates/en_tw",
        "tq-wa": "https://content.bibletranslationtools.org/WycliffeAssociates/en_tq",
        "bc-wa": "https://content.bibletranslationtools.org/WycliffeAssociates/en_bc",
    }
    ID_GIT_REPO_MAP: Mapping[str, str] = {
        "ayt": "https://content.bibletranslationtools.org/WA-Catalog/id_ayt",
        "tn": "https://content.bibletranslationtools.org/WA-Catalog/id_tn",
        "tq": "https://content.bibletranslationtools.org/WA-Catalog/id_tq",
        "tw": "https://content.bibletranslationtools.org/WA-Catalog/id_tw",
    }

    ENGLISH_RESOURCE_TYPE_MAP: Mapping[str, str] = {
        "ulb-wa": "Unlocked Literal Bible (ULB)",
        # "udb-wa": "Unlocked Dynamic Bible (UDB)",
        "tn-wa": "ULB Translation Notes",
        "tq-wa": "ULB Translation Questions",
        "tw-wa": "ULB Translation Words",
        "bc-wa": "Bible Commentary",
    }

    ID_LANGUAGE_NAME: str = "Bahasa Indonesian"
    ID_RESOURCE_TYPE_MAP: Mapping[str, str] = {
        "ayt": "Bahasa Indonesian Bible (ayt)",
        "tn": "Translation Helps (tn)",
        "tq": "Translation Questions (tq)",
        "tw": "Translation Words (tw)",
    }

    # Return boolean indicating if caching of generated documents should be
    # cached.
    ASSET_CACHING_ENABLED: bool = True
    # Caching window of time in which asset
    # files on disk are considered fresh rather than re-acquiring (in
    # the case of resource asset files) or re-generating them (in the
    # case of the final PDF). In hours.
    ASSET_CACHING_PERIOD: int

    # Provided by .env file:
    EMAIL_SEND_SUBJECT: str
    TO_EMAIL_ADDRESS: EmailStr

    # Provided by system env vars (fake values provided so github action can run):
    FROM_EMAIL_ADDRESS: EmailStr = "foo@example.com"
    SMTP_HOST: str = "https://example.com"
    SMTP_PORT: int = 111
    SMTP_PASSWORD: str = "fakepass"
    SEND_EMAIL: bool = False

    # Used by gunicorn
    PORT: int
    # local image tag for local dev with prod image
    IMAGE_TAG: str

    # Example fake user agent value required by domain host to allow serving
    # files. Other values could possibly work. This value definitely
    # works.
    USER_AGENT: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"

    # Used in assembly_strategy_utils modeule when zero-filling various strings

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# mypy with pydantic v2 doesn't understand that defaults will be picked up from .env file as they had been in v1
settings = Settings()  # type: ignore
# Could also use:
# settings: Settings = Settings.parse_obj({})
# settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
