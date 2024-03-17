import re
from typing import Any, Mapping, Optional, Sequence, TypeVar

from celery import current_task
from docx import Document  # type: ignore
from docxcompose.composer import Composer  # type: ignore
import openai
from bs4 import BeautifulSoup
from dft.config import dft_settings

# from dft.domain import model
from document.config import settings
from document.domain import document_generator, parsing, resource_lookup, worker
from document.domain.bible_books import BOOK_NAMES
from document.domain.model import USFMBook
from document.utils.file_utils import asset_file_needs_update
from document.domain.assembly_strategies_docx import assembly_strategy_utils
from dft.domain.god_the_father_terms import gtf_terms_table
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import HttpUrl, Json
from dft.domain.son_of_god_terms import sog_terms_table
from dft.domain.model import DocumentRequest
from toolz import unique  # type: ignore

logger = settings.logger(__name__)


COLUMN_LABELS: str = "<tr><td>Verse Reference</td><td>GL (from DOC)</td><td>HL (from DOC)</td><td>Backtranslate HL to GL via Chatgpt</td><td>Comments</td></tr>\n"

T = TypeVar("T")


async def lang_codes_and_names(
    # WAITING Needed to download translations.json for other functions where data API is not mature enough yet:
    working_dir: str = settings.RESOURCE_ASSETS_DIR,
    # WAITING Needed to download translations.json for other functions where data API is not mature enough yet:
    translations_json_location: HttpUrl = settings.TRANSLATIONS_JSON_LOCATION,
    lang_code_filter_list: Sequence[str] = settings.LANG_CODE_FILTER_LIST,
    gateway_languages: Sequence[str] = settings.GATEWAY_LANGUAGES,
    data_api_url: str = "https://api.bibleineverylanguage.org/v1/graphql",
    # WAITING WA is going to add an is_gateway attribute eventually so that we
    # don't have to figure out if gateway ourselves
    graphql_query: str = """query MyQuery {
  content(
    where: {wa_content_meta: {status: {_eq: "Primary"}, show_on_biel: {_eq: true}}}
  ) {
    language {
      ietf_code
      english_name
      national_name
    }
  }
}
        """,
) -> Sequence[tuple[str, str, bool]]:
    """
    >>> from document.domain import resource_lookup
    >>> # data = await resource_lookup.lang_codes_and_names2()
    >>> # data[0]
    ('abz', 'Abui', False)
    """

    # WAITING Needed to download translations.json for other functions
    # where data API is not mature enough yet. Remove when data API can
    # fully replace translations.json. For now this will make the app
    # slower.
    # data = fetch_source_data(working_dir, str(translations_json_location))

    # Select your transport with a defined url endpoint
    transport = AIOHTTPTransport(url=data_api_url)

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql(graphql_query)
    data = await client.execute_async(query)
    languages_info = None
    values = []
    try:
        languages_info = data["content"]
        # logger.debug("data['content'][0]: %s", languages_info)
        for language_info in languages_info:
            language = language_info["language"]
            ietf_code = language["ietf_code"]
            english_name = language["english_name"]
            national_name = language["national_name"]
            is_gateway = ietf_code in gateway_languages
            if ietf_code not in lang_code_filter_list:
                if english_name in national_name:
                    logger.debug(
                        "About to add: %s", (ietf_code, national_name, is_gateway)
                    )
                    values.append((ietf_code, national_name, is_gateway))
                else:
                    logger.debug(
                        "About to add: %s",
                        (ietf_code, f"{national_name} ({english_name})", is_gateway),
                    )
                    values.append(
                        (ietf_code, f"{national_name} ({english_name})", is_gateway)
                    )

    except:
        logger.exception("Failed due to the following exception")
    unique_values = unique(values, key=lambda value: value[0])
    # heart_langs = [
    #     unique_value for unique_value in unique_values if not unique_value[2]
    # ]
    # logger.debug("heart_langs: %s", heart_langs)
    return sorted(unique_values, key=lambda value: value[1])


