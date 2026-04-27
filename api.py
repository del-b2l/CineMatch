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

from csp import base_CSP

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

class RecommendationList(BaseModel):
    user_id: int
    recommendations: list[Recommendation]

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

@app.get("/recommendations", response_model=RecommendationList)
def get_recommendations(user_id: int, k: int = 10):
    all_items = set(app_state['train_item_rating'].keys())
    train = app_state['train']
    rated_by_user = set(train[user_id].keys())
    candidates = all_items - rated_by_user
    scores = {}
    for candidate in candidates:
        predicted_label, score_dict = predict_hybrid(user_id, candidate, train, app_state['train_item_rating'],
                                           app_state['item_prior'], app_state['item_likelihood'],
                                           app_state['user_prior'], app_state['user_likelihood'], R)
        scores[candidate] = score_dict
    sorted_scores = sorted(scores.items(), key=lambda x: x[1][max(x[1], key=x[1].get)], reverse=True)[:k]
    return RecommendationList(
        user_id=user_id,
        recommendations=[
            Recommendation(movie_id=movie_id, predicted_rating=max(score_dict, key=score_dict.get))
            for movie_id, score_dict in sorted_scores
        ]
    )

@app.post("/constraints")
def get_constrained_recommendations(constraint: Constraints):
    exclude = {"user_id", "k"}
    user_constraints = {
        k: tuple(v) if isinstance(v, list) else v
        for k, v in constraint.model_dump().items()
        if v is not None and k not in exclude
    }

    candidate_ids, log, msg = base_CSP.csp_filter(base_CSP.movies, user_constraints)
    all_items = set(app_state['train_item_rating'].keys())
    train = app_state['train']
    rated_by_user = set(train[constraint.user_id].keys())
    unrated_movies = all_items - rated_by_user
    candidates = set(candidate_ids) & unrated_movies
    scores = {}
    for candidate in candidates:
        predicted_label, score_dict = predict_hybrid(constraint.user_id, candidate, train, app_state['train_item_rating'],
                                           app_state['item_prior'], app_state['item_likelihood'],
                                           app_state['user_prior'], app_state['user_likelihood'], R)
        scores[candidate] = score_dict
    sorted_scores = sorted(scores.items(), key=lambda x: x[1][max(x[1], key=x[1].get)], reverse=True)[:constraint.k]
    return RecommendationList(
        user_id=constraint.user_id,
        recommendations=[
            Recommendation(movie_id=movie_id, predicted_rating=max(score_dict, key=score_dict.get))
            for movie_id, score_dict in sorted_scores
        ]
    )

