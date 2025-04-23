"""Python code analyzer implementation."""
import os
import re
import subprocess
from app import LanguageAnalyzer
from constants import PYTHON_EXTENSIONS

class PythonAnalyzer(LanguageAnalyzer):
    """Python language analyzer using Flake8, Pylint, Radon, and Bandit."""
    
    @staticmethod
    def get_extensions():
        """Return file extensions supported by this analyzer."""
        return PYTHON_EXTENSIONS
    
    def analyze_style(self, directory):
        """Run flake8 on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            python_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
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
    
    def analyze_quality(self, directory):
        """Run pylint on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            python_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
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
    
    def analyze_complexity(self, directory):
        """Run radon on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            python_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
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
    
    def analyze_security(self, directory):
        """Run bandit on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            python_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
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
