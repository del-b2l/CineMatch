import pandas as pd
import ast
import re

# ── PATHS ──────────────────────────────────────────────────────────────────────
TMDB_PATH        = "data/raw/tmdb_5000_movies.csv"
ML_MOVIES_PATH   = "data/raw/ml-100k/u.item"
ML_RATINGS_PATH  = "data/raw/ml-100k/u.data"
OUT_MOVIES       = "data/clean/movies_clean.csv"
OUT_RATINGS      = "data/clean/ratings_clean.csv"


# ── STEP 1: Load MovieLens 100k Movies ──────────────────────────────────────
print("Loading MovieLens 100k movies...")
genre_cols = ['unknown', 'Action', 'Adventure', 'Animation', "Children's", 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']

ml_movies = pd.read_csv(
    ML_MOVIES_PATH,
    sep="|",
    engine="python",
    names=["movieId", "title", "release_date", "video_release_date", "imdb_url"] + genre_cols,
    encoding="latin-1"
)

# Extract year from title like "Toy Story (1995)" → 1995
ml_movies["release_year"] = ml_movies["title"].str.extract(r"\((\d{4})\)$").astype(float)

# Clean title for consistency: remove the year part and lowercase
ml_movies["title_clean"] = ml_movies["title"].str.replace(r"\s*\(\d{4}\)$", "", regex=True).str.strip()

# Convert genre columns (0/1) to pipe-separated genre names
def genres_to_string(row):
    genres = []
    for genre, val in zip(genre_cols, row[genre_cols]):
        if val == 1:
            genres.append(genre)
    return "|".join(genres) if genres else "unknown"

ml_movies["genres"] = ml_movies.apply(genres_to_string, axis=1)

# Add default values for compatibility
ml_movies["runtime"] = 120  # default runtime in minutes
ml_movies["language"] = "en"  # default language

print(f"  MovieLens 100k movies loaded: {len(ml_movies)}")


# Build the final movies_clean file
movies_clean = ml_movies[[
    "movieId",
    "title",              # title from MovieLens (includes year)
    "genres",             # parsed genres from MovieLens, pipe-separated
    "release_year",       # integer year
    "runtime",            # default runtime
    "language"            # default language
]]

movies_clean = movies_clean.drop_duplicates(subset="movieId")
movies_clean.to_csv(OUT_MOVIES, index=False)
print(f"  movies_clean.csv saved: {len(movies_clean)} movies")


# ── STEP 2: Clean Ratings ──────────────────────────────────────────────────────
print("Loading ratings...")
ratings = pd.read_csv(
    ML_RATINGS_PATH,
    sep="\t",
    engine="python",
    names=["userId", "movieId", "rating", "timestamp"],
    encoding="latin-1"
)

# Keep only ratings for movies that exist in our movies data
valid_movie_ids = set(ml_movies["movieId"])
ratings_clean = ratings[ratings["movieId"].isin(valid_movie_ids)][["userId", "movieId", "rating"]]

ratings_clean.to_csv(OUT_RATINGS, index=False)
print(f"  ratings_clean.csv saved: {len(ratings_clean)} ratings")

print("\nDone! Both clean files are in data/clean/")