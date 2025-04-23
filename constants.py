"""Constants used throughout the application."""

PYTHON_EXTENSIONS = ['.py']
JAVASCRIPT_EXTENSIONS = ['.js', '.jsx']
TYPESCRIPT_EXTENSIONS = ['.ts', '.tsx']
JAVA_EXTENSIONS = ['.java']
CPP_EXTENSIONS = ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp']
GO_EXTENSIONS = ['.go']
RUBY_EXTENSIONS = ['.rb']
PHP_EXTENSIONS = ['.php']
CSHARP_EXTENSIONS = ['.cs']

PYTHON = 'Python'
JAVASCRIPT = 'JavaScript'
TYPESCRIPT = 'TypeScript'
JAVA = 'Java'
CPP = 'C/C++'
GO = 'Go'
RUBY = 'Ruby'
PHP = 'PHP'
CSHARP = 'C#'

LANGUAGE_BY_EXTENSION = {
    **{ext: PYTHON for ext in PYTHON_EXTENSIONS},
    **{ext: JAVASCRIPT for ext in JAVASCRIPT_EXTENSIONS},
    **{ext: TYPESCRIPT for ext in TYPESCRIPT_EXTENSIONS},
    **{ext: JAVA for ext in JAVA_EXTENSIONS},
    **{ext: CPP for ext in CPP_EXTENSIONS},
    **{ext: GO for ext in GO_EXTENSIONS},
    **{ext: RUBY for ext in RUBY_EXTENSIONS},
    **{ext: PHP for ext in PHP_EXTENSIONS},
    **{ext: CSHARP for ext in CSHARP_EXTENSIONS},
}

ALL_EXTENSIONS = (
    PYTHON_EXTENSIONS +
    JAVASCRIPT_EXTENSIONS +
    TYPESCRIPT_EXTENSIONS +
    JAVA_EXTENSIONS +
    CPP_EXTENSIONS +
    GO_EXTENSIONS +
    RUBY_EXTENSIONS +
    PHP_EXTENSIONS +
    CSHARP_EXTENSIONS
)

DEFAULT_SCORE = 10.0
DEFAULT_MESSAGE = 'No files found for this language'
