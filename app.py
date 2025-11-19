from flask import Flask, request, jsonify, render_template
from fuzzy_cedar import example_setup, OSFTerm, run_query, get_graph_data

app = Flask(__name__, template_folder="templates")

kb, deg_fn = example_setup()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/graph")
def graph():
    threshold = float(request.args.get("t", 0.0))
    return jsonify(get_graph_data(kb, threshold))

@app.route("/query", methods=["POST"])
def query():
    data = request.json
    sort = data["sort"]
    threshold = data.get("threshold", 0.0)

    q = OSFTerm(sort)
    results = run_query(kb, q, deg_fn, threshold)

    return jsonify([
        {"name": name, "degree": float(d), "unifier": str(u)}
        for name, u, d in results
    ])

if __name__ == "__main__":
    app.run(debug=True, port=5000)
