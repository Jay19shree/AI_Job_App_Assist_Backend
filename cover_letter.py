"""
cover_letter.py
---------------
Generates a professional cover letter from structured input.
"""

from pydantic import BaseModel, field_validator


class CoverLetterInput(BaseModel):
    name: str
    role: str
    skills: list[str]

    @field_validator("name", "role")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be empty")
        return v.strip()

    @field_validator("skills")
    @classmethod
    def skills_not_empty(cls, v: list[str]) -> list[str]:
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError("At least one skill is required")
        return cleaned


def generate_cover_letter(name: str, role: str, skills: list[str]) -> str:
    """
    Generate a professional cover letter.

    Args:
        name:   Applicant's full name.
        role:   Job title being applied for.
        skills: List of relevant skills.

    Returns:
        Formatted cover letter as a string.
    """
    data = CoverLetterInput(name=name, role=role, skills=skills)

    skills_text = ", ".join(data.skills[:-1])
    if len(data.skills) > 1:
        skills_text += f", and {data.skills[-1]}"
    else:
        skills_text = data.skills[0]

    return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {data.role} position at your organization. \
With a solid foundation in {skills_text}, I am confident in my ability to make a meaningful \
contribution to your team from day one.

Throughout my career, I have applied these skills to deliver scalable, efficient, and \
maintainable solutions in real-world environments. I thrive in collaborative settings, \
approach challenges with a problem-solving mindset, and am committed to continuous learning \
and professional growth.

I am particularly drawn to this opportunity because it aligns closely with both my technical \
expertise and my passion for building impactful technology. I would welcome the chance to \
discuss how my background and skills can support your team's goals.

Thank you for your time and consideration. I look forward to the possibility of working \
together.

Sincerely,
{data.name}
"""