def resource_types_and_names_for_lang(
    lang_code: str,
    working_dir: str = settings.RESOURCE_ASSETS_DIR,
    english_resource_type_map: Mapping[str, str] = settings.ENGLISH_RESOURCE_TYPE_MAP,
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
    # Formatting graphql strings is a bit of pain, using re.sub works.
    query = gql(re.sub("foo", lang_code, graphql_query))
    # result = client.execute(query, variable_values=params)
    result = client.execute(query)
    gl_lang_code = None
    try:
        gl_lang_code = result["language"][0][
            "languagesToLanguagesByGatewayLanguageToIetf"
        ][0]["gateway_language_ietf"]
    except:
        logger.debug(
            "Could not obtain associated gateway language ietf code for %s", lang_code
        )
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
                    resource_lookup_dto, resource_dir, [], False
                )
            except:
                logger.exception("Failed due to the following exception")
            else:
                usfm_books.append(usfm_book)
    return usfm_books


@worker.app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_document(document_request_json: Json[Any]) -> Json[Any]:
    current_task.update_state(state="Receiving request")
    document_request = DocumentRequest.parse_raw(document_request_json)
    logger.debug(
        "document_request: %s",
        document_request,
    )
    lang_code = document_request.lang_code
    terms = document_request.terms
    document_request_key_ = ""
    if terms == "gtf":
        document_request_key_ = document_request_key(
            lang_code, "god_the_father_terms", "pdf"
        )
        gtf_terms_for_language(lang_code, True, document_request_key_)
    elif terms == "sog":
        document_request_key_ = document_request_key(
            lang_code, "son_of_god_terms", "pdf"
        )
        sog_terms_for_language(lang_code, True, document_request_key_)
    return document_request_key_


@worker.app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_docx_document(document_request_json: Json[Any]) -> Json[Any]:
    current_task.update_state(state="Receiving request")
    logger.debug("About to parse document request json...")
    document_request = DocumentRequest.parse_raw(document_request_json)
    logger.debug(
        "document_request: %s",
        document_request,
    )
    lang_code = document_request.lang_code
    terms = document_request.terms
    document_request_key_ = ""
    if terms == "gtf":
        document_request_key_ = document_request_key(
            lang_code, "god_the_father_terms", "docx"
        )
        gtf_terms_for_language(lang_code, True, document_request_key_)
    elif terms == "sog":
        document_request_key_ = document_request_key(
            lang_code, "son_of_god_terms", "docx"
        )
        sog_terms_for_language(lang_code, True, document_request_key_)
    return document_request_key_


