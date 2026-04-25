import pandas as pd
import ast

movies = pd.read_csv("data/clean/movies_clean.csv")

# genres column is pipe-separated e.g. "Action|Drama"
# convert to a list for easier filtering
movies["genres_list"] = movies["genres"].str.split("|")

print(movies.head())

def build_domains(movies):
    domains = {
        "genre": set(),
        "release_year": set(),
        "runtime": set(),
        "language": set()
    }

    for _, row in movies.iterrows():
        for g in row["genres_list"]:
            if g:
                domains["genre"].add(g)

        # only add non-NaN years
        if not pd.isna(row["release_year"]):
            domains["release_year"].add(int(row["release_year"]))

        domains["runtime"].add(int(row["runtime"]))
        domains["language"].add(row["language"])

    return domains

domains = build_domains(movies)
print()
print("Genres:", list(domains["genre"])[:5])
print("Years range:", min(domains["release_year"]), "-", max(domains["release_year"]))

# this is what the UI will eventually pass in, hardcoded example for now:
user_constraints = {
    "genre": "Action", # must include this genre
    "release_year": (">=", 2000),
    "runtime": ("<=", 120),
    "language": "en"
}

def check_constraint(value, constraint):
    if isinstance(constraint, tuple):
        op, threshold = constraint[0], constraint[1]
        if op == ">=": return value >= threshold
        if op == "<=": return value <= threshold
        if op == ">":  return value > threshold
        if op == "<":  return value < threshold
    else:
        return value == constraint

# AC-3 filtering --> remove every movie that violates at least one constraint

def ac3_filter(movies, user_constraints):
    filtered = movies.copy()
    pruning_log = []   # for visualisation, we'll log every step

    # genre constraint
    if "genre" in user_constraints and len(filtered) > 0:
        before = len(filtered)
        g = user_constraints["genre"]
        filtered = filtered[filtered["genres_list"].apply(lambda lst: g in lst)]
        pruning_log.append(f"genre == '{g}': {before} → {len(filtered)} movies")

    # release_year constraint
    if "release_year" in user_constraints and len(filtered) > 0:
        before = len(filtered)
        filtered = filtered[filtered["release_year"].apply(
            lambda y: check_constraint(y, user_constraints["release_year"]) if pd.notna(y) else False
        )]
        pruning_log.append(f"release_year {user_constraints['release_year']}: {before} → {len(filtered)} movies")

    # runtime constraint
    if "runtime" in user_constraints and len(filtered) > 0:
        before = len(filtered)
        filtered = filtered[filtered["runtime"].apply(
            lambda r: check_constraint(r, user_constraints["runtime"])
        )]
        pruning_log.append(f"runtime {user_constraints['runtime']}: {before} → {len(filtered)} movies")

    # language constraint
    if "language" in user_constraints and len(filtered) > 0:
        before = len(filtered)
        filtered = filtered[filtered["language"] == user_constraints["language"]]
        pruning_log.append(f"language == '{user_constraints['language']}': {before} → {len(filtered)} movies")

    return filtered, pruning_log

# run the AC-3 filter with the user's set constraints and print the pruning log

result, log = ac3_filter(movies, user_constraints)
for step in log:
    print(step)
print(f"\nFinal candidates: {len(result)} movies\n")
print(result[["movieId", "title", "release_year", "runtime"]].head(10))

# only runs when ac3_filter returns 0 movies
# suggests problematic constraint + relaxes it

def backtrack_relax(movies, user_constraints):
    """
    try removing one constraint at a time
    return the first relaxation that gives any results,
    with a human-readable message
    """
    constraint_keys = list(user_constraints.keys())

    for key in constraint_keys:
        # temporarily remove this one constraint
        relaxed = {k: v for k, v in user_constraints.items() if k != key}
        result, _ = ac3_filter(movies, relaxed)

        if len(result) > 0:
            return result, f"\nNo movies match all your filters. \n!!! Try removing the '{key}' constraint - that gives {len(result)} results."

    return pd.DataFrame(), "\nNo movies found even after relaxing individual constraints. Try loosening multiple filters."

def csp_filter(movies, user_constraints):
    """
    main entry point for the CSP layer!!
    returns: (candidate_movie_ids, log_for_visualisation, message)
    """
    result, log = ac3_filter(movies, user_constraints)

    if len(result) == 0:
        print("\nAC-3 found no results. Running backtracking...")
        result, message = backtrack_relax(movies, user_constraints)
    else:
        message = f"Found {len(result)} movies matching your filters."

    candidate_ids = result["movieId"].tolist() if len(result) > 0 else []
    return candidate_ids, log, message

# sample usage:

candidate_ids, log, message = csp_filter(movies, user_constraints)
print(message)
print("Candidate IDs to pass:", candidate_ids[:10])