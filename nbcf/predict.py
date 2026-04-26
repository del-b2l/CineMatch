import math

# P(ru,i=y)∝P(ri=y) ∏ j∈Iu P(rj=ru,j|ri=y)
def predict_user_based(user, item, train, item_prior, item_likelihood, R):
    """
    Returns predicted rating for (user, item) pair.
    """
    scores = {}
    for y in R:
        score = math.log(item_prior[item][y])
        for j, r_uj in train[user].items():
            score += math.log(item_likelihood[item][y][j][r_uj])
        scores[y] = score

    return (max(scores, key=scores.get), scores)

# P(ru,i=y)∝P(ru=y) ∏ v∈Ui P(rv=rv,j|ru=y)
def predict_item_based(user, item, train_item_ratings, user_prior, user_likelihood, R):
    """
    Returns predicted rating for (user, item) pair.
    """
    scores = {}
    for y in R:
        score = math.log(user_prior[user][y])
        for v, r_vj in train_item_ratings[item].items():
            score += math.log(user_likelihood[user][y][v][r_vj])
        scores[y] = score

    return (max(scores, key=scores.get), scores)

def predict_hybrid(user, item, train, train_item_ratings, 
                   item_prior, item_likelihood,
                   user_prior, user_likelihood, R):
    # score(y) = (1/(1+|Ui|)) * log_score_item_based(y) + (1/(1+|Iu|)) * log_score_user_based(y)
    u_i = len(train_item_ratings[item])
    i_u = len(train[user])  

    scores=  {}
    _ , scores_item_based = predict_item_based(user, item, train_item_ratings, user_prior, user_likelihood, R)
    _ , scores_user_based = predict_user_based(user, item, train, item_prior, item_likelihood, R)
    for y in R:
        scores[y] = (1/(1+u_i)) * scores_item_based[y] + (1/(1+i_u)) * scores_user_based[y]

    return max(scores, key=scores.get)


