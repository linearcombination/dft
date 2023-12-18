import os
import re
import shutil
import sys
import urllib
from contextlib import closing
from itertools import zip_longest
from os.path import basename, join, sep
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence, TypeVar
from urllib.request import urlopen

from document.config import settings
from document.domain import model, parsing, resource_lookup
from document.domain.model import USFMBook
from document.utils.file_utils import (
    delete_tree,
    load_json_object,
    source_file_needs_update,
)
from god_the_father_terms import gtf_terms_table
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import HttpUrl
from son_of_god_terms import sog_terms_table

logger = settings.logger(__name__)

T = TypeVar("T")


def resource_types_and_names_for_lang(
    lang_code: str,
    working_dir: str = settings.RESOURCE_ASSETS_DIR,
    english_resource_type_map: Mapping[str, str] = settings.ENGLISH_RESOURCE_TYPE_MAP,
    id_resource_type_map: Mapping[str, str] = settings.ID_RESOURCE_TYPE_MAP,
    translations_json_location: HttpUrl = settings.TRANSLATIONS_JSON_LOCATION,
    all_usfm_resource_types: Sequence[str] = settings.ALL_USFM_RESOURCE_TYPES,
    all_tn_resource_types: Sequence[str] = settings.ALL_TN_RESOURCE_TYPES,
    all_tq_resource_types: Sequence[str] = settings.ALL_TQ_RESOURCE_TYPES,
    all_tw_resource_types: Sequence[str] = settings.ALL_TW_RESOURCE_TYPES,
    bc_resource_types: Sequence[str] = settings.BC_RESOURCE_TYPES,
) -> Sequence[tuple[str, str]]:
    """
    Get all resource type, name tuples for a given language available
    through API.
    """
    logger.debug("About to get resource types and names for lang: %s", lang_code)
    if lang_code == "en":
        return [(key, value) for key, value in english_resource_type_map.items()]
    if lang_code == "id":
        return [(key, value) for key, value in id_resource_type_map.items()]
    data = resource_lookup.fetch_source_data(
        working_dir, str(translations_json_location)
    )
    values = []
    items = [lang for lang in data if lang["code"] == lang_code]
    item = items[0] if items else None
    # for item in [lang for lang in data if lang["code"] == lang_code]:
    if item:
        values = [
            (
                resource_type["code"],
                "{} ({})".format(
                    resource_type["name"] if "name" in resource_type else "",
                    resource_type["code"],
                ),
            )
            for resource_type in item["contents"]
            if (
                resource_type["code"]
                in [
                    *all_usfm_resource_types,
                    *all_tn_resource_types,
                    *all_tq_resource_types,
                    *all_tw_resource_types,
                    *bc_resource_types,
                ]
            )
        ]
    return sorted(values, key=lambda value: value[0])


def log_event(context: dict[str, T]) -> None:
    logger.debug(context)


def delete_asset(resource_dir: str, dir_to_preserve: str = "temp") -> None:
    parent_dir = str(Path(resource_dir).parent.absolute())
    if Path(parent_dir).name != dir_to_preserve:
        delete_tree(parent_dir)
    elif Path(resource_dir).name != dir_to_preserve:
        delete_tree(resource_dir)


# @app.get("/dft_table/{lang_code}")
# async def dft_table(lang_code: str) -> JSONResponse:
#     pass


def main() -> Iterable[list[str]]:
    """
    Check heart language USFM assets.

    Usage:
    >>> #list(main())
    """
    # For each HL language
    for lang_code_and_name in [
        lang_code_and_name
        for lang_code_and_name in resource_lookup.lang_codes_and_names()
        if not lang_code_and_name[2]
    ]:
        associated_gl_lang_code = associated_gateway_language_for_heart_language(
            lang_code_and_name[0]
        )
        yield dfts_for_language(lang_code_and_name, associated_gl_lang_code)


def associated_gateway_language_for_heart_language(
    lang_code: str,
    data_api_url: str = "https://api.bibleineverylanguage.org/v1/graphql",
    graphql_query: str = """query GetGatewayLanguage {
          language(where: {ietf_code: {_eq: "foo"}}) {
            ietf_code
            english_name
            languagesToLanguagesByGatewayLanguageToIetf {
              gateway_language_ietf
              language {
                english_name
              }
            }
          }
        }
        """,
) -> Optional[str]:
    """
    >>> associated_gateway_language_for_heart_language("aob")
    'tpi'
    """
    # Select your transport with a defined url endpoint
    transport = AIOHTTPTransport(url=data_api_url)

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Provide a GraphQL query
    # params = {"heartLangCode": lang_code}
    # TODO Formatting graphql strings is a bit of pain, this approach works.
    query = gql(re.sub("foo", lang_code, graphql_query))
    # result = client.execute(query, variable_values=params)
    result = client.execute(query)
    gl_lang_code = None
    try:
        gl_lang_code = result["language"][0][
            "languagesToLanguagesByGatewayLanguageToIetf"
        ][0]["gateway_language_ietf"]
    except:
        logger.exception("Failed due to the following exception")
    return gl_lang_code


