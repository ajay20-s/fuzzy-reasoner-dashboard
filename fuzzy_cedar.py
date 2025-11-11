# fuzzy_cedar.py
from collections import defaultdict, deque
import json
import copy

# -------------------------
# 1. Knowledge Base Model
# -------------------------
class KnowledgeBase:
    def __init__(self):
        self.sorts = set()
        # crisp subsumption edges: (a,b) -> 1 means a <= b (a is subsumed by b)
        self.subsumption = defaultdict(float)
        # similarity (symmetric) : (a,b) -> degree in (0,1]
        self.similarity = defaultdict(float)
        # instances: name -> OSFTerm (root sort + features)
        self.instances = {}  # e.g., {'psycho': OSFTerm(...)}
        # features domain typing: feature -> domain sort (optional)
        self.features = {}

    def add_sort(self, s):
        self.sorts.add(s)

    def add_subsumption(self, a, b):
        self.add_sort(a); self.add_sort(b)
        self.subsumption[(a,b)] = max(self.subsumption[(a,b)], 1.0)

    def add_similarity(self, a, b, deg):
        self.add_sort(a); self.add_sort(b)
        self.similarity[(a,b)] = max(self.similarity[(a,b)], deg)
        self.similarity[(b,a)] = max(self.similarity[(b,a)], deg)

    def add_feature(self, feature, domain_sort=None):
        self.features[feature] = domain_sort

    def add_instance(self, name, term):
        self.instances[name] = term

# -------------------------
# 2. OSF Term representation
# -------------------------
class OSFTerm:
    def __init__(self, sort, features=None, const_value=None):
        self.sort = sort
        self.features = features or {}
        self.const_value = const_value

    def is_constant(self):
        return self.const_value is not None

    def copy(self):
        return copy.deepcopy(self)

    def __repr__(self):
        if self.is_constant():
            return f'{self.const_value} : {self.sort}'
        feat_repr = ', '.join(f'{k} -> {v!r}' for k,v in self.features.items())
        return f'{self.sort}({feat_repr})'

# -------------------------
# 3. Build fuzzy subsumption matrix (max-min transitive closure)
# -------------------------
def build_fuzzy_subsumption(kb: KnowledgeBase):
    sorts = sorted(kb.sorts)
    idx = {s:i for i,s in enumerate(sorts)}
    n = len(sorts)
    M = [[0.0]*n for _ in range(n)]
    for i in range(n):
        M[i][i] = 1.0
    for (a,b),v in kb.subsumption.items():
        M[idx[a]][idx[b]] = max(M[idx[a]][idx[b]], 1.0)
    for (a,b),deg in kb.similarity.items():
        M[idx[a]][idx[b]] = max(M[idx[a]][idx[b]], deg)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                via = min(M[i][k], M[k][j])
                if via > M[i][j]:
                    M[i][j] = via
    def degree(a,b):
        if a not in idx or b not in idx:
            return 0.0
        return M[idx[a]][idx[b]]
    return degree, sorts, M, idx

# -------------------------
# 4. Fuzzy Unification (simplified)
# -------------------------
def unify_terms(t1: OSFTerm, t2: OSFTerm, degree_fn):
    root_deg = max(degree_fn(t1.sort, t2.sort), degree_fn(t2.sort, t1.sort))
    if root_deg == 0:
        return None, 0.0
    d12 = degree_fn(t1.sort, t2.sort)
    d21 = degree_fn(t2.sort, t1.sort)
    chosen_sort = t1.sort if d12 >= d21 else t2.sort
    unified = OSFTerm(chosen_sort, {})
    degrees = [root_deg]
    all_feats = set(t1.features.keys()) | set(t2.features.keys())
    for f in all_feats:
        v1 = t1.features.get(f, None)
        v2 = t2.features.get(f, None)
        if v1 is None:
            unified.features[f] = copy.deepcopy(v2)
            continue
        if v2 is None:
            unified.features[f] = copy.deepcopy(v1)
            continue
        if not isinstance(v1, OSFTerm) and not isinstance(v2, OSFTerm):
            if v1 == v2:
                unified.features[f] = v1
                degrees.append(1.0)
            else:
                return None, 0.0
        elif isinstance(v1, OSFTerm) and isinstance(v2, OSFTerm):
            unif_sub, deg_sub = unify_terms(v1, v2, degree_fn)
            if unif_sub is None or deg_sub == 0:
                return None, 0.0
            unified.features[f] = unif_sub
            degrees.append(deg_sub)
        else:
            if isinstance(v1, OSFTerm) and v2 is not None and not isinstance(v2, OSFTerm):
                if v1.is_constant() and v1.const_value == v2:
                    unified.features[f] = v2
                    degrees.append(1.0)
                else:
                    return None, 0.0
            elif isinstance(v2, OSFTerm) and v1 is not None and not isinstance(v1, OSFTerm):
                if v2.is_constant() and v2.const_value == v1:
                    unified.features[f] = v1
                    degrees.append(1.0)
                else:
                    return None, 0.0
            else:
                return None, 0.0
    final_degree = min(degrees) if degrees else root_deg
    return unified, final_degree

