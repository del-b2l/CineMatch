from collections import defaultdict

# P(rj​=k ∣ ri​=y) = #{u∈U ∣ ru,j​=k ∧ ru,i​=y}+α​ / #{u∈U ∣ ru,j​ !=∙ ^ ru,i​=y}+#R⋅α
def compute_item_likelihood(train, train_item_ratings, R, alpha=0.01):
    likelihood = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))

    # counts[i][y][j][k] = # users who rated i as y AND j as k
    counts = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

    for user, items in train.items():
        for item_i, rating_i in items.items():
            for item_j, rating_j in items.items():
                if item_i != item_j:
                    counts[item_i][rating_i][item_j][rating_j] += 1

    for item_i, y_dict in counts.items():
        for y, j_dict in y_dict.items():
            for item_j, k_dict in j_dict.items():
                denom = sum(k_dict.values()) + len(R)*alpha
                for k in R:
                    numer = k_dict.get(k, 0)+alpha
                    likelihood[item_i][y][item_j][k] = numer / denom
    return likelihood

# P(rv=k|ru=y)= #{i∈I |rv,i=k∧ru,i=y}+α / #{i∈I |rv,i≠•∧ru,i=y}+#R⋅α
def compute_user_likelihood(train, train_item_ratings, R, alpha=0.01):
    likelihood = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))

    # counts[u][y][v][k] = # user u who rated items as y AND user v who rated items as k
    counts = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

    for item, users in train_item_ratings.items():
        for user_u, rating_u in users.items():
            for user_v, rating_v in users.items():
                if user_v != user_u:
                    counts[user_u][rating_u][user_v][rating_v] += 1

    for user_u, y_dict in counts.items():
        for y, v_dict in y_dict.items():
            for user_v, k_dict in v_dict.items():
                denom = sum(k_dict.values()) + len(R)*alpha
                for k in R:
                    numer = k_dict.get(k, 0)+alpha
                    likelihood[user_u][y][user_v][k] = numer / denom
    return likelihood
