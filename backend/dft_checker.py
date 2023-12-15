import os
import shutil
import sys
import urllib
from contextlib import closing
from os.path import basename, join, sep
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TypeVar
from urllib.request import urlopen

from document.config import settings
from document.domain import model, parsing, resource_lookup
from document.utils.file_utils import (
    delete_tree,
    load_json_object,
    source_file_needs_update,
)
from pydantic import HttpUrl

from god_the_father_terms import gtf_terms_table
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
    Convenience method that can be called from UI to get the set
    of all resource type, name tuples for a given language available
    through API. Presumably this could be called to populate a
    drop-down menu or as an API method.
    """
    if lang_code == "en":
        return [(key, value) for key, value in english_resource_type_map.items()]
    if lang_code == "id":
        return [(key, value) for key, value in id_resource_type_map.items()]
    data = resource_lookup.fetch_source_data(
        working_dir, str(translations_json_location)
    )
    for item in [lang for lang in data if lang["code"] == lang_code]:
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
    >>> #main()
    """
    # For each HL language
    for lang_code_and_name in [
        lang_code_and_name
        for lang_code_and_name in resource_lookup.lang_codes_and_names()
        if not lang_code_and_name[2]
    ]:
        yield dfts_for_language(lang_code_and_name)


def dfts_for_language(
    lang_code_and_name: tuple[str, str, bool],
    usfm_resource_types: Sequence[str] = settings.USFM_RESOURCE_TYPES,
) -> list[str]:
    """
    Produce table of output showing dfts for language

    Usage:
    >>> dfts_for_language(("auh", "Aushi"))
    """
    output_table: list[str] = []
    output_table.append(
        "Verse Reference, GL (from DOC), HL (from DOC), Backtranslate HL to GL via Chatgpt, Comments\n"
    )
    # logger.debug("About to get data for language: %s", lang_code_and_name)

    # Get book codes for language and filter book codes to only
    # those that are referenced in the gtf_terms_table
    for book_code in [
        book_code
        for book_code in resource_lookup.book_codes_for_lang(lang_code_and_name[0])
        if book_code[0] in gtf_terms_table.keys()
    ]:
        # Could be more than one USFM type per language, e.g., ulb and f10
        # For each USFM type associated with the language
        for usfm_resource_type_and_name in [
            resource_type_and_name
            for resource_type_and_name in resource_types_and_names_for_lang(
                lang_code_and_name[0]
            )
            if resource_type_and_name[0] in usfm_resource_types
        ]:
            # FIXME usfm_resource_lookup uses translations.json to find lookup info.
            # Bear in mind that if we are working with mirrored repos that are not
            # in translations.json this is a chicken before the egg situation.
            # However, if we find the issue in the repo pointed to by
            # translations.json then we can subsequently lookup its mirrored repo
            # using some reliable URL naming pattern and make changes on the
            # mirrored repo.
            resource_lookup_dto = resource_lookup.usfm_resource_lookup(
                lang_code_and_name[0],
                usfm_resource_type_and_name[0],
                book_code[0],
            )
            # FIXME Some assets will not be git repos, for those that are zip files we can
            # at least find issues. We would need to determine the git repo where
            # the zips are coming from in order to see if that repo was mirrored so
            # that we could clone and make changes there.
            resource_dir = resource_lookup.provision_asset_files(resource_lookup_dto)
            try:
                # Reify the content
                usfm_book = parsing.usfm_book_content(
                    resource_lookup_dto, resource_dir, False
                )
                # Get the chapter/verses lists from the gtf_terms_table for the current book
                gtf_chapters = gtf_terms_table[usfm_book.book_code]
                # For each chapter/verses list
                for gtf_chapter_num, gtf_verse_nums in gtf_chapters.items():
                    # For each verse in verse list
                    for verse_num in gtf_verse_nums:
                        # Add a row of columns to the output table
                        output_table.append(
                            # The last column in the row is the empty comments column
                            f"{book_code[1]} {gtf_chapter_num}:{verse_num}, {usfm_book.chapters[gtf_chapter_num].verses[str(verse_num)]}, chatgpt backtranslate output goes here, \n"
                        )
            except:
                logger.exception("Failed due to the following exception")
    return output_table


if __name__ == "__main__":

    # To run the doctests in the this module, in the root of the project do:
    # FROM_EMAIL_ADDRESS=... python backend/usfm_checker.py
    # See https://docs.python.org/3/library/doctest.html
    # for more details.
    import doctest

    doctest.testmod()