def gtf_terms_for_language(
    lang_code: str,
    docx_p: bool,
    document_request_key: str,
    # html_filename_part: str = "god_the_father_terms",
    title2: str = "God the Father Terms",
    column_labels: str = COLUMN_LABELS,
    book_names: Mapping[str, str] = BOOK_NAMES,
    terms: dict[str, dict[int, list[int]]] = gtf_terms_table,
) -> str:
    """
    Produce table of output showing God the Father terms table for
    the requested language.

    Usage:
    >>> #gtf_terms_for_language("tpi")
    >>> #gtf_terms_for_language("adh")
    >>> gtf_terms_for_language("ach-SS-acholi", True, )
    """
    # filename = f"{lang_code}_{html_filename_part}"
    # document_request_key_ = document_request_key(
    #     lang_code, html_filename_part, "docx" if docx_p else "pdf"
    # )
    html_filepath_ = document_generator.html_filepath(document_request_key)
    pdf_filepath_ = document_generator.pdf_filepath(document_request_key)
    docx_filepath_ = document_generator.docx_filepath(document_request_key)
    enclosed_content = ""
    if asset_file_needs_update(html_filepath_):
        output_table: list[str] = []
        output_table.append(column_labels)
        current_task.update_state(state="Getting associated gateway language")
        gl_lang_code = associated_gateway_language_for_heart_language(lang_code)
        logger.debug("About to get data for heart language: %s", lang_code)
        logger.debug("About to get data for gateway language: %s", gl_lang_code)
        gl_usfm_books_ = gl_usfm_books(gl_lang_code)
        for hl_usfm_book in hl_usfm_books(lang_code):
            gl_usfm_book = associated_gl_usfm_book(
                gl_usfm_books_, hl_usfm_book.book_code
            )
            hl_gtf_chapters, gl_gtf_chapters = chapter_verse_lists(
                hl_usfm_book, gl_usfm_book, terms
            )
            for hl_gtf_chapter_num, hl_gtf_verse_nums in hl_gtf_chapters.items():
                for hl_verse_num in hl_gtf_verse_nums:
                    hl_verse = (
                        hl_usfm_book.chapters[hl_gtf_chapter_num].verses[
                            str(hl_verse_num)
                        ]
                        if hl_usfm_book
                        and hl_gtf_chapter_num in hl_usfm_book.chapters.keys()
                        and str(hl_verse_num)
                        in hl_usfm_book.chapters[hl_gtf_chapter_num].verses.keys()
                        else ""
                    )
                    gl_verse = (
                        gl_usfm_book.chapters[hl_gtf_chapter_num].verses[
                            str(hl_verse_num)
                        ]
                        if gl_usfm_book
                        and hl_gtf_chapter_num in gl_usfm_book.chapters.keys()
                        and str(hl_verse_num)
                        in gl_usfm_book.chapters[hl_gtf_chapter_num].verses.keys()
                        else ""
                    )
                    verse_reference = f"{book_names[hl_usfm_book.book_code]} {hl_gtf_chapter_num}:{hl_verse_num}"
                    current_task.update_state(
                        state=f"Backtranslating {lang_code} verse {verse_reference} using AI"
                    )
                    backtranslation = backtranslate(
                        hl_verse, verse_reference, lang_code, gl_lang_code
                    )
                    output_table.append(
                        # The last column in the row is the empty comments column
                        f"<tr><td>{verse_reference}</td><td>{gl_verse}</td><td>{hl_verse}</td><td>{backtranslation}</td><td></td></tr>\n"
                    )
        content = f"<table>\n{''.join(output_table)}</table>"
        header = document_generator.instantiated_html_header_template(
            "header_enclosing_landscape"
        )
        enclosed_content = document_generator.enclose_html_content(content, header)
        document_generator.write_html_content_to_file(
            enclosed_content,
            html_filepath_,
        )
    else:
        logger.debug("Cache hit for %s", html_filepath_)
    # If the document has previously been generated and is fresh enough,
    # immediately return pre-built PDF.
    if not docx_p and asset_file_needs_update(pdf_filepath_):
        document_generator.convert_html_to_pdf(
            html_filepath_,
            pdf_filepath_,
            document_request_key,
        )
    if docx_p and asset_file_needs_update(docx_filepath_):
        doc = Document()
        composer = Composer(doc)
        subdoc = assembly_strategy_utils.create_docx_subdoc(
            enclosed_content, lang_code, False, False
        )
        composer.append(subdoc)
        title1 = "Language: " + lang_code
        document_generator.convert_html_to_docx(
            html_filepath_,
            docx_filepath_,
            composer,
            False,
            title1,
            title2,
            "Formatted for Translators",
            "template.docx",
        )
    return document_request_key


def sog_terms_for_language(
    lang_code: str,
    docx_p: bool,
    document_request_key: str,
    # html_filename_part: str = "son_of_god_terms",
    title2: str = "Son of God Terms",
    column_labels: str = COLUMN_LABELS,
    book_names: Mapping[str, str] = BOOK_NAMES,
    terms: dict[str, dict[int, list[int]]] = sog_terms_table,
) -> str:
    """
    Produce table of output showing God the Father terms table for
    the requested language.

    Usage:
    >>> #sog_terms_for_language("nfd")
    >>> sog_terms_for_language("ziw")
    >>> #sog_terms_for_language("zin")

    """

    return gtf_terms_for_language(
        # lang_code, html_filename_part, title2, column_labels, book_names, terms
        lang_code,
        docx_p,
        document_request_key,
        title2,
        column_labels,
        book_names,
        terms,
    )


def gl_usfm_books(
    gl_lang_code: Optional[str],
    gl_usfm_resource_types: Sequence[str] = settings.ALL_USFM_RESOURCE_TYPES,
) -> list[USFMBook]:
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
    return gl_usfm_books


