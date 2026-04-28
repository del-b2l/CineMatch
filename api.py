from fastapi import FastAPI
from contextlib import asynccontextmanager
import pickle
import os
import random
from collections import defaultdict

from src.data import build_rating_dicts, train_test_split, build_train_item_ratings
from nbcf.priors import compute_item_priors, compute_user_priors
from nbcf.likelihoods import compute_item_likelihood, compute_user_likelihood
from nbcf.predict import predict_hybrid
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import math
import pandas as pd

from csp import base_CSP
from csp.base_CSP import movies, domains

random.seed(42)

CACHE = 'data/cache'
R = [1, 2, 3, 4, 5]
file_path = "./data/clean/ratings_clean.csv"

def defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_dict(v) for k, v in d.items()}
    return d

app_state = {}

class Recommendation(BaseModel):
    movie_id: int
    predicted_rating: int
    title: str = ""
    genres: str = ""
    release_year: float = 0.0
    confidence: float = 0.0
    explanation: str = ""

class RecommendationList(BaseModel):
    user_id: int
    recommendations: list[Recommendation]
    log: list[str] = []
    message: str = ""
    network_data: dict = {}

class Constraints(BaseModel):
    user_id: int
    k: int = 10
    genre: str | None = None
    language: str | None = None
    runtime: list[str | int] | None = None
    release_year: list[str | int] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(f'{CACHE}/item_likelihood.pkl'):
        train = pickle.load(open(f'{CACHE}/train.pkl', 'rb'))
        test = pickle.load(open(f'{CACHE}/test.pkl', 'rb'))
        item_prior = pickle.load(open(f'{CACHE}/item_prior.pkl', 'rb'))
        user_prior = pickle.load(open(f'{CACHE}/user_prior.pkl', 'rb'))
        item_likelihood = pickle.load(open(f'{CACHE}/item_likelihood.pkl', 'rb'))
        user_likelihood = pickle.load(open(f'{CACHE}/user_likelihood.pkl', 'rb'))

        train_item_rating = build_train_item_ratings(train)
        app_state.update({
            "train": train,
            "train_item_rating": train_item_rating,
            "item_prior": item_prior,
            "user_prior": user_prior,
            "item_likelihood": item_likelihood,
            "user_likelihood": user_likelihood,
        })
    else:
        os.makedirs(CACHE, exist_ok=True)
        user_ratings, item_ratings = build_rating_dicts(file_path)
        train, test = train_test_split(user_ratings)
        train_item_rating = build_train_item_ratings(train)
        item_prior = compute_item_priors(train_item_rating, R)
        user_prior = compute_user_priors(train, R)
        user_likelihood = compute_user_likelihood(train, train_item_rating, R)
        item_likelihood = compute_item_likelihood(train, train_item_rating, R)

        item_likelihood = defaultdict_to_dict(item_likelihood)
        user_likelihood = defaultdict_to_dict(user_likelihood)
        item_prior = defaultdict_to_dict(item_prior)
        user_prior = defaultdict_to_dict(user_prior)
        train = defaultdict_to_dict(train)
        test = defaultdict_to_dict(test)

        pickle.dump(train, open(f'{CACHE}/train.pkl', 'wb'))
        pickle.dump(test, open(f'{CACHE}/test.pkl', 'wb'))
        pickle.dump(user_prior, open(f'{CACHE}/user_prior.pkl', 'wb'))
        pickle.dump(item_prior, open(f'{CACHE}/item_prior.pkl', 'wb'))
        pickle.dump(user_likelihood, open(f'{CACHE}/user_likelihood.pkl', 'wb'))
        pickle.dump(item_likelihood, open(f'{CACHE}/item_likelihood.pkl', 'wb'))

        app_state.update({
            "train": train,
            "train_item_rating": train_item_rating,
            "item_prior": item_prior,
            "user_prior": user_prior,
            "item_likelihood": item_likelihood,
            "user_likelihood": user_likelihood,
        })

    yield
    # cleanup if needed

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _movie_title(movie_id):
    row = movies[movies['movieId'] == movie_id]
    return row.iloc[0]['title'] if not row.empty else f"Movie {movie_id}"


