from typing import List, Tuple

from sentence_transformers import SentenceTransformer, util

from models import CVData, Job

_model = SentenceTransformer('all-MiniLM-L6-v2')


def _semantic_similarity(text1: str, text2: str) -> float:
    embeddings = _model.encode(
        [text1, text2],
        convert_to_tensor=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return float(util.cos_sim(embeddings[0], embeddings[1]).item())


def _skill_similarity(cv_skills: List[str], job_skills: List[str]) -> float:
    if not job_skills or not cv_skills:
        return 0.0
    cv_embeddings = _model.encode(cv_skills, convert_to_tensor=True, show_progress_bar=False)
    job_embeddings = _model.encode(job_skills, convert_to_tensor=True, show_progress_bar=False)
    similarity_matrix = util.cos_sim(job_embeddings, cv_embeddings)
    best_matches = [float(scores.max()) for scores in similarity_matrix]
    return sum(best_matches) / len(job_skills)


def _experience_similarity(cv_years: float, jd_years: int) -> float:
    if jd_years == 0:
        return 1.0
    if cv_years >= jd_years:
        return 1.0
    return (cv_years / jd_years) ** 0.7


def calculate_similarity(cv_data: CVData, job: Job) -> float:
    semantic = _semantic_similarity(cv_data.raw_text, job.requirements)
    skill = _skill_similarity(cv_data.skills, job.skills)
    experience = _experience_similarity(cv_data.experience_years, job.experience_needed)

    return (0.40 * semantic + 0.40 * skill + 0.20 * experience) * 100


def rank_jobs(
    jobs: List[Job], cv_data: CVData, top_k: int = 4
) -> List[Tuple[Job, float]]:
    scored = [(job, calculate_similarity(cv_data, job)) for job in jobs]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
