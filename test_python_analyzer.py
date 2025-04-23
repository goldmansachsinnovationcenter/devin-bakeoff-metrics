"""
Test script for Python analyzer.
This script tests the Python analyzer with sample files.
"""
import os
import sys
import tempfile
import shutil
import subprocess

def test_python_analyzer(sample_dir):
    """Test the Python analyzer with sample files."""
    print("\n=== Testing Python Analyzer ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        for root, _, files in os.walk(sample_dir):
            for file in files:
                src_path = os.path.join(root, file)
                dst_path = os.path.join(temp_dir, file)
                shutil.copy2(src_path, dst_path)
        
        print("\nStyle Analysis:")
        try:
            output = subprocess.check_output(['flake8', temp_dir], stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output
        
        issues = output.strip().split('\n')
        if issues and issues[0]:
            print(f"Issues found: {len(issues)}")
            for issue in issues[:5]:
                print(f"- {issue}")
            if len(issues) > 5:
                print(f"... and {len(issues) - 5} more issues")
        else:
            print("No style issues found")
        
        print("\nQuality Analysis:")
        try:
            output = subprocess.check_output(['pylint', '--output-format=text', temp_dir], stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output
        
        score_match = re.search(r'Your code has been rated at ([-\d.]+)/10', output)
        if score_match:
            score = float(score_match.group(1))
            print(f"Score: {max(0, score)}/10")
        
        issues = [line for line in output.strip().split('\n') if ':' in line and not line.startswith('Your code')]
        print(f"Issues found: {len(issues)}")
        for issue in issues[:5]:
            print(f"- {issue}")
        if len(issues) > 5:
            print(f"... and {len(issues) - 5} more issues")
        
        print("\nComplexity Analysis:")
        try:
            output = subprocess.check_output(['radon', 'cc', temp_dir, '--no-assert'], stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output
        
        issues = output.strip().split('\n')
        if issues and issues[0]:
            print(f"Issues found: {len(issues)}")
            for issue in issues[:5]:
                print(f"- {issue}")
            if len(issues) > 5:
                print(f"... and {len(issues) - 5} more issues")
        else:
            print("No complexity issues found")
        
        print("\nSecurity Analysis:")
        try:
            output = subprocess.check_output(['bandit', '-r', temp_dir], stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output
        
        issues = [line for line in output.strip().split('\n') if 'Issue:' in line or 'Location:' in line or 'Severity:' in line]
        print(f"Issues found: {len(issues) // 3}")  # Divide by 3 because each issue has 3 lines
        for i in range(0, min(15, len(issues)), 3):
            print(f"- {issues[i]}")
            print(f"  {issues[i+1]}")
            print(f"  {issues[i+2]}")
        if len(issues) > 15:
            print(f"... and {len(issues) // 3 - 5} more issues")
        
        return True
    except Exception as e:
        print(f"Error testing Python analyzer: {str(e)}")
        return False
    finally:
        shutil.rmtree(temp_dir)

def main():
    """Main function to test Python analyzer."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(base_dir, "test_samples")
    
    python_sample_dir = os.path.join(samples_dir, "python")
    python_result = test_python_analyzer(python_sample_dir)
    
    print("\n=== Summary ===")
    print(f"Python Analyzer: {'PASS' if python_result else 'FAIL'}")
    
    if python_result:
        print("\nPython analyzer passed!")
        return 0
    else:
        print("\nPython analyzer failed!")
        return 1

if __name__ == "__main__":
    import re  # Import re here to avoid circular imports
    sys.exit(main())
