"""
resume_parser.py
----------------
Extracts skills from resume text using keyword matching.
The SKILLS_DB can be extended or replaced with a database-driven list.
"""

import re

# ---------------------------------------------------------------------------
# Skills database — grouped by category for maintainability
# ---------------------------------------------------------------------------

SKILLS_DB: list[str] = sorted(
    [
        # Languages
        "python", "java", "javascript", "typescript", "c", "c++", "c#",
        "go", "rust", "kotlin", "swift", "r", "scala", "php", "ruby",
        # Web / Frontend
        "react", "next.js", "vue", "angular", "html", "css", "tailwind",
        "bootstrap", "redux", "graphql", "rest api",
        # Backend / Frameworks
        "node", "fastapi", "django", "flask", "express", "spring boot",
        "asp.net",
        # Databases
        "mongodb", "postgresql", "mysql", "sqlite", "redis", "elasticsearch",
        "firebase",
        # Cloud / DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "ci/cd", "github actions", "jenkins",
        # Data / AI / ML
        "machine learning", "deep learning", "nlp", "computer vision",
        "data analysis", "data science", "pandas", "numpy", "scikit-learn",
        "tensorflow", "pytorch", "keras", "tableau", "power bi",
        # General
        "sql", "git", "linux", "agile", "scrum",
    ],
    key=len,
    reverse=True,   # match longer phrases first (e.g. "machine learning" before "machine")
)


def extract_skills(text: str) -> list[str]:
    """
    Extract known skills from resume text using whole-word regex matching.

    Args:
        text: Raw text extracted from a resume.

    Returns:
        Sorted list of unique skills found in the text.
    """
    if not text or not text.strip():
        return []

    normalized = text.lower()
    found: set[str] = set()

    for skill in SKILLS_DB:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalized):
            found.add(skill)

    return sorted(found)
