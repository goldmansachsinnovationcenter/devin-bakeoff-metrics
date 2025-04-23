"""Base interface for language analyzers."""

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
