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
            if j not in item_likelihood.get(item, {}).get(y, {}):
                continue
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
            if v not in user_likelihood.get(user, {}).get(y, {}):
                continue
            score += math.log(user_likelihood[user][y][v][r_vj])
        scores[y] = score

    return (max(scores, key=scores.get), scores)

def predict_hybrid(user, item, train, train_item_ratings,
                   item_prior, item_likelihood,
                   user_prior, user_likelihood, R,
                   max_p=3, max_q=3):
    """
    Hybrid Naive-Bayes predictor.

    Returns
    -------
    best_label : int
    scores     : dict[rating -> combined log-score]
    p_evidence : list[(item_id, rating)]  – items the *user* rated that
                 contribute to the user-based (item-centric) arm.
    q_evidence : list[(user_id, rating)]  – co-raters of *item* that
                 contribute to the item-based (user-centric) arm.
    p_weight   : float  – weight given to the item-based (P) arm
    q_weight   : float  – weight given to the user-based (Q) arm
    """
    # |U_i| = number of users who rated the candidate item
    u_i = len(train_item_ratings.get(item, {}))
    # |I_u| = number of items the requesting user has rated
    i_u = len(train.get(user, {}))

    alpha_q = 1.0 / (1.0 + u_i)   # weight for user-based (Q) arm
    alpha_p = 1.0 / (1.0 + i_u)   # weight for item-based (P) arm

    _, scores_item_based = predict_item_based(
        user, item, train_item_ratings, user_prior, user_likelihood, R)
    _, scores_user_based = predict_user_based(
        user, item, train, item_prior, item_likelihood, R)

    scores = {}
    for y in R:
        scores[y] = alpha_p * scores_item_based[y] + alpha_q * scores_user_based[y]

    best_y = max(scores, key=scores.get)

    # --- P evidences: items the user rated that have a known likelihood
    #     entry in the user-based arm (item_likelihood[item][best_y][j])
    p_evidence = [
        (j, r_uj)
        for j, r_uj in train.get(user, {}).items()
        if j in item_likelihood.get(item, {}).get(best_y, {})
    ][:max_p]

    # --- Q evidences: co-raters of the candidate item that have a known
    #     likelihood entry in the item-based arm (user_likelihood[user][best_y][v])
    q_evidence = [
        (v, r_vj)
        for v, r_vj in train_item_ratings.get(item, {}).items()
        if v in user_likelihood.get(user, {}).get(best_y, {})
    ][:max_q]

    return best_y, scores, p_evidence, q_evidence, alpha_p, alpha_q