def enrich_recommendations(sorted_scores):
    """
    sorted_scores: list of (movie_id, score_dict, p_evidence, q_evidence, alpha_p, alpha_q)
    """
    recs = []
    for movie_id, score_dict, p_evidence, q_evidence, alpha_p, alpha_q in sorted_scores:
        predicted_rating = max(score_dict, key=score_dict.get)
        movie_row = movies[movies['movieId'] == movie_id]
        title = movie_row.iloc[0]['title'] if not movie_row.empty else "Unknown"
        genres = movie_row.iloc[0]['genres'] if not movie_row.empty else ""
        year = movie_row.iloc[0]['release_year'] if not movie_row.empty else 0.0

        best_score = score_dict[predicted_rating]
        second_best = sorted(score_dict.values(), reverse=True)[1] if len(score_dict) > 1 else best_score - 1
        confidence = min(max(0.0, 50.0 + (best_score - second_best) * 10), 99.9)

        # --- Build justification sentence with P and Q evidences ---
        p_titles = [_movie_title(j) for j, _ in p_evidence]
        q_users  = [f"User {v}" for v, _ in q_evidence]

        if p_titles and q_users:
            p_part = ", ".join(p_titles)
            q_part = ", ".join(q_users)
            explanation = (
                f"You will like \u2018{title}\u2019 because you liked "
                f"{p_part} and it liked to the users {q_part} "
                f"who share interests with you."
            )
        elif p_titles:
            p_part = ", ".join(p_titles)
            explanation = (
                f"You will like \u2018{title}\u2019 because you liked {p_part} "
                f"(item-based evidence, \u03b1={alpha_p:.2f})."
            )
        elif q_users:
            q_part = ", ".join(q_users)
            explanation = (
                f"You will like \u2018{title}\u2019 because of shared taste with "
                f"{q_part} (user-based evidence, \u03b1={alpha_q:.2f})."
            )
        else:
            explanation = (
                f"Predicted {predicted_rating}/5 for \u2018{title}\u2019 via hybrid "
                f"Naive Bayes (\u03b1_P={alpha_p:.2f}, \u03b1_Q={alpha_q:.2f})."
            )

        recs.append(Recommendation(
            movie_id=movie_id,
            predicted_rating=predicted_rating,
            title=title,
            genres=genres,
            release_year=float(year) if not pd.isna(year) else 0.0,
            confidence=round(confidence, 1),
            explanation=explanation
        ))
    return recs

@app.get("/movies/domains")
def get_domains():
    import math
    safe_domains = {}
    for k, v in domains.items():
        if k == 'release_year':
            safe_domains[k] = [int(x) for x in v if not math.isnan(x)]
        elif k == 'genre':
            safe_domains[k] = [g for g in list(v) if g and g.lower() != 'unknown']
        else:
            safe_domains[k] = list(v)
            
    # Include max_user_id from training data
    train_users = list(app_state.get('train', {}).keys())
    max_user = max(train_users) if train_users else 1
    safe_domains['max_user_id'] = max_user
    
    return safe_domains

@app.get("/movies")
def get_movies(limit: int = 100):
    return {"movies": movies.head(limit).to_dict(orient="records")}


@app.get("/recommendations", response_model=RecommendationList)
def get_recommendations(user_id: int, k: int = 10):
    all_items = set(app_state['train_item_rating'].keys())
    train = app_state['train']
    rated_by_user = set(train.get(user_id, {}).keys())
    candidates = all_items - rated_by_user

    raw_scores = {}  # candidate -> (score_dict, p_ev, q_ev, alpha_p, alpha_q)
    for candidate in candidates:
        best_y, score_dict, p_ev, q_ev, alpha_p, alpha_q = predict_hybrid(
            user_id, candidate, train, app_state['train_item_rating'],
            app_state['item_prior'], app_state['item_likelihood'],
            app_state['user_prior'], app_state['user_likelihood'], R)
        raw_scores[candidate] = (score_dict, p_ev, q_ev, alpha_p, alpha_q)

    sorted_candidates = sorted(
        raw_scores.items(),
        key=lambda x: x[1][0][max(x[1][0], key=x[1][0].get)],
        reverse=True
    )[:k]

    # Build enrichment input and per-item log lines
    enrichment_input = []
    log_lines = [
        "[Hybrid] Naive Bayes recommender initialised.",
        f"[Hybrid] Scoring {len(candidates)} candidate movies for User {user_id}...",
    ]
    for movie_id, (score_dict, p_ev, q_ev, alpha_p, alpha_q) in sorted_candidates:
        enrichment_input.append((movie_id, score_dict, p_ev, q_ev, alpha_p, alpha_q))
        best_y = max(score_dict, key=score_dict.get)
        title  = _movie_title(movie_id)
        p_names = ", ".join(_movie_title(j) for j, _ in p_ev) or "none"
        q_names = ", ".join(f"User {v}" for v, _ in q_ev) or "none"
        log_lines.append(
            f"[Hybrid] '{title}' → ★{best_y} | "
            f"α_P={alpha_p:.2f} | α_Q={alpha_q:.2f} | "
            f"P=[{p_names}] | Q=[{q_names}]"
        )

    recs = enrich_recommendations(enrichment_input)

    # Generate network visualization for the #1 recommendation
    net_data = {}
    if recs:
        best_rec = recs[0]
        nodes = [{"id": f"M{best_rec.movie_id}", "name": best_rec.title, "group": 1, "val": 8}]
        links = []

        nodes.append({"id": "Prior", "name": "Item Prior", "group": 3, "val": 4})
        links.append({"source": "Prior", "target": f"M{best_rec.movie_id}", "label": "P(r_i)"})

        item_ratings = app_state['train_item_rating'].get(best_rec.movie_id, {})
        _, _, q_ev_top, _, _ = raw_scores[best_rec.movie_id]
        q_users_top = [v for v, _ in q_ev_top] or list(item_ratings.keys())[:3]
        for u in q_users_top:
            nodes.append({"id": f"U{u}", "name": f"User {u}", "group": 2, "val": 5})
            links.append({"source": f"U{u}", "target": f"M{best_rec.movie_id}", "label": "Q: Co-rater"})

        _, p_ev_top, _, _, _ = raw_scores[best_rec.movie_id]
        for j, r_uj in p_ev_top:
            t = _movie_title(j)
            nodes.append({"id": f"M{j}", "name": t, "group": 4, "val": 5})
            links.append({"source": f"M{j}", "target": f"M{best_rec.movie_id}",
                          "label": f"P: rated {r_uj}★"})

        net_data = {"nodes": nodes, "links": links}

    return RecommendationList(
        user_id=user_id,
        recommendations=recs,
        log=log_lines,
        message=f"[Hybrid] Found top {k} recommendations for User {user_id}.",
        network_data=net_data
    )