# -------------------------
# 5. Query: match a query term (can have variable placeholders) against instances
# -------------------------
def run_query(kb: KnowledgeBase, query_term: OSFTerm, degree_fn, threshold=0.01):
    results = []
    for name, inst in kb.instances.items():
        unif, deg = unify_terms(query_term, inst, degree_fn)
        if deg >= threshold:
            results.append((name, unif, deg))
    results.sort(key=lambda x: -x[2])
    return results

# -------------------------
# 6. Example setup & test data
# -------------------------
def example_setup():
    kb = KnowledgeBase()

    # -------- DOMAIN 1: MOVIES --------
    movie_sorts = ['media', 'movie', 'thriller', 'horror', 'slasher', 'comedy', 'romcom', 'drama', 'action', 'documentary']
    for s in movie_sorts:
        kb.add_sort(s)
    kb.add_subsumption('movie', 'media')
    kb.add_subsumption('horror', 'movie')
    kb.add_subsumption('slasher', 'horror')
    kb.add_subsumption('thriller', 'movie')
    kb.add_subsumption('comedy', 'movie')
    kb.add_subsumption('romcom', 'comedy')
    kb.add_subsumption('drama', 'movie')
    kb.add_subsumption('action', 'movie')
    kb.add_subsumption('documentary', 'movie')

    # Similarities between movie genres
    kb.add_similarity('horror', 'thriller', 0.6)
    kb.add_similarity('thriller', 'action', 0.5)
    kb.add_similarity('romcom', 'drama', 0.4)
    kb.add_similarity('documentary', 'drama', 0.5)
    kb.add_similarity('horror', 'action', 0.3)

    # Instances
    kb.add_instance('memento', OSFTerm('thriller', features={'title': 'Memento'}))
    kb.add_instance('psycho', OSFTerm('slasher', features={'title': 'Psycho'}))
    kb.add_instance('halloween', OSFTerm('horror', features={'title': 'Halloween'}))
    kb.add_instance('titanic', OSFTerm('drama', features={'title': 'Titanic'}))
    kb.add_instance('rush_hour', OSFTerm('action', features={'title': 'Rush Hour'}))
    kb.add_instance('friends', OSFTerm('romcom', features={'title': 'Friends'}))
    kb.add_instance('earth', OSFTerm('documentary', features={'title': 'Planet Earth'}))

    # -------- DOMAIN 2: EDUCATION --------
    edu_sorts = ['person', 'student', 'teacher', 'researcher', 'professor', 'lecturer', 'university', 'college', 'school']
    for s in edu_sorts:
        kb.add_sort(s)
    kb.add_subsumption('student', 'person')
    kb.add_subsumption('teacher', 'person')
    kb.add_subsumption('researcher', 'person')
    kb.add_subsumption('professor', 'teacher')
    kb.add_subsumption('lecturer', 'teacher')
    kb.add_subsumption('university', 'school')
    kb.add_subsumption('college', 'school')

    kb.add_similarity('teacher', 'researcher', 0.6)
    kb.add_similarity('professor', 'researcher', 0.8)
    kb.add_similarity('student', 'researcher', 0.4)
    kb.add_similarity('college', 'university', 0.7)

    kb.add_instance('alice', OSFTerm('professor', features={'works_at': OSFTerm('university')}))
    kb.add_instance('bob', OSFTerm('researcher', features={'works_at': OSFTerm('college')}))
    kb.add_instance('carol', OSFTerm('teacher', features={'works_at': OSFTerm('school')}))
    kb.add_instance('david', OSFTerm('student', features={'studies_at': OSFTerm('university')}))

    # -------- DOMAIN 3: HEALTH --------
    health_sorts = ['organism', 'disease', 'virus', 'bacteria', 'infection', 'symptom', 'fever', 'cold', 'flu', 'covid']
    for s in health_sorts:
        kb.add_sort(s)
    kb.add_subsumption('virus', 'organism')
    kb.add_subsumption('bacteria', 'organism')
    kb.add_subsumption('infection', 'disease')
    kb.add_subsumption('flu', 'infection')
    kb.add_subsumption('cold', 'infection')
    kb.add_subsumption('covid', 'infection')
    kb.add_subsumption('fever', 'symptom')

    kb.add_similarity('flu', 'covid', 0.7)
    kb.add_similarity('cold', 'flu', 0.5)
    kb.add_similarity('bacteria', 'virus', 0.4)

    kb.add_instance('covid19', OSFTerm('covid', features={'symptom': OSFTerm('fever')}))
    kb.add_instance('influenza', OSFTerm('flu', features={'symptom': OSFTerm('cold')}))
    kb.add_instance('strep', OSFTerm('bacteria', features={'symptom': OSFTerm('fever')}))

    # -------- DOMAIN 4: ANIMALS --------
    animal_sorts = ['animal', 'mammal', 'reptile', 'bird', 'fish', 'dog', 'cat', 'snake', 'eagle', 'shark']
    for s in animal_sorts:
        kb.add_sort(s)
    kb.add_subsumption('mammal', 'animal')
    kb.add_subsumption('reptile', 'animal')
    kb.add_subsumption('bird', 'animal')
    kb.add_subsumption('fish', 'animal')
    kb.add_subsumption('dog', 'mammal')
    kb.add_subsumption('cat', 'mammal')
    kb.add_subsumption('snake', 'reptile')
    kb.add_subsumption('eagle', 'bird')
    kb.add_subsumption('shark', 'fish')

    kb.add_similarity('dog', 'cat', 0.6)
    kb.add_similarity('eagle', 'shark', 0.3)
    kb.add_similarity('reptile', 'fish', 0.4)

    kb.add_instance('bella', OSFTerm('dog', features={'age': 3}))
    kb.add_instance('whiskers', OSFTerm('cat', features={'age': 4}))
    kb.add_instance('cobra', OSFTerm('snake', features={'length': 2}))
    kb.add_instance('falcon', OSFTerm('eagle', features={'age': 5}))
    kb.add_instance('nemo', OSFTerm('fish', features={'species': 'clownfish'}))

    # -------- CROSS-DOMAIN FUZZY SIMILARITIES --------
    kb.add_similarity('researcher', 'movie', 0.2)   # creative domains
    kb.add_similarity('teacher', 'doctor', 0.3)
    kb.add_similarity('virus', 'animal', 0.1)
    kb.add_similarity('thriller', 'fever', 0.1)  # funny link to show cross concept mapping

    # Build fuzzy closure
    degree_fn, sorts, M, idx = build_fuzzy_subsumption(kb)
    return kb, degree_fn, sorts, M, idx


# -------------------------
# 7. Graph export helper
# -------------------------
def get_graph_data(kb: KnowledgeBase):
    """
    Return dict with nodes and edges consumable by D3.
    Node: { id: 'movie' }
    Edge: { source: 'horror', target: 'thriller', type: 'similarity'/'subsumption', weight: 0.5 }
    """
    nodes = [{'id': s} for s in sorted(kb.sorts)]
    edges = []
    # crisp subsumption edges (weight 1)
    for (a,b),v in kb.subsumption.items():
        edges.append({'source': a, 'target': b, 'type': 'subsumption', 'weight': float(v)})
    # similarity edges (may be duplicated symmetric, keep only once)
    seen = set()
    for (a,b),deg in kb.similarity.items():
        if (b,a) in seen or (a,b) in seen:
            continue
        seen.add((a,b))
        seen.add((b,a))
        edges.append({'source': a, 'target': b, 'type': 'similarity', 'weight': float(deg)})
    return {'nodes': nodes, 'edges': edges}

# If run as script for quick test
if __name__ == '__main__':
    kb, degree_fn, sorts, M, idx = example_setup()
    g = get_graph_data(kb)
    print(json.dumps(g, indent=2))