def usfm_books(
    book_codes: list[str],
    usfm_resource_types_and_names: list[tuple[str, str]],
    lang_code: str,
) -> list[USFMBook]:
    usfm_books = []
    for book_code in book_codes:
        for usfm_resource_type_and_name in usfm_resource_types_and_names:
            resource_lookup_dto = resource_lookup.usfm_resource_lookup(
                lang_code,
                usfm_resource_type_and_name[0],
                book_code,
            )
            resource_dir = resource_lookup.provision_asset_files(resource_lookup_dto)
            try:
                # Reify the content
                usfm_book = parsing.usfm_book_content(
                    resource_lookup_dto, resource_dir, False
                )
            except:
                logger.exception("Failed due to the following exception")
            else:
                usfm_books.append(usfm_book)
    return usfm_books


def dfts_for_language(
    hl_lang_code_and_name: tuple[str, str, bool],
    gl_lang_code: Optional[str] = None,
    usfm_resource_types: Sequence[str] = settings.USFM_RESOURCE_TYPES,
    gl_usfm_resource_types: Sequence[str] = settings.ALL_USFM_RESOURCE_TYPES,
    column_labels: str = "Verse Reference, GL (from DOC), HL (from DOC), Backtranslate HL to GL via Chatgpt, Comments\n",
) -> list[str]:
    """
    Produce table of output showing Divine Familial Terms table for
    the requested language.

    Usage:
    >>> #dfts_for_language(("tpi", "Tok Pisin"), "aob")
    >>> dfts_for_language(("tpi", "Tok Pisin"), "en")
    """
    output_table: list[str] = []
    output_table.append(column_labels)
    logger.debug("About to get data for heart language: %s", hl_lang_code_and_name)
    logger.debug("About to get data for gateway language: %s", gl_lang_code)
    # Get book codes for language and filter book codes to only
    # those that are referenced in the gtf_terms_table
    hl_book_codes = [
        book_code[0]
        for book_code in resource_lookup.book_codes_for_lang(hl_lang_code_and_name[0])
        if book_code[0] in gtf_terms_table.keys()
    ]
    gl_book_codes = []
    gl_usfm_books: list[USFMBook] = []
    if gl_lang_code:
        gl_book_codes = [
            book_code[0]
            for book_code in resource_lookup.book_codes_for_lang(gl_lang_code)
            if book_code[0] in gtf_terms_table.keys()
        ]
        gl_usfm_resource_types_and_names = [
            resource_type_and_name
            for resource_type_and_name in resource_types_and_names_for_lang(
                gl_lang_code
            )
            if resource_type_and_name[0] in gl_usfm_resource_types
        ]
        gl_usfm_books = usfm_books(
            gl_book_codes, gl_usfm_resource_types_and_names, gl_lang_code
        )
    # Could be more than one USFM type per language, e.g., ulb and f10
    # For each USFM type associated with the language
    hl_usfm_resource_types_and_names = [
        resource_type_and_name
        for resource_type_and_name in resource_types_and_names_for_lang(
            hl_lang_code_and_name[0]
        )
        if resource_type_and_name[0] in usfm_resource_types
    ]
    hl_usfm_books = usfm_books(
        hl_book_codes, hl_usfm_resource_types_and_names, hl_lang_code_and_name[0]
    )
    for hl_usfm_book, gl_usfm_book in zip_longest(hl_usfm_books, gl_usfm_books):
        # Get the chapter/verses lists from the gtf_terms_table for the current book
        hl_gtf_chapters = (
            gtf_terms_table[hl_usfm_book.book_code] if hl_usfm_book else {}
        )
        gl_gtf_chapters = (
            gtf_terms_table[gl_usfm_book.book_code] if gl_usfm_book else {}
        )
        for (hl_gtf_chapter_num, hl_gtf_verse_nums), (
            gl_gtf_chapter_num,
            gl_gtf_verse_nums,
        ) in zip_longest(hl_gtf_chapters.items(), gl_gtf_chapters.items()):
            for hl_verse_num, gl_verse_num in zip_longest(
                hl_gtf_verse_nums, gl_gtf_verse_nums
            ):
                hl_verse = (
                    hl_usfm_book.chapters[hl_gtf_chapter_num].verses[str(hl_verse_num)]
                    if hl_usfm_book
                    and hl_gtf_chapter_num in hl_usfm_book.chapters.keys()
                    and str(hl_verse_num)
                    in hl_usfm_book.chapters[hl_gtf_chapter_num].verses.keys()
                    else ""
                )
                gl_verse = (
                    gl_usfm_book.chapters[gl_gtf_chapter_num].verses[str(gl_verse_num)]
                    if gl_usfm_book
                    and gl_gtf_chapter_num in gl_usfm_book.chapters.keys()
                    and str(gl_verse_num)
                    in gl_usfm_book.chapters[gl_gtf_chapter_num].verses.keys()
                    else ""
                )
                output_table.append(
                    # The last column in the row is the empty comments column
                    (
                        f"{hl_usfm_book.book_code} {hl_gtf_chapter_num}:{hl_verse_num},"
                        f"{gl_verse}, {hl_verse}, chatgpt backtranslate output goes here, \n"
                    )
                )
    return output_table


if __name__ == "__main__":

    # To run the doctests in the this module, in the root of the project do:
    # FROM_EMAIL_ADDRESS=... python backend/usfm_checker.py
    # See https://docs.python.org/3/library/doctest.html
    # for more details.
    import doctest

    doctest.testmod()
