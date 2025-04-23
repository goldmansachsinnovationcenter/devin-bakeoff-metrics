# Code Quality Metrics Tool

A web-based application that analyzes code for quality metrics and generates comprehensive PDF reports.

## Features

- Upload code files for analysis
- Analyze GitHub Pull Requests directly
- Analyze code using multiple metrics:
  - Code style
  - Code quality
  - Cyclomatic complexity
  - Security vulnerabilities
- Generate detailed PDF reports with visualizations
- Modern, responsive web interface

## Installation

1. Clone the repository
2. Create a Python virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install flask reportlab pylint flake8 radon bandit coverage
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```
2. Open your web browser and navigate to `http://localhost:5000`
3. Choose one of the following options:
   - **File Upload**: Upload your code file or ZIP archive containing Python files
   - **GitHub PR**: Enter a GitHub Pull Request URL (e.g., https://github.com/owner/repo/pull/123)
4. Click "Generate Report" to analyze the code and download the PDF report

### GitHub PR Analysis

The tool can analyze code directly from GitHub Pull Requests:
1. Enter a valid GitHub PR URL in the format: `https://github.com/owner/repo/pull/123`
2. The tool will fetch all Python files from the PR
3. Analysis will be performed on these files and a comprehensive report will be generated

## Requirements

- Python 3.6+
- Flask
- ReportLab
- Pylint
- Flake8
- Radon
- Bandit
- Coverage

## License

MIT
