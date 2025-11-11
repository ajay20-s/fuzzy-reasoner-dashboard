# app.py
from flask import Flask, request, jsonify, render_template
from fuzzy_cedar import example_setup, run_query, OSFTerm, get_graph_data

app = Flask(__name__, template_folder='templates')
kb, deg_fn, sorts, M, idx = example_setup()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/graph', methods=['GET'])
def graph():
    data = get_graph_data(kb)
    return jsonify(data)

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    sort = data.get('sort')
    feats = data.get('features', {})

    def parse_val(v):
        if v is None:
            return None
        if isinstance(v, dict) and 'sort' in v:
            f = {}
            for k, val in v.get('features', {}).items():
                f[k] = parse_val(val)
            const = v.get('const_value', None)
            return OSFTerm(v['sort'], features=f, const_value=const)
        return v

    features_parsed = {}
    for k, v in feats.items():
        val = parse_val(v)
        if val is not None:
            features_parsed[k] = val

    q = OSFTerm(sort, features=features_parsed)
    results = run_query(kb, q, deg_fn, threshold=0.01)
    out = []
    for name, unif, deg in results:
        out.append({'name': name, 'degree': float(deg), 'unifier': str(unif)})
    return jsonify(out)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
