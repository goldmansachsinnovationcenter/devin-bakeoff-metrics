"""JavaScript/TypeScript code analyzer implementation."""
import os
import re
import subprocess
import json
import tempfile
from language_analyzer import LanguageAnalyzer
from constants import JAVASCRIPT_EXTENSIONS, TYPESCRIPT_EXTENSIONS

class JavaScriptAnalyzer(LanguageAnalyzer):
    """JavaScript language analyzer using ESLint, JSHint, and npm audit."""
    
    @staticmethod
    def get_extensions():
        """Return file extensions supported by this analyzer."""
        return JAVASCRIPT_EXTENSIONS + TYPESCRIPT_EXTENSIONS
    
    def analyze_style(self, directory):
        """Run ESLint on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            js_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
                        js_files.append(os.path.join(root, file))
            
            if not js_files:
                return {'score': 10.0, 'issues': ['No JavaScript/TypeScript files found']}
            
            eslint_config = os.path.join(directory, '.eslintrc.json')
            config_created = False
            
            if not os.path.exists(eslint_config):
                with open(eslint_config, 'w') as f:
                    json.dump({
                        "extends": "eslint:recommended",
                        "parserOptions": {
                            "ecmaVersion": 2020,
                            "sourceType": "module"
                        },
                        "env": {
                            "browser": True,
                            "node": True,
                            "es6": True
                        }
                    }, f)
                config_created = True
            
            total_issues = 0
            
            for js_file in js_files:
                try:
                    output = subprocess.check_output(['npx', 'eslint', '--format=json', js_file], 
                                                    stderr=subprocess.STDOUT, text=True)
                    lint_results = json.loads(output)
                    
                    for file_result in lint_results:
                        for message in file_result.get('messages', []):
                            issue = f"{js_file}:{message.get('line')}:{message.get('column')} - {message.get('message')} ({message.get('ruleId')})"
                            result['issues'].append(issue)
                            total_issues += 1
                            
                except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                    if isinstance(e, subprocess.CalledProcessError):
                        output = e.output
                        try:
                            lint_results = json.loads(output)
                            for file_result in lint_results:
                                for message in file_result.get('messages', []):
                                    issue = f"{js_file}:{message.get('line')}:{message.get('column')} - {message.get('message')} ({message.get('ruleId')})"
                                    result['issues'].append(issue)
                                    total_issues += 1
                        except json.JSONDecodeError:
                            result['issues'].append(f"Error parsing ESLint output for {js_file}: {output}")
                    else:
                        result['issues'].append(f"Error running ESLint on {js_file}: {str(e)}")
            
            if config_created:
                os.remove(eslint_config)
            
            avg_issues = total_issues / len(js_files) if js_files else 0
            result['score'] = max(0, 10 - min(10, avg_issues))
            
        except Exception as e:
            result['issues'].append(f"Error running ESLint: {str(e)}")
            result['score'] = 0
        
        return result
    
    def analyze_quality(self, directory):
        """Run JSHint on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            js_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
                        js_files.append(os.path.join(root, file))
            
            if not js_files:
                return {'score': 10.0, 'issues': ['No JavaScript/TypeScript files found']}
            
            total_issues = 0
            
            for js_file in js_files:
                try:
                    output = subprocess.check_output(['npx', 'jshint', '--reporter=json', js_file], 
                                                    stderr=subprocess.STDOUT, text=True)
                    lint_results = json.loads(output)
                    
                    for issue in lint_results:
                        issue_str = f"{js_file}:{issue.get('line')}:{issue.get('col')} - {issue.get('reason')}"
                        result['issues'].append(issue_str)
                        total_issues += 1
                            
                except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                    if isinstance(e, subprocess.CalledProcessError):
                        try:
                            output = e.output
                            lint_results = json.loads(output)
                            for issue in lint_results:
                                issue_str = f"{js_file}:{issue.get('line')}:{issue.get('col')} - {issue.get('reason')}"
                                result['issues'].append(issue_str)
                                total_issues += 1
                        except json.JSONDecodeError:
                            result['issues'].append(f"Error parsing JSHint output for {js_file}")
                    else:
                        result['issues'].append(f"Error running JSHint on {js_file}: {str(e)}")
            
            avg_issues = total_issues / len(js_files) if js_files else 0
            result['score'] = max(0, 10 - min(10, avg_issues * 2))  # Higher weight for quality issues
            
        except Exception as e:
            result['issues'].append(f"Error running JSHint: {str(e)}")
            result['score'] = 0
        
        return result
    
    def analyze_complexity(self, directory):
        """Analyze code complexity using ESLint complexity plugin."""
        result = {'score': 0, 'issues': []}
        
        try:
            js_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
                        js_files.append(os.path.join(root, file))
            
            if not js_files:
                return {'score': 10.0, 'issues': ['No JavaScript/TypeScript files found']}
            
            eslint_config = os.path.join(directory, '.eslintrc.json')
            config_created = False
            
            if not os.path.exists(eslint_config):
                with open(eslint_config, 'w') as f:
                    json.dump({
                        "plugins": ["complexity"],
                        "rules": {
                            "complexity": ["error", 10]
                        }
                    }, f)
                config_created = True
            
            total_complexity = 0
            file_count = 0
            
            for js_file in js_files:
                try:
                    subprocess.run(['npm', 'install', 'eslint-plugin-complexity', '--no-save'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=directory, check=False)
                    
                    output = subprocess.check_output(['npx', 'eslint', '--plugin', 'complexity', 
                                                     '--rule', 'complexity: ["error", 10]', 
                                                     '--format=json', js_file], 
                                                    stderr=subprocess.STDOUT, text=True)
                    lint_results = json.loads(output)
                    
                    complexity_issues = 0
                    for file_result in lint_results:
                        for message in file_result.get('messages', []):
                            if message.get('ruleId') == 'complexity':
                                complexity = int(re.search(r'has a complexity of (\d+)', message.get('message', '')).group(1))
                                issue = f"{js_file}:{message.get('line')}:{message.get('column')} - {message.get('message')}"
                                result['issues'].append(issue)
                                total_complexity += complexity
                                complexity_issues += 1
                    
                    if complexity_issues > 0:
                        file_count += 1
                            
                except (subprocess.CalledProcessError, json.JSONDecodeError, AttributeError) as e:
                    result['issues'].append(f"Error analyzing complexity for {js_file}: {str(e)}")
            
            if config_created:
                os.remove(eslint_config)
            
            avg_complexity = total_complexity / file_count if file_count > 0 else 0
            result['score'] = max(0, 10 - min(10, avg_complexity / 2))
            
        except Exception as e:
            result['issues'].append(f"Error analyzing complexity: {str(e)}")
            result['score'] = 0
        
        return result
    
    def analyze_security(self, directory):
        """Run npm audit on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            js_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
                        js_files.append(os.path.join(root, file))
            
            if not js_files:
                return {'score': 10.0, 'issues': ['No JavaScript/TypeScript files found']}
            
            package_json = os.path.join(directory, 'package.json')
            if not os.path.exists(package_json):
                result['issues'].append("No package.json found, skipping security audit")
                result['score'] = 5.0  # Neutral score since we can't perform a proper audit
                return result
            
            try:
                output = subprocess.check_output(['npm', 'audit', '--json'], 
                                               stderr=subprocess.STDOUT, text=True, cwd=directory)
                audit_results = json.loads(output)
                
                vulnerabilities = audit_results.get('vulnerabilities', {})
                total_issues = sum(v.get('count', 0) for v in vulnerabilities.values())
                
                for vuln_name, vuln_data in vulnerabilities.items():
                    severity = vuln_data.get('severity', 'unknown')
                    count = vuln_data.get('count', 0)
                    issue = f"Found {count} {severity} severity vulnerability(ies) in {vuln_name}"
                    result['issues'].append(issue)
                
                if total_issues == 0:
                    result['issues'].append("No security vulnerabilities found")
                    result['score'] = 10.0
                else:
                    weighted_issues = 0
                    severity_weights = {'critical': 4, 'high': 3, 'moderate': 2, 'low': 1}
                    for vuln_data in vulnerabilities.values():
                        severity = vuln_data.get('severity', 'low')
                        count = vuln_data.get('count', 0)
                        weighted_issues += count * severity_weights.get(severity, 1)
                    
                    result['score'] = max(0, 10 - min(10, weighted_issues / 2))
                
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                result['issues'].append(f"Error running npm audit: {str(e)}")
                result['score'] = 0
            
        except Exception as e:
            result['issues'].append(f"Error in security analysis: {str(e)}")
            result['score'] = 0
        
        return result
