import os
import tempfile
import zipfile
import subprocess
import re
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, send_file, redirect, url_for
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from constants import ALL_EXTENSIONS, LANGUAGE_BY_EXTENSION
from analyzers import PythonAnalyzer, JavaScriptAnalyzer, JavaAnalyzer

class LanguageAnalyzer:
    """Base interface for language analyzers."""
    
    @staticmethod
    def get_extensions():
        """Return file extensions supported by this analyzer."""
        raise NotImplementedError()
    
    def analyze_style(self, directory):
        """Analyze code style."""
        raise NotImplementedError()
    
    def analyze_quality(self, directory):
        """Analyze code quality."""
        raise NotImplementedError()
    
    def analyze_complexity(self, directory):
        """Analyze code complexity."""
        raise NotImplementedError()
    
    def analyze_security(self, directory):
        """Analyze code security."""
        raise NotImplementedError()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze_pr', methods=['POST'])
def analyze_pr():
    """Analyze code from a GitHub Pull Request."""
    pr_url = request.form.get('pr_url', '')
    if not pr_url:
        return render_template('index.html', error="Please provide a valid GitHub PR URL.")
    
    try:
        owner, repo, pr_number = parse_github_pr_url(pr_url)
        if not owner or not repo or not pr_number:
            return render_template('index.html', error="Invalid GitHub PR URL format. Expected: https://github.com/owner/repo/pull/number")
        
        temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])
        
        pr_files = fetch_github_pr_files(owner, repo, pr_number, temp_dir)
        
        if not pr_files:
            return render_template('index.html', error="No supported code files found in the PR or unable to access the repository.")
        
        language_metrics = analyze_directory(temp_dir)
        
        if not language_metrics:
            return render_template('index.html', error="No supported code files found in the PR.")
        
        report_title = f"{owner}/{repo} PR #{pr_number}"
        report_path = generate_report(language_metrics, report_title)
        
        return send_file(
            report_path, 
            as_attachment=True, 
            download_name=f"code_quality_report_PR_{owner}_{repo}_{pr_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
    except requests.exceptions.RequestException as e:
        return render_template('index.html', error=f"Network error accessing GitHub API: {str(e)}")
    except json.JSONDecodeError:
        return render_template('index.html', error="Invalid response from GitHub API. Please check your access token if you're using one.")
    except Exception as e:
        return render_template('index.html', error=f"Error analyzing PR: {str(e)}")

def parse_github_pr_url(url):
    """Parse a GitHub PR URL to extract owner, repo, and PR number."""
    pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.match(pattern, url)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

def fetch_github_pr_files(owner, repo, pr_number, temp_dir):
    """Fetch files from a GitHub PR and save them to the temp directory."""
    github_token = os.environ.get('GITHUB_TOKEN', '')
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    response = requests.get(api_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR files: {response.status_code} {response.text}")
    
    files_data = response.json()
    downloaded_files = []
    skipped_files = []
    language_counts = {}
    
    for file_data in files_data:
        filename = file_data.get('filename')
        if not filename:
            continue
        
        _, file_extension = os.path.splitext(filename)
        file_extension = file_extension.lower()
        
        if file_extension not in ALL_EXTENSIONS:
            skipped_files.append(filename)
            continue
        
        language = LANGUAGE_BY_EXTENSION.get(file_extension, "Unknown")
        language_counts[language] = language_counts.get(language, 0) + 1
        
        raw_url = file_data.get('raw_url')
        if not raw_url:
            raw_url = file_data.get('contents_url', '').replace('api.github.com/repos', 'raw.githubusercontent.com').replace('/contents/', '/')
        
        if not raw_url:
            skipped_files.append(filename)
            continue
        
        file_response = requests.get(raw_url, headers=headers)
        if file_response.status_code != 200:
            skipped_files.append(filename)
            continue
        
        file_path = os.path.join(temp_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(file_response.content)
        
        downloaded_files.append(file_path)
    
    print(f"Downloaded {len(downloaded_files)} files from PR #{pr_number}")
    for language, count in language_counts.items():
        print(f"  - {language}: {count} files")
    if skipped_files:
        print(f"Skipped {len(skipped_files)} unsupported files")
    
    return downloaded_files

def get_language_analyzer(file_extension):
    """Factory method to get the appropriate language analyzer based on file extension."""
    if file_extension in ['.py']:
        return PythonAnalyzer()
    elif file_extension in ['.js', '.jsx', '.ts', '.tsx']:
        return JavaScriptAnalyzer()
    elif file_extension in ['.java']:
        return JavaAnalyzer()
    return None

def get_language_name(file_extension):
    """Get the language name for a file extension."""
    return LANGUAGE_BY_EXTENSION.get(file_extension, "Unknown")

def analyze_directory(directory):
    """Analyze all supported files in a directory and return metrics by language."""
    language_metrics = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            _, file_extension = os.path.splitext(file)
            if file_extension in ALL_EXTENSIONS:
                language = get_language_name(file_extension)
                if language not in language_metrics:
                    language_metrics[language] = {
                        'files': [],
                        'style': {'score': 0, 'issues': []},
                        'quality': {'score': 0, 'issues': []},
                        'complexity': {'score': 0, 'issues': []},
                        'security': {'score': 0, 'issues': []}
                    }
                language_metrics[language]['files'].append(os.path.join(root, file))
    
    for language, data in language_metrics.items():
        if not data['files']:
            continue
        
        _, file_extension = os.path.splitext(data['files'][0])
        analyzer = get_language_analyzer(file_extension)
        
        if analyzer:
            data['style'] = analyzer.analyze_style(directory)
            data['quality'] = analyzer.analyze_quality(directory)
            data['complexity'] = analyzer.analyze_complexity(directory)
            data['security'] = analyzer.analyze_security(directory)
    
    return language_metrics

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)
    
    if file.filename.endswith('.zip'):
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        analyze_dir = extract_dir
    else:
        analyze_dir = temp_dir
    
    language_metrics = analyze_directory(analyze_dir)
    
    if not language_metrics:
        return render_template('index.html', error="No supported code files found in the upload.")
    
    report_path = generate_report(language_metrics, file.filename)
    
    return send_file(report_path, as_attachment=True, download_name=f"code_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

def generate_report(language_metrics, filename):
    """Generate a PDF report with the analysis results for multiple languages."""
    fd, path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    title_style = styles['Title']
    elements.append(Paragraph(f"Code Quality Report: {filename}", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    date_style = styles['Normal']
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
    elements.append(Spacer(1, 0.25*inch))
    
    heading_style = styles['Heading1']
    elements.append(Paragraph("Summary", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    data = [
        ["Language", "Files", "Style", "Quality", "Complexity", "Security", "Overall"]
    ]
    
    overall_scores = {
        'style': 0,
        'quality': 0,
        'complexity': 0,
        'security': 0,
        'overall': 0
    }
    
    total_languages = len(language_metrics)
    
    for language, metrics in language_metrics.items():
        style_score = metrics['style']['score']
        quality_score = metrics['quality']['score']
        complexity_score = metrics['complexity']['score']
        security_score = metrics['security']['score']
        overall_score = (style_score + quality_score + complexity_score + security_score) / 4
        
        data.append([
            language,
            len(metrics['files']),
            f"{style_score:.1f}",
            f"{quality_score:.1f}",
            f"{complexity_score:.1f}",
            f"{security_score:.1f}",
            f"{overall_score:.1f}"
        ])
        
        overall_scores['style'] += style_score
        overall_scores['quality'] += quality_score
        overall_scores['complexity'] += complexity_score
        overall_scores['security'] += security_score
        overall_scores['overall'] += overall_score
    
    if total_languages > 1:
        data.append([
            "Overall",
            sum(len(metrics['files']) for metrics in language_metrics.values()),
            f"{overall_scores['style'] / total_languages:.1f}",
            f"{overall_scores['quality'] / total_languages:.1f}",
            f"{overall_scores['complexity'] / total_languages:.1f}",
            f"{overall_scores['security'] / total_languages:.1f}",
            f"{overall_scores['overall'] / total_languages:.1f}"
        ])
    
    table = Table(data, colWidths=[1.2*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    if total_languages > 1:
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    for language, metrics in language_metrics.items():
        elements.append(Paragraph(f"{language} Analysis", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph(f"Files analyzed: {len(metrics['files'])}", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        metric_data = [
            ["Metric", "Score (0-10)", "Rating"],
            ["Code Style", f"{metrics['style']['score']:.1f}", get_rating(metrics['style']['score'])],
            ["Code Quality", f"{metrics['quality']['score']:.1f}", get_rating(metrics['quality']['score'])],
            ["Complexity", f"{metrics['complexity']['score']:.1f}", get_rating(metrics['complexity']['score'])],
            ["Security", f"{metrics['security']['score']:.1f}", get_rating(metrics['security']['score'])],
            ["Overall", f"{(metrics['style']['score'] + metrics['quality']['score'] + metrics['complexity']['score'] + metrics['security']['score'])/4:.1f}", 
             get_rating((metrics['style']['score'] + metrics['quality']['score'] + metrics['complexity']['score'] + metrics['security']['score'])/4)]
        ]
        
        lang_table = Table(metric_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        lang_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(lang_table)
        elements.append(Spacer(1, 0.25*inch))
        
        for metric_name in ['style', 'quality', 'complexity', 'security']:
            metric_data = metrics[metric_name]
            elements.append(Paragraph(f"{metric_name.capitalize()} Analysis", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            elements.append(Paragraph(f"Score: {metric_data['score']:.1f}/10 ({get_rating(metric_data['score'])})", styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
            
            elements.append(Paragraph("Issues:", styles['Heading3']))
            if not metric_data['issues']:
                elements.append(Paragraph("No issues found.", styles['Normal']))
            else:
                for issue in metric_data['issues'][:20]:  # Limit to 20 issues to avoid huge reports
                    elements.append(Paragraph(f"• {issue}", styles['Normal']))
                
                if len(metric_data['issues']) > 20:
                    elements.append(Paragraph(f"... and {len(metric_data['issues']) - 20} more issues", styles['Normal']))
            
            elements.append(Spacer(1, 0.25*inch))
    
    doc.build(elements)
    
    return path

def get_rating(score):
    """Convert a score to a rating."""
    if score >= 9:
        return "Excellent"
    elif score >= 7:
        return "Good"
    elif score >= 5:
        return "Average"
    elif score >= 3:
        return "Poor"
    else:
        return "Very Poor"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
