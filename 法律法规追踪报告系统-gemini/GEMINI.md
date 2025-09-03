# GEMINI Code Review Report

This document provides a comprehensive analysis of the "法律法规追踪报告系统" (Legal Regulation Tracking and Reporting System) project. It is intended to be used as a guide for future development and maintenance.

## Project Overview

This project is a Python-based desktop application designed to automatically track, analyze, and report on legal and regulatory changes. It scrapes relevant information from specified websites, uses an AI service to analyze the content, and stores the results in a local database. The application provides a user interface to view the tracked regulations and generate reports.

### Core Technologies

*   **Backend:** Python 3
*   **Data Scraping:** `requests` and `BeautifulSoup4`
*   **Database:** SQLite with `SQLAlchemy` as the ORM.
*   **AI Service:** A large language model is used for text analysis.
*   **GUI:** The UI is built with a Python GUI framework (likely Tkinter or PyQt, based on the file structure).

### Architecture

The project follows a modular architecture, with code organized into the following directories:

*   `src/config`: Contains configuration files for settings and constants.
*   `src/core`: Implements the core logic, including the web scraper (`scraper.py`) and the AI service integration (`ai_service.py`).
*   `src/database`: Manages the database connection, session handling, and data models (`connection.py`, `models.py`).
*   `src/ui`: Contains the user interface code (`app.py`).
*   `src/utils`: Provides utility functions, such as logging and decorators.
*   `tests`: Contains unit tests for the application's components.

## Building and Running

### Prerequisites

*   Python 3.x
*   `pip` for package management

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd 法律法规追踪报告系统-gemini
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    *   Create a `.env` file by copying the `.env.example` file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file to include the necessary API keys for the AI service.

### Running the Application

To start the application, run the `main.py` script:

```bash
python src/main.py
```

### Testing

The project includes a `tests` directory with unit tests. To run the tests, you can use `pytest`:

```bash
pytest
```

## Development Conventions

### Coding Style

The codebase appears to follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. It is recommended to use a linter like `flake8` or `pylint` to ensure consistency.

### Database Migrations

The project uses SQLAlchemy to manage the database schema. When making changes to the data models in `src/database/models.py`, a database migration may be required. The current setup does not include a migration tool like Alembic, so schema changes might need to be handled manually or by adding a migration tool.

### Contribution Guidelines

While there is no explicit `CONTRIBUTING.md` file, the following best practices are recommended:

*   Write clear and concise commit messages.
*   Create new branches for new features or bug fixes.
*   Write unit tests for new functionality.
*   Ensure all tests pass before submitting a pull request.
