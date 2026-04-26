# main.py
import os
import pickle
import random
from collections import defaultdict

from src.data import build_rating_dicts, train_test_split, build_train_item_ratings
from nbcf.priors import compute_item_priors, compute_user_priors
from nbcf.likelihoods import compute_item_likelihood, compute_user_likelihood

random.seed(42)

CACHE = 'data/cache'
R = [1, 2, 3, 4, 5]
file_path = "./data/clean/ratings_clean.csv"

def defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_dict(v) for k, v in d.items()}
    return d

# Step 1: Load or compute
if os.path.exists(f'{CACHE}/item_likelihood.pkl'):
    train = pickle.load(open(f'{CACHE}/train.pkl', 'rb'))
    test = pickle.load(open(f'{CACHE}/test.pkl', 'rb'))
    item_prior = pickle.load(open(f'{CACHE}/item_prior.pkl', 'rb'))
    user_prior = pickle.load(open(f'{CACHE}/user_prior.pkl', 'rb'))
    item_likelihood = pickle.load(open(f'{CACHE}/item_likelihood.pkl', 'rb'))
    user_likelihood = pickle.load(open(f'{CACHE}/user_likelihood.pkl', 'rb'))
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
