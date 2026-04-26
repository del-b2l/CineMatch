def compute_mae(test, train, train_item_ratings,
                item_prior, item_likelihood,
                user_prior, user_likelihood, R):
    """
    Returns MAE across all test ratings using hybrid prediction.
    """