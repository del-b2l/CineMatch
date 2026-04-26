from collections import defaultdict
import csv
import random

def build_rating_dicts(filepath):
    """
    filepath: path to ratings_clean.csv
    Returns:
        user_ratings: dict[user_id -> dict[item_id -> rating]]
        item_ratings: dict[item_id -> dict[user_id -> rating]]
    """
    user_ratings = defaultdict(dict)
    item_ratings = defaultdict(dict)

    with open(filepath) as f:
        reader = csv.reader(f)
        next(reader, None) # skip header

        for row in reader:
            userId = int(row[0])
            movieId = int(row[1])
            rating = int(row[2])
            user_ratings[userId][movieId] = rating
            item_ratings[movieId][userId] = rating
    return user_ratings, item_ratings

# Per-user split guarantees every user keeps 80% of their history in train.
def train_test_split(user_ratings, test_ratio=0.2):
    """
    Returns:
        train: dict[user_id -> dict[item_id -> rating]]
        test:  dict[user_id -> dict[item_id -> rating]]
    """
    train = defaultdict(dict)
    test = defaultdict(dict)
    for user, _ in user_ratings.items():
        items = list(user_ratings[user].keys())
        k = int(len(items)*test_ratio)
        test_items = random.sample(items, k)  
        test_items = set(test_items)
        for item in test_items:
            test[user][item] = user_ratings[user][item]
        train_items = [item for item in items if item not in test_items]
        for item in train_items:
            train[user][item] = user_ratings[user][item]
    return train, test

def build_train_item_ratings(train):
    train_item_ratings = defaultdict(dict)
    for user, items in train.items():
        for item, rating in items.items():
            train_item_ratings[item][user] = rating

    return train_item_ratings