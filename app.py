import os
import tempfile
import zipfile
import subprocess
import re
import requests
import json
import base64
from datetime import datetime
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

@app.route('/')
def index():
    return render_template('index.html')

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
    
    metrics = {}
    metrics['style'] = run_flake8(analyze_dir)
    metrics['quality'] = run_pylint(analyze_dir)
    metrics['complexity'] = run_radon(analyze_dir)
    metrics['security'] = run_bandit(analyze_dir)
    
    report_path = generate_report(metrics, file.filename)
    
    return send_file(report_path, as_attachment=True, download_name=f"code_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

def run_flake8(directory):
    """Run flake8 on the directory and return the results."""
    result = {'score': 0, 'issues': []}
    
    try:
        python_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        if not python_files:
            return {'score': 10.0, 'issues': ['No Python files found']}
        
        total_issues = 0
        for py_file in python_files:
            try:
                output = subprocess.check_output(['flake8', py_file], stderr=subprocess.STDOUT, text=True)
            except subprocess.CalledProcessError as e:
                output = e.output
            
            lines = output.strip().split('\n')
            if lines and lines[0]:  # If there are issues
                for line in lines:
                    result['issues'].append(line)
                    total_issues += 1
        
        avg_issues = total_issues / len(python_files) if python_files else 0
        result['score'] = max(0, 10 - min(10, avg_issues))
        
    except Exception as e:
        result['issues'].append(f"Error running flake8: {str(e)}")
        result['score'] = 0
    
    return result

def run_pylint(directory):
    """Run pylint on the directory and return the results."""
    result = {'score': 0, 'issues': []}
    
    try:
        python_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        if not python_files:
            return {'score': 10.0, 'issues': ['No Python files found']}
        
        total_score = 0
        for py_file in python_files:
            try:
                output = subprocess.check_output(['pylint', '--output-format=text', py_file], stderr=subprocess.STDOUT, text=True)
            except subprocess.CalledProcessError as e:
                output = e.output
            
            score_match = re.search(r'Your code has been rated at ([-\d.]+)/10', output)
            if score_match:
                file_score = float(score_match.group(1))
                if file_score < 0:
                    file_score = 0
                total_score += file_score
            
            for line in output.strip().split('\n'):
                if ':' in line and not line.startswith('Your code'):
                    result['issues'].append(line)
        
        result['score'] = total_score / len(python_files) if python_files else 0
        
    except Exception as e:
        result['issues'].append(f"Error running pylint: {str(e)}")
        result['score'] = 0
    
    return result

def run_radon(directory):
    """Run radon on the directory and return the results."""
    result = {'score': 0, 'issues': []}
    
    try:
        python_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        if not python_files:
            return {'score': 10.0, 'issues': ['No Python files found']}
        
        complexity_sum = 0
        file_count = 0
        
        for py_file in python_files:
            try:
                output = subprocess.check_output(['radon', 'cc', py_file, '--no-assert'], stderr=subprocess.STDOUT, text=True)
            except subprocess.CalledProcessError as e:
                output = e.output
            
            lines = output.strip().split('\n')
            if lines and lines[0]:  # If there are results
                for line in lines:
                    result['issues'].append(line)
                    complexity_match = re.search(r'[A-F] \((\d+)\)', line)
                    if complexity_match:
                        complexity_sum += int(complexity_match.group(1))
                        file_count += 1
        
        avg_complexity = complexity_sum / file_count if file_count else 0
        result['score'] = max(0, 10 - min(10, avg_complexity))
        
    except Exception as e:
        result['issues'].append(f"Error running radon: {str(e)}")
        result['score'] = 0
    
    return result

def run_bandit(directory):
    """Run bandit on the directory and return the results."""
    result = {'score': 0, 'issues': []}
    
    try:
        python_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        if not python_files:
            return {'score': 10.0, 'issues': ['No Python files found']}
        
        try:
            output = subprocess.check_output(['bandit', '-r', directory], stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output
        
        issues_found = False
        for line in output.strip().split('\n'):
            if 'Issue:' in line or 'Location:' in line or 'Severity:' in line:
                result['issues'].append(line)
                issues_found = True
        
        issue_count = len([i for i in result['issues'] if 'Issue:' in i])
        
        result['score'] = max(0, 10 - min(10, issue_count))
        
        if not issues_found:
            result['issues'].append("No security issues found")
            result['score'] = 10.0
        
    except Exception as e:
        result['issues'].append(f"Error running bandit: {str(e)}")
        result['score'] = 0
    
    return result

def generate_report(metrics, filename):
    """Generate a PDF report with the analysis results."""
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
    
    if '/' in filename and 'PR#' in filename:
        elements.append(Paragraph(f"GitHub Pull Request: {filename}", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
    
    heading_style = styles['Heading1']
    elements.append(Paragraph("Summary", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    data = [
        ["Metric", "Score (0-10)", "Rating"],
        ["Code Style", f"{metrics['style']['score']:.1f}", get_rating(metrics['style']['score'])],
        ["Code Quality", f"{metrics['quality']['score']:.1f}", get_rating(metrics['quality']['score'])],
        ["Complexity", f"{metrics['complexity']['score']:.1f}", get_rating(metrics['complexity']['score'])],
        ["Security", f"{metrics['security']['score']:.1f}", get_rating(metrics['security']['score'])],
        ["Overall", f"{(metrics['style']['score'] + metrics['quality']['score'] + metrics['complexity']['score'] + metrics['security']['score'])/4:.1f}", 
         get_rating((metrics['style']['score'] + metrics['quality']['score'] + metrics['complexity']['score'] + metrics['security']['score'])/4)]
    ]
    
    table = Table(data, colWidths=[2*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    for metric_name, metric_data in metrics.items():
        elements.append(Paragraph(f"{metric_name.capitalize()} Analysis", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph(f"Score: {metric_data['score']:.1f}/10 ({get_rating(metric_data['score'])})", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph("Issues:", styles['Heading3']))
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

def parse_github_pr_url(pr_url):
    """Parse a GitHub PR URL and extract owner, repo, and PR number."""
    if not pr_url:
        return None, None, None
        
    try:
        parts = pr_url.strip('/').split('/')
        if 'github.com' not in parts:
            return None, None, None
            
        github_index = parts.index('github.com')
        if len(parts) < github_index + 5 or parts[github_index + 3] != 'pull':
            return None, None, None
            
        owner = parts[github_index + 1]
        repo = parts[github_index + 2]
        pr_number = parts[github_index + 4]
        
        return owner, repo, pr_number
    except (ValueError, IndexError):
        return None, None, None

def fetch_github_pr_files(owner, repo, pr_number):
    """Fetch files from a GitHub PR and save them to a temporary directory."""
    if not owner or not repo or not pr_number:
        return None, "Invalid GitHub PR details"
    
    temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])
    
    try:
        pr_files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
        headers = {}
        
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            headers['Authorization'] = f"token {github_token}"
        
        response = requests.get(pr_files_url, headers=headers)
        if response.status_code != 200:
            return None, f"Failed to fetch PR files: {response.status_code} {response.reason}"
        
        pr_files = response.json()
        
        for file in pr_files:
            filename = file.get('filename')
            if not filename.endswith('.py'):
                continue
                
            file_path = os.path.join(temp_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            raw_url = file.get('raw_url')
            content_response = requests.get(raw_url, headers=headers)
            if content_response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(content_response.content)
        
        return temp_dir, None
    except Exception as e:
        return None, str(e)

@app.route('/analyze-pr', methods=['POST'])
def analyze_pr():
    pr_url = request.form.get('pr_url')
    
    owner, repo, pr_number = parse_github_pr_url(pr_url)
    if not owner or not repo or not pr_number:
        return render_template('index.html', error="Invalid GitHub PR URL. Please use format: https://github.com/owner/repo/pull/123")
    
    analyze_dir, error = fetch_github_pr_files(owner, repo, pr_number)
    if not analyze_dir:
        return render_template('index.html', error=f"Error fetching PR files: {error}")
    
    python_files = []
    for root, _, files in os.walk(analyze_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    if not python_files:
        return render_template('index.html', error="No Python files found in the PR")
    
    metrics = {}
    metrics['style'] = run_flake8(analyze_dir)
    metrics['quality'] = run_pylint(analyze_dir)
    metrics['complexity'] = run_radon(analyze_dir)
    metrics['security'] = run_bandit(analyze_dir)
    
    report_path = generate_report(metrics, f"{owner}/{repo} PR#{pr_number}")
    
    return send_file(report_path, as_attachment=True, download_name=f"code_quality_report_{owner}_{repo}_PR{pr_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
