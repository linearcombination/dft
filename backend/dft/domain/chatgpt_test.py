from openai import OpenAI
from dft.domain.dft_checker import associated_gateway_language_for_heart_language
from bs4 import BeautifulSoup

client = OpenAI()

lang_code = "ach-SS-acholi"
gl_lang_code = associated_gateway_language_for_heart_language(lang_code)
verse_reference = "Matthew 5:16"
hl_verse = "<span class=\"v-num\" id='ach-SS-acholi-040-ch-005-v-016'><sup><b>16</b></sup></span> Wun bene wubed jo ma menyo piny calo tara bot dano, wek gunen tic mabeco ma wutiyo ci gumi deyo bot Wonwu ma tye i polo. "
hl_verse_text = BeautifulSoup(hl_verse, "lxml").get_text()
print("hl_verse_text: ", hl_verse_text)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Translate {}: '{}' from {} language to {} language".format(
                verse_reference,
                BeautifulSoup(hl_verse, "lxml").get_text(),
                lang_code,
                gl_lang_code,
            ),
        }
    ],
    model="gpt-3.5-turbo",
    # model="gpt-4",
)
backtranslation = chat_completion.choices[0].message.content
print(backtranslation)
