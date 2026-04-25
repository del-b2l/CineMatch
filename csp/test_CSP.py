import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import csp.base_CSP as base_CSP

# test 1: normal case
user_constraints = {"genre": "Action", "release_year": (">=", 2010), "runtime": ("<=", 120), "language": "en"}
ids, log, msg = base_CSP.csp_filter(base_CSP.movies, user_constraints)
print("Test 1:", msg)

# test 2: impossible constraints (should trigger backtracking)
user_constraints = {"genre": "Documentary", "release_year": (">=", 2020), "runtime": ("<=", 30), "language": "en"}
ids, log, msg = base_CSP.csp_filter(base_CSP.movies, user_constraints)
print("Test 2:", msg)

# test 3: single constraint
user_constraints = {"language": "fr"}
ids, log, msg = base_CSP.csp_filter(base_CSP.movies, user_constraints)
print("Test 3:", msg)