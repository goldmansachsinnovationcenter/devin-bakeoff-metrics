"""Java code analyzer implementation."""
import os
import re
import subprocess
import tempfile
from language_analyzer import LanguageAnalyzer
from constants import JAVA_EXTENSIONS

class JavaAnalyzer(LanguageAnalyzer):
    """Java language analyzer using Checkstyle, PMD, and SpotBugs."""
    
    @staticmethod
    def get_extensions():
        """Return file extensions supported by this analyzer."""
        return JAVA_EXTENSIONS
    
    def analyze_style(self, directory):
        """Run Checkstyle on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            java_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
                        java_files.append(os.path.join(root, file))
            
            if not java_files:
                return {'score': 10.0, 'issues': ['No Java files found']}
            
            temp_config = tempfile.NamedTemporaryFile(suffix='.xml', delete=False)
            with open(temp_config.name, 'w') as f:
                f.write('''<?xml version="1.0"?>
<!DOCTYPE module PUBLIC "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN" "https://checkstyle.org/dtds/configuration_1_3.dtd">
<module name="Checker">
  <module name="TreeWalker">
    <module name="MissingSwitchDefault"/>
    <module name="FallThrough"/>
    <module name="VisibilityModifier"/>
    <module name="EmptyBlock"/>
    <module name="EmptyCatchBlock"/>
    <module name="AvoidStarImport"/>
    <module name="UnusedImports"/>
    <module name="OneStatementPerLine"/>
    <module name="OverloadMethodsDeclarationOrder"/>
    <module name="PackageDeclaration"/>
    <module name="MemberName"/>
    <module name="CyclomaticComplexity"/>
  </module>
</module>''')
            
            total_issues = 0
            
            for java_file in java_files:
                try:
                    checkstyle_path = os.path.expanduser('~/checkstyle.jar')
                    if not os.path.exists(checkstyle_path):
                        result['issues'].append(f"Checkstyle JAR not found at {checkstyle_path}, skipping style analysis")
                        result['score'] = 5.0  # Neutral score
                        return result
                    
                    output = subprocess.check_output(['java', '-jar', checkstyle_path, '-c', 
                                                     temp_config.name, java_file], 
                                                    stderr=subprocess.STDOUT, text=True)
                    
                    lines = output.strip().split('\n')
                    if lines and lines[0]:  # If there are issues
                        for line in lines:
                            if re.match(r'^\[ERROR\]', line):
                                result['issues'].append(line)
                                total_issues += 1
                            
                except subprocess.CalledProcessError as e:
                    output = e.output
                    lines = output.strip().split('\n')
                    for line in lines:
                        if re.match(r'^\[ERROR\]', line):
                            result['issues'].append(line)
                            total_issues += 1
            
            os.unlink(temp_config.name)
            
            avg_issues = total_issues / len(java_files) if java_files else 0
            result['score'] = max(0, 10 - min(10, avg_issues))
            
        except Exception as e:
            result['issues'].append(f"Error running Checkstyle: {str(e)}")
            result['score'] = 0
        
        return result
    
    def analyze_quality(self, directory):
        """Run PMD on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            java_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
                        java_files.append(os.path.join(root, file))
            
            if not java_files:
                return {'score': 10.0, 'issues': ['No Java files found']}
            
            try:
                subprocess.check_output(['pmd', '--version'], stderr=subprocess.STDOUT, text=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                result['issues'].append("PMD not found, skipping quality analysis")
                result['score'] = 5.0  # Neutral score
                return result
            
            file_list = tempfile.NamedTemporaryFile(delete=False)
            with open(file_list.name, 'w') as f:
                for java_file in java_files:
                    f.write(f"{java_file}\n")
            
            total_issues = 0
            
            try:
                output = subprocess.check_output(['pmd', 'check', '-f', 'text', '-R', 'rulesets/java/quickstart.xml', 
                                               '-filelist', file_list.name], 
                                              stderr=subprocess.STDOUT, text=True)
                
                lines = output.strip().split('\n')
                if lines and lines[0]:  # If there are issues
                    for line in lines:
                        result['issues'].append(line)
                        total_issues += 1
                
            except subprocess.CalledProcessError as e:
                output = e.output
                lines = output.strip().split('\n')
                for line in lines:
                    if not line.startswith('Usage:') and not line.startswith('Options:'):
                        result['issues'].append(line)
                        total_issues += 1
            
            os.unlink(file_list.name)
            
            avg_issues = total_issues / len(java_files) if java_files else 0
            result['score'] = max(0, 10 - min(10, avg_issues))
            
        except Exception as e:
            result['issues'].append(f"Error running PMD: {str(e)}")
            result['score'] = 0
        
        return result
    
    def analyze_complexity(self, directory):
        """Analyze code complexity using JavaNCSS."""
        result = {'score': 0, 'issues': []}
        
        try:
            java_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
                        java_files.append(os.path.join(root, file))
            
            if not java_files:
                return {'score': 10.0, 'issues': ['No Java files found']}
            
            total_complexity = 0
            file_count = 0
            
            for java_file in java_files:
                try:
                    with open(java_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if_count = len(re.findall(r'\bif\s*\(', content))
                    for_count = len(re.findall(r'\bfor\s*\(', content))
                    while_count = len(re.findall(r'\bwhile\s*\(', content))
                    switch_count = len(re.findall(r'\bswitch\s*\(', content))
                    catch_count = len(re.findall(r'\bcatch\s*\(', content))
                    
                    complexity = if_count + for_count + while_count + switch_count + catch_count
                    
                    if complexity > 0:
                        file_complexity = complexity / (len(content.split('\n')) / 100)  # Normalize by file size
                        result['issues'].append(f"{java_file}: Estimated complexity: {complexity} statements")
                        total_complexity += file_complexity
                        file_count += 1
                
                except Exception as e:
                    result['issues'].append(f"Error analyzing complexity for {java_file}: {str(e)}")
            
            if file_count == 0:
                result['score'] = 10.0
                result['issues'].append("No complexity issues found")
            else:
                avg_complexity = total_complexity / file_count
                result['score'] = max(0, 10 - min(10, avg_complexity / 2))
            
        except Exception as e:
            result['issues'].append(f"Error analyzing complexity: {str(e)}")
            result['score'] = 0
        
        return result
    
    def analyze_security(self, directory):
        """Run SpotBugs on the directory and return the results."""
        result = {'score': 0, 'issues': []}
        
        try:
            java_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.get_extensions()):
                        java_files.append(os.path.join(root, file))
            
            if not java_files:
                return {'score': 10.0, 'issues': ['No Java files found']}
            
            spotbugs_path = os.path.expanduser('~/spotbugs/lib/spotbugs.jar')
            if not os.path.exists(spotbugs_path):
                result['issues'].append(f"SpotBugs JAR not found at {spotbugs_path}, using alternative security analysis")
                
                security_patterns = [
                    (r'\.exec\s*\(', 'Potential command injection'),
                    (r'\.executeQuery\s*\(.*\+', 'Potential SQL injection'),
                    (r'\.executeUpdate\s*\(.*\+', 'Potential SQL injection'),
                    (r'\.createStatement\s*\(.*\+', 'Potential SQL injection'),
                    (r'\.prepareStatement\s*\(.*\+', 'Potential SQL injection'),
                    (r'\.createQuery\s*\(.*\+', 'Potential HQL/JPQL injection'),
                    (r'\.eval\s*\(', 'Potential code injection'),
                    (r'\.deserialize\s*\(', 'Potential deserialization vulnerability'),
                    (r'\.readObject\s*\(', 'Potential deserialization vulnerability'),
                    (r'\.readUnshared\s*\(', 'Potential deserialization vulnerability'),
                    (r'\.readExternal\s*\(', 'Potential deserialization vulnerability'),
                    (r'\.readResolve\s*\(', 'Potential deserialization vulnerability'),
                    (r'\.readObjectNoData\s*\(', 'Potential deserialization vulnerability'),
                    (r'\.load\s*\(.*\.class\.getResource', 'Potential unsafe resource loading'),
                    (r'\.printStackTrace\s*\(', 'Information leakage through stack traces'),
                    (r'System\.out\.print', 'Debug information leakage'),
                    (r'\.getParameter\s*\(.*\)', 'Unvalidated input'),
                    (r'\.getHeader\s*\(.*\)', 'Unvalidated header'),
                    (r'\.getCookie\s*\(.*\)', 'Unvalidated cookie'),
                    (r'\.getAttribute\s*\(.*\)', 'Unvalidated attribute'),
                ]
                
                total_issues = 0
                
                for java_file in java_files:
                    try:
                        with open(java_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        for pattern, issue_type in security_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                result['issues'].append(f"{java_file}: {issue_type} ({len(matches)} occurrences)")
                                total_issues += len(matches)
                    
                    except Exception as e:
                        result['issues'].append(f"Error analyzing security for {java_file}: {str(e)}")
                
                if total_issues == 0:
                    result['issues'].append("No security issues found")
                    result['score'] = 10.0
                else:
                    result['score'] = max(0, 10 - min(10, total_issues / 2))
                
                return result
            
            class_dir = tempfile.mkdtemp()
            
            for java_file in java_files:
                try:
                    subprocess.check_output(['javac', '-d', class_dir, java_file], 
                                          stderr=subprocess.STDOUT, text=True)
                except subprocess.CalledProcessError:
                    pass
            
            try:
                output = subprocess.check_output(['java', '-jar', spotbugs_path, '-textui', '-effort:max', 
                                               '-low', class_dir], 
                                              stderr=subprocess.STDOUT, text=True)
                
                lines = output.strip().split('\n')
                issues_found = False
                
                for line in lines:
                    if 'Warnings generated:' in line:
                        issues_found = True
                    if issues_found and line.strip() and not line.startswith('Warnings generated:'):
                        result['issues'].append(line)
                
                issue_count = len(result['issues'])
                
                if issue_count == 0:
                    result['issues'].append("No security issues found")
                    result['score'] = 10.0
                else:
                    result['score'] = max(0, 10 - min(10, issue_count / 2))
                
            except subprocess.CalledProcessError as e:
                result['issues'].append(f"Error running SpotBugs: {str(e)}")
                result['score'] = 0
            
            import shutil
            shutil.rmtree(class_dir, ignore_errors=True)
            
        except Exception as e:
            result['issues'].append(f"Error in security analysis: {str(e)}")
            result['score'] = 0
        
        return result