def hl_usfm_books(
    lang_code: str,
    usfm_resource_types: Sequence[str] = settings.USFM_RESOURCE_TYPES,
) -> list[USFMBook]:
    hl_book_codes = [
        book_code[0]
        for book_code in resource_lookup.book_codes_for_lang(lang_code)
        if book_code[0] in gtf_terms_table.keys()
    ]
    hl_usfm_resource_types_and_names = [
        resource_type_and_name
        for resource_type_and_name in resource_types_and_names_for_lang(lang_code)
        if resource_type_and_name[0] in usfm_resource_types
    ]
    hl_usfm_books = usfm_books(
        hl_book_codes, hl_usfm_resource_types_and_names, lang_code
    )
    return hl_usfm_books


def associated_gl_usfm_book(
    gl_usfm_books: list[USFMBook], book_code: str
) -> Optional[USFMBook]:
    usfm_books = [
        gl_usfm_book
        for gl_usfm_book in gl_usfm_books
        if gl_usfm_book.book_code == book_code
    ]
    return usfm_books[0] if usfm_books else None


def chapter_verse_lists(
    hl_usfm_book: USFMBook,
    gl_usfm_book: Optional[USFMBook],
    terms: dict[str, dict[int, list[int]]],
) -> tuple[dict[int, list[int]], dict[int, list[int]]]:
    # Get the per chapter verse lists for the current book
    hl_gtf_chapters = (
        terms[hl_usfm_book.book_code]
        if hl_usfm_book and hl_usfm_book.book_code in terms
        else {}
    )
    gl_gtf_chapters = (
        terms[gl_usfm_book.book_code]
        if gl_usfm_book and gl_usfm_book.book_code in terms
        else {}
    )
    # Handle when per chapter verse lists do not exist for the current book
    if not hl_gtf_chapters:
        if gl_gtf_chapters:
            for (
                gl_gtf_chapters_chapter_num,
                gl_gtf_chapters_verse_nums,
            ) in gl_gtf_chapters.items():
                hl_gtf_chapters[gl_gtf_chapters_chapter_num] = []
    if not gl_gtf_chapters:
        if hl_gtf_chapters:
            for (
                hl_gtf_chapters_chapter_num,
                hl_gtf_chapters_verse_nums,
            ) in hl_gtf_chapters.items():
                gl_gtf_chapters[hl_gtf_chapters_chapter_num] = []
    logger.debug("hl_gtf_chapters: %s", hl_gtf_chapters)
    logger.debug("gl_gtf_chapters: %s", gl_gtf_chapters)
    return hl_gtf_chapters, gl_gtf_chapters


def backtranslate(
    hl_verse_html: str,
    verse_reference: str,
    lang_code: str,
    gl_lang_code: Optional[str],
    use_ai: bool = dft_settings.USE_AI,
    chatgpt_model: str = "gpt-3.5-turbo",
) -> Optional[str]:
    backtranslation: Optional[str] = ""
    if hl_verse_html and gl_lang_code and use_ai:
        prompt = "Translate {}: '{}' from {} language to {} language".format(
            verse_reference,
            BeautifulSoup(hl_verse_html, "lxml").get_text(),
            lang_code,
            gl_lang_code,
        )
        # OPENAI_API_KEY gets picked up from env automatically
        chat_completion = openai.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=chatgpt_model,
        )
        backtranslation = chat_completion.choices[0].message.content
    return backtranslation


def document_request_key(
    lang_code: str,
    table_name: str,
    doc_type: str,
    underscore: str = "_",
) -> str:
    """
    Create and return the document_request_key. The
    document_request_key uniquely identifies a document request.
    """
    document_request_key = underscore.join([lang_code, table_name, doc_type])
    return document_request_key


# def main() -> None:
#     gtf_terms_for_language("ach-SS-acholi", True, "foo")
#     sog_terms_for_language("ziw", True, "bar")


if __name__ == "__main__":

    # To run the doctests in the this module, in the root of the
    # project do something like:
    # FROM_EMAIL_ADDRESS=... python backend/usfm_checker.py
    import doctest

    doctest.testmod()
