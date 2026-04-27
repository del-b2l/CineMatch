import pickle

CACHE = 'data/cache'

train = pickle.load(open(f'{CACHE}/train.pkl', 'rb'))
test = pickle.load(open(f'{CACHE}/test.pkl', 'rb'))
item_prior = pickle.load(open(f'{CACHE}/item_prior.pkl', 'rb'))
user_prior = pickle.load(open(f'{CACHE}/user_prior.pkl', 'rb'))
item_likelihood = pickle.load(open(f'{CACHE}/item_likelihood.pkl', 'rb'))
user_likelihood = pickle.load(open(f'{CACHE}/user_likelihood.pkl', 'rb'))

print("Training data for user 196: \n", train[196])
print("Test data for user 196: \n", test[196])
print("Item prior for item 242: \n", item_prior[242])
print("User prior for user 196: \n", user_prior[196])
print("Item likelihood [242][3][302]: \n", item_likelihood[242][3][302])