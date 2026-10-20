# Military Career Platform

A unified career-support platform designed to help ex-servicemen and military veterans explore civilian employment opportunities and prepare resumes that communicate their service experience in civilian-friendly language.

The project brings together two main workflows:

- **AI-assisted resume building** — document extraction, military-to-civilian wording support, resume formatting, and export.
- **Job discovery** — collection and presentation of job opportunities from configured sources, with links to the original postings.

> **Project status:** This README describes the capabilities and setup paths documented in the project. Exact feature availability depends on the code, installed dependencies, configured API keys, and the job sources currently supported.

## Contents

- [Features](#features)
- [Project structure](#project-structure)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Manual installation](#manual-installation)
- [Configuration](#configuration)
- [Running the applications](#running-the-applications)
- [Troubleshooting](#troubleshooting)
- [Privacy and security](#privacy-and-security)
- [Limitations](#limitations)
- [Contributing](#contributing)

## Features

### Resume builder

The resume workflow is intended to help veterans present military experience in a format that is easier for civilian recruiters to understand.

- **Document extraction:** OCR and PDF-processing support for scanned or digital documents, depending on the input and installed tools.
- **Military-to-civilian translation:** helps reframe service experience and transferable skills using civilian terminology.
- **AI-assisted content improvement:** the project documentation lists Mistral AI integration for resume-content enhancement.
- **Resume formatting:** professional, ATS-conscious layouts and structured resume content.
- **Export options:** the project documentation lists PDF, HTML, JSON, and text output; verify which formats are enabled in your current version.

Always review extracted details and AI-generated wording before using a resume. OCR and language models can omit, misread, or invent details. Do not include classified, restricted, or otherwise sensitive military information.

### Job finder

The job-finder workflow collects job listings from configured sources and presents them for exploration.

- **Job-source collection:** scraping tools for the job boards configured in the project.
- **Job discovery:** explore opportunities relevant to veterans and people transitioning to civilian employment.
- **Job details and application links:** inspect available listing information and follow the source link to the original posting.
- **Filtering and market insights:** use the filters and dashboard analytics implemented in the current version.

Job availability, listing freshness, supported fields, and source coverage depend on the individual source and its current website structure. Scraped listings should be verified on the original job page before applying.

## Project structure

The repository layout documented by the project is approximately:

```text
military_career_platform/
├── main_app.py                 # Unified Streamlit entry point
├── setup.py                    # Setup and launch helper
├── EASY_SETUP.bat               # Windows setup helper
├── requirements.txt             # Top-level Python dependencies
├── verify_installation.py       # Installation verification helper
├── military_resume/
│   ├── resume.py                # Resume-builder application
│   ├── requirements.txt         # Resume-specific dependencies
│   └── resume/                  # Sample resume documents, if included
└── milatary/
    ├── streamlit_app.py         # Job-finder dashboard
    ├── requirements.txt         # Job-finder dependencies
    ├── jobScrap/                # Scraping utilities
    ├── military_1/              # Job-source data or module
    └── military_2/              # Additional job-source data or module
```

The tree is based on the supplied project documentation. Confirm names and paths against the actual checkout; in particular, the directory is documented as `milatary/` (rather than `military/`).

## Requirements

The original project documentation specifies:

- Python 3.8 or newer
- Windows, macOS, or Linux
- Internet access for package installation and any network-dependent features
- Additional disk space for Python packages, NLP models, and document processing tools

Some OCR workflows may require the Tesseract executable in addition to Python packages. The spaCy English model may also need to be installed separately.

## Quick start

### Windows

From the repository root, run:

```bat
EASY_SETUP.bat
```

Review the script before running it, especially if you are using a managed or work computer. Run it from a terminal so you can see setup errors.

### Cross-platform

The repository documents this setup helper:

```bash
python setup.py
```

Inspect `setup.py` first to understand what it installs, configures, or launches. If it does not work in your environment, use the manual steps below.

## Manual installation

It is recommended to use a virtual environment so the project's dependencies do not interfere with other Python applications.

### 1. Create and activate a virtual environment

**Windows (Command Prompt):**

```bat
python -m venv .venv
.venv\Scripts\activate
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS or Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the resume builder or job finder maintains separate dependency files, install the relevant module's dependencies as needed:

```bash
python -m pip install -r military_resume/requirements.txt
python -m pip install -r milatary/requirements.txt
```

Only run the commands for files that exist in your checkout. If a package fails to install, keep the full error output for diagnosis rather than immediately forcing a reinstall.

### 3. Install the spaCy model

If the application uses spaCy's small English model:

```bash
python -m spacy download en_core_web_sm
```

### 4. Install OCR software if required

On Ubuntu or Debian-based Linux systems:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

For Windows and macOS, install Tesseract using a trusted distribution for your operating system and ensure its executable is available on your `PATH` if the application invokes it directly.

### 5. Launch the application

From the repository root:

```bash
streamlit run main_app.py
```

Streamlit normally prints a local URL in the terminal, commonly `http://localhost:8501`. Open the URL shown by your terminal.

## Configuration

Some features may require API credentials. The original project documentation lists a `.env` file and the following variables:

```dotenv
# Add only keys that are used by your current code
MISTRAL_API_KEY=your_mistral_api_key
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
INDEED_API_KEY=your_indeed_api_key
LINKEDIN_API_KEY=your_linkedin_api_key
```

Not every variable is necessarily consumed by the current implementation. Check the code and dependency configuration to determine which integrations are active. Do not put real API keys in source control, screenshots, logs, or issue reports.

If the project loads values from `.env`, ensure the relevant environment-loading package is installed and that the application loads the file before accessing the variables.

Add secrets and local data files to `.gitignore`. A minimal example is:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
.streamlit/secrets.toml
```

Adapt the ignore rules to the actual project. Do not ignore dependency lock files or other reproducibility files if the project uses them intentionally.

## Running the applications

### Change the port

```bash
streamlit run main_app.py --server.port 8080
```

### Run in headless mode

```bash
streamlit run main_app.py --server.headless true
```

### Bind to a specific address

```bash
streamlit run main_app.py --server.address 0.0.0.0
```

Binding to `0.0.0.0` can expose the application to other devices on the network. Do this only when you understand the network and access-control implications. Do not expose a development instance directly to the public internet without appropriate authentication, authorization, and deployment hardening.

## Troubleshooting

### Python or pip is not found

Check the installed versions:

```bash
python --version
python -m pip --version
```

On Windows, the Python launcher may be available as `py`:

```bat
py --version
py -m pip --version
```

Reopen the terminal after installing Python and confirm that Python was added to `PATH`.

### A module cannot be imported

Activate the project's virtual environment, then install the applicable requirements file:

```bash
python -m pip install -r requirements.txt
```

Check the traceback to identify the missing module and the Python interpreter running the application.

### spaCy model is missing

```bash
python -m spacy download en_core_web_sm
```

Confirm that the installed spaCy version is compatible with the model version.

### OCR does not work

- Confirm that Tesseract is installed if the application depends on it.
- Check whether the executable is available on `PATH`.
- Test with a readable, non-sensitive sample document.
- Check the terminal output for file-path, PDF-rendering, or OCR errors.

### The Streamlit port is already in use

Try another port:

```bash
streamlit run main_app.py --server.port 8504
```

### Job data is missing or outdated

- Check network connectivity and the source website.
- Inspect scraper logs and the source-specific parsing code.
- Confirm that the website has not changed its markup or access requirements.
- Verify whether the source permits automated access and follow its terms and applicable policies.
- Open the original posting to confirm the role, deadline, and application link.

Avoid bypassing access controls or using undocumented access methods that violate a source's terms.

## Privacy and security

Resume documents can contain personal, employment, and military-service information. Before processing or sharing a document:

- Use sample or redacted documents when testing.
- Do not upload classified, restricted, or sensitive operational information.
- Review third-party AI provider data-handling terms before sending document text to an external API.
- Keep API keys and other credentials out of Git.
- Limit access to uploaded documents, extracted text, logs, and generated resumes.
- Confirm where files and extracted data are stored and how they are deleted.

Do not assume that all processing is local: AI integrations, web scraping, and other network features may send requests to external services.

## Limitations

- OCR quality depends on scan quality, layout, language, and document condition.
- AI-generated resume wording and extracted entities require human verification.
- ATS-friendly formatting does not guarantee that an applicant tracking system will accept or rank a resume.
- Scrapers can break when source websites change, and job data can become stale.
- Availability of API integrations and export formats depends on the installed code and configuration.

## Contributing

Contributions that improve reliability, reproducibility, accessibility, and data quality are welcome.

1. Create a branch for your change.
2. Keep changes focused and document any new configuration.
3. Add or update tests where practical.
4. Never commit credentials, personal documents, or real user data.
5. Include steps to reproduce a bug and the expected behavior when opening an issue or pull request.

## Acknowledgements

The project documentation references open-source tools including Streamlit, spaCy, and PyMuPDF, along with Mistral AI for resume-content enhancement. See the dependency files and each upstream project's license for the exact components and applicable terms.

---

**Built to support the transition from military service to civilian careers.**