@app.post("/constraints")
def get_constrained_recommendations(constraint: Constraints):
    exclude = {"user_id", "k"}
    user_constraints = {
        k: tuple(v) if isinstance(v, list) else v
        for k, v in constraint.model_dump().items()
        if v is not None and k not in exclude
    }

    candidate_ids, csp_log, msg = base_CSP.csp_filter(base_CSP.movies, user_constraints)
    all_items = set(app_state['train_item_rating'].keys())
    train = app_state['train']
    rated_by_user = set(train.get(constraint.user_id, {}).keys())
    unrated_movies = all_items - rated_by_user
    candidates = set(candidate_ids) & unrated_movies

    raw_scores = {}
    for candidate in candidates:
        best_y, score_dict, p_ev, q_ev, alpha_p, alpha_q = predict_hybrid(
            constraint.user_id, candidate, train, app_state['train_item_rating'],
            app_state['item_prior'], app_state['item_likelihood'],
            app_state['user_prior'], app_state['user_likelihood'], R)
        raw_scores[candidate] = (score_dict, p_ev, q_ev, alpha_p, alpha_q)

    sorted_candidates = sorted(
        raw_scores.items(),
        key=lambda x: x[1][0][max(x[1][0], key=x[1][0].get)],
        reverse=True
    )[:constraint.k]

    enrichment_input = []
    hybrid_log = list(csp_log)  # keep CSP log lines first
    hybrid_log.append(f"[Hybrid] Scoring {len(candidates)} CSP-filtered candidates for User {constraint.user_id}...")
    for movie_id, (score_dict, p_ev, q_ev, alpha_p, alpha_q) in sorted_candidates:
        enrichment_input.append((movie_id, score_dict, p_ev, q_ev, alpha_p, alpha_q))
        best_y = max(score_dict, key=score_dict.get)
        title  = _movie_title(movie_id)
        p_names = ", ".join(_movie_title(j) for j, _ in p_ev) or "none"
        q_names = ", ".join(f"User {v}" for v, _ in q_ev) or "none"
        hybrid_log.append(
            f"[Hybrid] '{title}' → ★{best_y} | "
            f"α_P={alpha_p:.2f} | α_Q={alpha_q:.2f} | "
            f"P=[{p_names}] | Q=[{q_names}]"
        )

    recs = enrich_recommendations(enrichment_input)

    # Network visualisation for the #1 constrained recommendation
    net_data = {}
    if recs:
        best_rec = recs[0]
        nodes = [{"id": f"M{best_rec.movie_id}", "name": best_rec.title, "group": 1, "val": 8}]
        links = []

        nodes.append({"id": "Prior", "name": "Item Prior", "group": 3, "val": 4})
        links.append({"source": "Prior", "target": f"M{best_rec.movie_id}", "label": "P(r_i)"})

        item_ratings = app_state['train_item_rating'].get(best_rec.movie_id, {})
        _, _, q_ev_top, _, _ = raw_scores[best_rec.movie_id]
        q_users_top = [v for v, _ in q_ev_top] or list(item_ratings.keys())[:3]
        for u in q_users_top:
            nodes.append({"id": f"U{u}", "name": f"User {u}", "group": 2, "val": 5})
            links.append({"source": f"U{u}", "target": f"M{best_rec.movie_id}", "label": "Q: Co-rater"})

        _, p_ev_top, _, _, _ = raw_scores[best_rec.movie_id]
        for j, r_uj in p_ev_top:
            t = _movie_title(j)
            nodes.append({"id": f"M{j}", "name": t, "group": 4, "val": 5})
            links.append({"source": f"M{j}", "target": f"M{best_rec.movie_id}",
                          "label": f"P: rated {r_uj}★"})

        net_data = {"nodes": nodes, "links": links}

    return RecommendationList(
        user_id=constraint.user_id,
        recommendations=recs,
        log=hybrid_log,
        message=msg,
        network_data=net_data
    )

