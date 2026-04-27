# CineMatch

CineMatch is a movie recommender system that combines:

- Naive Bayes collaborative filtering (user-based + item-based hybrid scoring)
- CSP-style constraint filtering (genre, release year, runtime, language)
- A FastAPI service for serving recommendations

The project uses MovieLens-style ratings data and produces ranked movie suggestions, optionally narrowed by user constraints.

## Repository Structure

- api.py: FastAPI app with recommendation endpoints
- main.py: offline training and cache generation for recommendation model parameters
- data_prep.py: data cleaning script to build cleaned movies and ratings CSV files
- verification.py: cache inspection helper for quick sanity checks
- src/data.py: data loading and train-test split helpers
- nbcf/priors.py: prior probability estimation
- nbcf/likelihoods.py: likelihood estimation for user-based and item-based models
- nbcf/predict.py: user-based, item-based, and hybrid prediction logic
- csp/base_CSP.py: CSP-style filtering and simple backtracking-based relaxation
- csp/test_CSP.py: script-style tests for CSP filtering behavior
- data/raw/: raw source datasets
- data/clean/: cleaned input data for model training and CSP filtering
- data/cache/: serialized model artifacts used by the API and scripts

## How It Works

## 1) Data Preparation

The cleaning script writes:

- data/clean/movies_clean.csv
- data/clean/ratings_clean.csv

Expected cleaned schema:

- movies_clean.csv: movieId, title, genres, release_year, runtime, language
- ratings_clean.csv: userId, movieId, rating

## 2) Probabilistic Model (NBCF)

Training builds:

- Item priors P(r_i = y)
- User priors P(r_u = y)
- Item likelihoods P(r_j = k | r_i = y)
- User likelihoods P(r_v = k | r_u = y)

Hybrid prediction combines user-based and item-based log scores and returns the most likely rating class in 1..5.

## 3) Constraint Filtering (CSP Layer)

The CSP module filters candidate movies using constraints such as:

- genre == Action
- release_year >= 2000
- runtime <= 120
- language == en

If no movie satisfies all constraints, the module tries relaxing one constraint at a time and returns the first relaxation that yields results.

## 4) API Serving

On startup, the API loads cached artifacts from data/cache/. If cache is missing, it computes artifacts from data/clean/ratings_clean.csv and saves them.

Recommendation flow:

1. Gather unrated movies for a user.
2. Optionally apply CSP filtering via constraints.
3. Predict scores with hybrid NBCF.
4. Return top-k movie recommendations.

## Installation

1. Create and activate a Python virtual environment.
2. Install dependencies:

pip install -r requirements.txt

Note: requirements.txt currently lists core data/scikit dependencies. For API serving, install FastAPI and Uvicorn if not already installed:

pip install fastapi uvicorn

## Data Setup

The repository already contains cleaned CSV files in data/clean/ and cache artifacts in data/cache/.

If you need to regenerate cleaned data:

python data_prep.py

Important: data_prep.py currently expects MovieLens files at:

- data/raw/ml-100k/u.item
- data/raw/ml-100k/u.data

If those files are not present in your local copy, update the paths in data_prep.py or place the expected files there.

## Training / Cache Generation

To generate (or regenerate) model cache artifacts:

python main.py

This creates pickles in data/cache/:

- train.pkl
- test.pkl
- item_prior.pkl
- user_prior.pkl
- item_likelihood.pkl
- user_likelihood.pkl

## Run the API

Start the FastAPI server:

uvicorn api:app --reload

Open docs:

- http://127.0.0.1:8000/docs

## API Endpoints

## GET /recommendations

Query params:

- user_id: int
- k: int (default 10)

Example:

GET /recommendations?user_id=196&k=10

Response shape:

- user_id
- recommendations: list of { movie_id, predicted_rating }

## POST /constraints

JSON body fields:

- user_id: int
- k: int (default 10)
- genre: string | null
- language: string | null
- runtime: [operator, value] | null (example: ["<=", 120])
- release_year: [operator, value] | null (example: [">=", 2000])

Example request body:

{
	"user_id": 196,
	"k": 10,
	"genre": "Action",
	"language": "en",
	"runtime": ["<=", 120],
	"release_year": [">=", 2000]
}

## CSP Test Script

Run basic CSP checks:

python csp/test_CSP.py

The script exercises:

- normal constraints
- impossible constraints (to trigger relaxation)
- single-constraint filtering

## Notes and Caveats

- csp/base_CSP.py executes sample code at import time (prints and sample filtering). This is functional but noisy in production logs.
- nbcf/evaluate.py currently defines only a function signature stub and is not yet implemented.
- requirements.txt does not currently include FastAPI/Uvicorn entries.

## Next Improvements

- Add full metric evaluation (MAE/RMSE/top-k ranking metrics) in nbcf/evaluate.py
- Move demo code in csp/base_CSP.py behind a main guard
- Add unit tests for API endpoint behavior and hybrid predictor correctness
- Align data_prep.py raw path assumptions with files tracked in data/raw/
