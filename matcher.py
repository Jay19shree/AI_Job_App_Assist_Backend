"""
matcher.py
----------
Calculates a resume-to-job-description match score using TF-IDF
cosine similarity.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def match_score(resume: str, job_description: str) -> float:
    """
    Compute the textual similarity between a resume and a job description.

    Uses TF-IDF vectorization and cosine similarity. Both inputs are
    lowercased before comparison.

    Args:
        resume:          Raw resume text.
        job_description: Raw job description text.

    Returns:
        Similarity score as a percentage (0.0 – 100.0), rounded to 2 dp.

    Raises:
        ValueError: If either input is empty after stripping whitespace.
    """
    resume = resume.strip().lower()
    job_description = job_description.strip().lower()

    if not resume:
        raise ValueError("Resume text must not be empty")
    if not job_description:
        raise ValueError("Job description must not be empty")

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    vectors = vectorizer.fit_transform([resume, job_description])

    score: float = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return round(float(score) * 100, 2)
