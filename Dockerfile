FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y \
    # wget \
    # curl \
    git \
    unzip \
    # For additional fonts needed, specifically Chinese
    # texlive-fonts-recommended \
    # For ebook-convert
    # xz-utils \
    # xdg-utils \
    # libegl1 \
    # libopengl0 \
    # libegl1 \
    # libopengl0 \
    # libxcb-cursor0 \
    # libxcb-xinerama0 \
    # libxkbcommon0 \
    # libglx0 \
    # libnss3
    # For usfm_tools and mypyc
    gcc

# Get and install needed fonts.
# RUN cd /tmp \
#     && git clone --depth 1 https://github.com/Bible-Translation-Tools/ScriptureAppBuilder-pipeline \
#     && cp /tmp/ScriptureAppBuilder-pipeline/ContainerImage/home/fonts/*.ttf /usr/share/fonts/
# # Refresh system font cache.
# RUN fc-cache -f -v

# Get and install calibre for use of its ebook-convert binary for HTML
# to ePub conversion.
# RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin install_dir=/calibre-bin isolated=y

WORKDIR /app

# Make the output directory where resource asset files are cloned or
# downloaded and unzipped.
RUN mkdir -p working/temp
# Make the output directory where generated HTML and PDFs are placed.
RUN mkdir -p working/output
# Make the output directory where generated documents (PDF, ePub, Docx) are copied too.
RUN mkdir -p document_output

COPY pyproject.toml .
COPY ./backend/requirements.txt .
COPY ./backend/requirements-prod.txt .
COPY template.docx .
# COPY template_compact.docx .

# See https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
# for why a Python virtual env is used inside Docker.
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv ${VIRTUAL_ENV}
ENV PATH=${VIRTUAL_ENV}/bin:${PATH}

RUN pip install -v --upgrade pip
RUN pip install -v -r requirements.txt
RUN pip install -v -r requirements-prod.txt

COPY ./backend ./backend
# COPY ./tests ./tests
COPY .env .
COPY .env_dft .

# Make sure Python can find the code to run
# ENV PYTHONPATH=/app/backend:/app/tests
ENV PYTHONPATH=/app/backend

# Inside the Python virtual env: install any missing mypy
# type packages and check types in strict mode.
RUN mypy --strict --install-types --non-interactive backend/dft/**/*.py
# RUN mypy --strict --install-types --non-interactive tests/**/*.py

# No longer using mypyc as the resulting executable code is now
# actually slower than non-transpiled python.
# Inside the Python virtual env: check types, install any missing mypy stub
# types packages, and transpile most modules into C using mypyc which
# in turn build them with the resident C compiler, usually clang or
# gcc.
# RUN cd backend && mypyc --strict --install-types --non-interactive document/domain/assembly_strategies/assembly_strategies.py document/domain/parsing.py document/domain/resource_lookup.py # document/domain/document_generator.py
