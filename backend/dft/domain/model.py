"""
This module provides classes that are used as data transfer objects.
In particular, many of the classes here are subclasses of
pydantic.BaseModel as FastAPI can use these classes to do automatic
validation and JSON serialization.
"""

from enum import Enum
from typing import Any, NamedTuple, Optional, Sequence, Union, final

# from document.config import settings

# from document.domain.bible_books import BOOK_NAMES
# from document.utils.number_utils import is_even
# from docx import Document  # type: ignore
# from more_itertools import all_equal
from pydantic import BaseModel, EmailStr

# from pydantic.functional_validators import model_validator
from toolz import itertoolz  # type: ignore

# These type aliases give us more self-documenting code, but of course
# aren't strictly necessary.
# HtmlContent = str


# @final
# class ChunkSizeEnum(str, Enum):
#     """
#     The length of content to burst out at a time when interleaving.
#     E.g., if CHAPTER is chosen as the chunk size then the interleaving will
#     do so in chapter chunks (one chapter of scripture, then one chapter of helps,
#     etc.). This exists because translators want to be able to choose
#     the chunk size of scripture that should be grouped together for the
#     purpose of translational cohesion.

#     * CHAPTER
#       - This enum value signals to make each chunk of interleaved
#         content be one chapter's worth in length.
#     """

#     CHAPTER = "chapter"


# https://blog.meadsteve.dev/programming/2020/02/10/types-at-the-edges-in-python/
# https://pydantic-docs.helpmanual.io/usage/models/
# @final
# class ResourceRequest(BaseModel):
#     """
#     This class is used to encode a request for a resource. A
#     document request composes N of these resource request instances.
#     """

#     lang_code: str
#     resource_type: str
#     book_code: str


@final
class DocumentRequestSourceEnum(str, Enum):
    """
    This class/enum captures the concept of: where did the document
    request originate from?
    """

    UI = "ui"
    TEST = "test"


class DocumentRequestTermsEnum(str, Enum):
    """
    This class/enum captures the type of terms table being requested.
    """

    GTF = "gtf"
    SOG = "sog"


@final
class DocumentRequest(BaseModel):
    """
    This class reifies a document generation request from a client of
    the API.
    """

    email_address: Optional[EmailStr] = None
    # The user can choose whether the result should be formatted to
    # print. When the user selects yes/True to format for print
    # then we'll choose a compact layout that makes sense for their
    # document request.
    # layout_for_print: bool = False
    lang_code: str
    terms: DocumentRequestTermsEnum
    # resource_requests: Sequence[ResourceRequest]
    # Indicate whether PDF should be generated.
    generate_pdf: bool = True
    # Indicate whether ePub should be generated.
    # generate_epub: bool = False
    # Indicate whether Docx should be generated.
    generate_docx: bool = False
    # Indicate where the document request originated from. We default to
    # TEST so that tests don't have to specify and every other client, e.g.,
    # UI, should specify in order for
    # document_generator.select_assembly_layout_kind to produce
    # expected results.
    document_request_source: DocumentRequestSourceEnum = DocumentRequestSourceEnum.TEST

    # @model_validator(mode="after")
    # def ensure_valid_document_request(self) -> Any:
    #     """
    #     See ValueError messages below for the rules we are enforcing.
    #     """

    #     usfm_resource_types = settings.ALL_USFM_RESOURCE_TYPES

    #     non_usfm_resource_types = [
    #         *settings.ALL_TN_RESOURCE_TYPES,
    #         *settings.ALL_TQ_RESOURCE_TYPES,
    #         *settings.ALL_TW_RESOURCE_TYPES,
    #         *settings.BC_RESOURCE_TYPES,
    #     ]
    #     all_resource_types = [*usfm_resource_types, *non_usfm_resource_types]
    #     for resource_request in self.resource_requests:
    #         # Make sure resource_type for every ResourceRequest instance
    #         # is a valid value
    #         if not resource_request.resource_type in all_resource_types:
    #             raise ValueError(
    #                 f"{resource_request.resource_type} is not a valid resource type"
    #             )
    #         # Make sure book_code is a valid value
    #         if not resource_request.book_code in BOOK_NAMES.keys():
    #             raise ValueError(
    #                 f"{resource_request.book_code} is not a valid book code"
    #             )

    #     # Partition USFM resource requests by language
    #     language_groups = itertoolz.groupby(
    #         lambda r: r.lang_code,
    #         filter(
    #             lambda r: r.resource_type in usfm_resource_types,
    #             self.resource_requests,
    #         ),
    #     )
    #     # Get a list of the sorted set of books for each language for later
    #     # comparison.
    #     sorted_book_set_for_each_language = [
    #         sorted({item.book_code for item in value})
    #         for key, value in language_groups.items()
    #     ]

    #     # Get the unique number of languages
    #     number_of_usfm_languages = len(
    #         # set(
    #         [
    #             resource_request.lang_code
    #             for resource_request in self.resource_requests
    #             if resource_request.resource_type in usfm_resource_types
    #         ]
    #         # )
    #     )

    #     return self


# @final
# class Attachment(NamedTuple):
#     """
#     An email attachment.
#     """

#     filepath: str
#     mime_type: tuple[str, str]
