from collections import defaultdict

# P(ri​=y)= #{u∈U∣ru,i​=y}+α​ / #{u∈U∣ru,i​ != .}+#R⋅α
def compute_item_priors(train_item_ratings, R, alpha=0.01):
    """
    train_item_ratings: item_ratings dict (only training data)
    train_item_ratings: dict[item_id -> dict[user_id -> rating]]
    R: list of possible rating values e.g. [1,2,3,4,5]
    alpha: smoothing parameter
    
    Returns:
        item_prior: dict[item_id -> dict[rating_value -> probability]]
    """
    item_prior = defaultdict(dict)
    for item, users in train_item_ratings.items():
        for y in R:
            cnt = 0
            for user, rating in users.items():
                if rating == y:
                    cnt+=1
            item_prior[item][y] = (cnt+alpha) / (len(users.keys())+len(R)*alpha)
    return item_prior

# P(ru=y)= # {i∈I | ru,i=y}+α / #{i∈I | ru,i≠•}+#R⋅α 
def compute_user_priors(train, R, alpha=0.01):
    """
    train: dict[user_id -> dict[item_id -> rating]]
    R: list of possible rating values e.g. [1,2,3,4,5]
    alpha: smoothing parameter

    returns:
        user_prior: dict[user_id -> dict[rating_value -> probability]]
    """
    user_prior = defaultdict(dict)
    for user, items in train.items():
        for y in R:
            cnt = 0
            for item, rating in items.items():
                if rating == y:
                    cnt+=1
            user_prior[user][y] = (cnt+alpha) / (len(items.keys()) + len(R)*alpha)
    return user_prior
