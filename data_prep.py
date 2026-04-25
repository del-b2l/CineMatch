import pandas as pd
import ast
import re

# ── PATHS ──────────────────────────────────────────────────────────────────────
TMDB_PATH        = "data/raw/tmdb_5000_movies.csv"
ML_MOVIES_PATH   = "data/raw/movies.dat"
ML_RATINGS_PATH  = "data/raw/ratings.dat"
OUT_MOVIES       = "data/clean/movies_clean.csv"
OUT_RATINGS      = "data/clean/ratings_clean.csv"


# ── STEP 1: Load TMDB ──────────────────────────────────────────────────────────
print("Loading TMDB...")
tmdb = pd.read_csv(TMDB_PATH)

# Keep only the columns we need
tmdb = tmdb[["title", "release_date", "runtime", "original_language", "genres"]]

# Extract year from release_date (e.g. "2008-07-18" → 2008)
tmdb["release_year"] = pd.to_datetime(tmdb["release_date"], errors="coerce").dt.year

# Parse genres — this is the key step
# genres column looks like: '[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}]'
# We want: "Action|Adventure"
def parse_genres(raw):
    try:
        genre_list = ast.literal_eval(raw)          # safely parse the string as a Python list
        return "|".join([g["name"] for g in genre_list])
    except:
        return ""

tmdb["genres_clean"] = tmdb["genres"].apply(parse_genres)

# Clean up title (strip whitespace)
tmdb["title_clean"] = tmdb["title"].str.strip().str.lower()

# Drop rows missing critical CSP fields
tmdb = tmdb.dropna(subset=["runtime", "release_year", "original_language"])
tmdb = tmdb[tmdb["runtime"] > 0]

print(f"  TMDB rows after cleaning: {len(tmdb)}")


# ── STEP 2: Load MovieLens ─────────────────────────────────────────────────────
print("Loading MovieLens movies...")
ml_movies = pd.read_csv(
    ML_MOVIES_PATH,
    sep="::",
    engine="python",
    names=["movieId", "title", "genres_ml"],
    encoding="latin-1"
)

# Extract year from title like "Toy Story (1995)" → 1995
ml_movies["year"] = ml_movies["title"].str.extract(r"\((\d{4})\)$").astype(float)

# Clean title for joining: remove the year part and lowercase
ml_movies["title_clean"] = ml_movies["title"].str.replace(r"\s*\(\d{4}\)$", "", regex=True).str.strip().str.lower()

print(f"  MovieLens movies loaded: {len(ml_movies)}")


# ── STEP 3: Join TMDB + MovieLens on title ─────────────────────────────────────
print("Joining on title...")
merged = ml_movies.merge(tmdb, on="title_clean", how="inner")

# Build the final movies_clean file
movies_clean = merged[[
    "movieId",
    "title_x",            # title from MovieLens (includes year)
    "genres_clean",       # parsed genres from TMDB, pipe-separated
    "release_year",       # integer year
    "runtime",            # integer minutes
    "original_language"   # ISO code string e.g. "en"
]].rename(columns={"title_x": "title", "genres_clean": "genres", "original_language": "language"})

movies_clean = movies_clean.drop_duplicates(subset="movieId")
movies_clean.to_csv(OUT_MOVIES, index=False)
print(f"  movies_clean.csv saved: {len(movies_clean)} movies")


# ── STEP 4: Clean Ratings ──────────────────────────────────────────────────────
print("Loading ratings...")
ratings = pd.read_csv(
    ML_RATINGS_PATH,
    sep="::",
    engine="python",
    names=["userId", "movieId", "rating", "timestamp"],
    encoding="latin-1"
)

# Keep only ratings for movies that survived the join
valid_movie_ids = set(movies_clean["movieId"])
ratings_clean = ratings[ratings["movieId"].isin(valid_movie_ids)][["userId", "movieId", "rating"]]

ratings_clean.to_csv(OUT_RATINGS, index=False)
print(f"  ratings_clean.csv saved: {len(ratings_clean)} ratings")

print("\nDone! Both clean files are in data/clean/")