# fuzzy_cedar.py
# Final version — Supports dynamic threshold & clean graph data

from sentence_transformers import SentenceTransformer
import numpy as np

SORT_DESCRIPTIONS = {
    "movie": "A form of visual storytelling intended for entertainment.",
    "thriller": "A movie genre focusing on tension, uncertainty, and excitement.",
    "slasher": "A horror subgenre featuring killers and violent scenes.",
    "horror": "A film genre intended to frighten or shock the audience.",
    "teacher": "A person whose job is to teach students.",
    "university_teacher": "A teacher who works in a university.",
    "school_teacher": "A teacher who works in a primary or secondary school."
}

# ---------------------------------------------
# BERT Similarity Matrix
# ---------------------------------------------

def build_similarity_matrix(descriptions):
    print("\n🔍 Generating AI-based similarity matrix...")

    model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

    sorts = list(descriptions.keys())
    texts = [descriptions[s] for s in sorts]
    emb = model.encode(texts)

    sim = {}
    for i, a in enumerate(sorts):
        sim[a] = {}
        for j, b in enumerate(sorts):
            sim[a][b] = float(
                np.dot(emb[i], emb[j]) /
                (np.linalg.norm(emb[i]) * np.linalg.norm(emb[j]))
            )

    return sim

# ---------------------------------------------
# OSF TERM
# ---------------------------------------------

class OSFTerm:
    def __init__(self, sort, features=None, const_value=None):
        self.sort = sort
        self.features = features if features else {}
        self.const_value = const_value

    def __str__(self):
        if self.const_value:
            return f"{self.sort}('{self.const_value}')"
        if not self.features:
            return f"{self.sort}()"

        return f"{self.sort}(" + ", ".join(f"{k}->{v}" for k, v in self.features.items()) + ")"

# ---------------------------------------------
# UNIFICATION (CEDAR)
# ---------------------------------------------

def unify(kb, query, instance, similarity, deg_fn):
    if not isinstance(instance, OSFTerm):
        return None, 0

    d = similarity.get(query.sort, {}).get(instance.sort, 0)
    if d == 0:
        return None, 0

    degree = d
    unifier = {}

    for feat, qv in query.features.items():
        if feat not in instance.features:
            return None, 0

        iv = instance.features[feat]

        if isinstance(qv, OSFTerm):
            sub, d2 = unify(kb, qv, iv, similarity, deg_fn)
            if d2 == 0:
                return None, 0

            degree = deg_fn(degree, d2)
            unifier[feat] = sub

        else:
            if iv != qv:
                return None, 0
            unifier[feat] = iv

    return OSFTerm(instance.sort, unifier), degree

# ---------------------------------------------
# QUERY
# ---------------------------------------------

def run_query(kb, query, deg_fn, similarity_threshold):
    results = []

    sim = kb["similarity"]

    for name, inst in kb.items():
        if name == "similarity":
            continue

        unifier, d = unify(kb, query, inst, sim, deg_fn)

        if d >= similarity_threshold:
            results.append((name, unifier, d))

    results.sort(key=lambda x: -x[2])
    return results

# ---------------------------------------------
# GRAPH DATA (Filter based on threshold)
# ---------------------------------------------

def get_graph_data(kb, threshold):
    sim = kb["similarity"]

    nodes = [{"id": s, "group": 1} for s in SORT_DESCRIPTIONS.keys()]
    links = []

    for a in sim:
        for b in sim[a]:
            val = sim[a][b]
            if a != b and val >= threshold:
                links.append({
                    "source": a,
                    "target": b,
                    "value": val
                })

    return {"nodes": nodes, "links": links}

# ---------------------------------------------
# KB
# ---------------------------------------------

def example_setup():
    similarity = build_similarity_matrix(SORT_DESCRIPTIONS)

    kb = {
        "similarity": similarity,

        "memento": OSFTerm("thriller", {"title": "Memento"}),
        "psycho": OSFTerm("slasher", {"title": "Psycho"}),
        "halloween": OSFTerm("thriller", {"title": "Halloween", "year": 1979}),

        "carol": OSFTerm("university_teacher", {"works_at": OSFTerm("university")}),
        "bob": OSFTerm("school_teacher", {"works_at": OSFTerm("school")})
    }

    deg_fn = lambda a, b: min(a, b)
    return kb, deg_fn
