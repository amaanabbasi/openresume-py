# openresume-py
This repository contains a Python script for parsing and extracting information from resume PDF files using PyMuPDF (fitz). The script identifies sections such as Profile, Experience, Education, Projects, and Skills, and extracts relevant details like job titles, company names, dates, etc. The parsed data is then structured in a dictionary format.

# Resume Parser

A Python script for parsing resume PDF files to extract and organize information. This script utilizes PyMuPDF (fitz) for text extraction and applies heuristics to identify and structure resume sections and their contents.

## Features

- Extracts text from PDF resumes
- Identifies and organizes sections like Profile, Experience, Education, Projects, and Skills
- Detects subsections within sections
- Extracts specific attributes such as names, emails, phone numbers, job titles, companies, dates, etc.
- Cleans and normalizes extracted text

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/amaanabbasi/resume-parser.git
    ```

2. Change to the repository directory:

    ```bash
    cd resume-parser
    ```

3. Create a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Ensure your resume PDF is accessible.

2. Update the script with the path to your resume PDF:

    ```python
    parser = ResumeParser("/path/to/your/resume.pdf")
    ```

3. Run the script:

    ```bash
    python resume_parser.py
    ```

4. The parsed resume data will be printed to the console.

## Example

```python
if __name__ == "__main__":
    parser = ResumeParser("/path/to/your/resume.pdf")
    resume_data = parser.parse()
    print(resume_data)

