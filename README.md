🧠 Fuzzy Reasoner Visualization Dashboard

An AI-driven fuzzy logic reasoning and visualization platform inspired by the CEDAR (Conceptual, Extended, Degree-based Approximate Reasoner) framework.
It demonstrates how order-sorted feature logic (OSF) and fuzzy similarity reasoning can be visualized interactively using Flask + D3.js.

🚀 Features

✅ Fuzzy Reasoning Engine — Implements fuzzy subsumption and similarity between concepts
✅ Interactive Graph Visualization — Explore a knowledge base across multiple domains
✅ Zoom / Pan / Tooltips / Animated Focus on nodes
✅ Multi-Domain Knowledge Base — Movies 🎬, Education 🎓, Health 🩺, Animals 🐾
✅ Fuzzy Degrees on edges (0 – 1 similarity)
✅ REST API for programmatic reasoning (/query)
✅ Browser Dashboard UI built with D3.js

🏗️ Architecture
Client (Browser)
 ├── index.html (D3.js Visualization)
 │     └── Fetch /query results from Flask
 └── app.py (Flask)
       └── fuzzy_cedar.py
              ├── KnowledgeBase
              ├── Similarity Matrix
              ├── Fuzzy Reasoning Engine
              └── Example Knowledge Graph

⚙️ Installation & Run Locally
# Clone the repository
git clone https://github.com/ajay20-s/fuzzy-reasoner-dashboard.git
cd fuzzy-reasoner-dashboard

# Create & activate virtual environment
python -m venv venv
venv\Scripts\activate   # (Windows)
# or source venv/bin/activate (Linux/Mac)

# Install dependencies
pip install flask

# Run the app
python app.py


Open your browser at 👉 http://127.0.0.1:5000/

💡 Concept

Traditional logic is binary (true/false).
Fuzzy reasoning allows partial truths — degrees between 0 and 1.

Example reasoning chain:

slasher ⊑ horror = 1.0
horror ∼ thriller = 0.5
⇒ slasher ⊑ thriller = 0.5

So, when querying thriller, your system infers that Psycho and Halloween are partially thrillers.

🧩 Knowledge Base Domains
Domain	Example Concepts	Example Similarities
🎬 Movies	thriller, horror, drama, romcom	horror ∼ thriller = 0.6
🎓 Education	teacher, professor, researcher	teacher ∼ researcher = 0.6
🩺 Health	flu, cold, covid	flu ∼ covid = 0.7
🐾 Animals	dog, cat, eagle, shark	dog ∼ cat = 0.6
🧭 Example API Query
curl -X POST http://127.0.0.1:5000/query \
     -H "Content-Type: application/json" \
     -d "{\"sort\":\"thriller\",\"features\":{}}"


Response:

[
  {"name": "memento", "degree": 1.0, "unifier": "thriller(title -> 'Memento')"},
  {"name": "psycho", "degree": 0.5, "unifier": "slasher(title -> 'Psycho')"},
  {"name": "halloween", "degree": 0.5, "unifier": "thriller(title -> 'Halloween', year -> 1979)"}
]

🧠 Applications

Healthcare: Symptom-based disease similarity reasoning

Recommender Systems: Similar movies, music, or courses

Semantic Search: “Find items similar to this concept”

Expert Systems: Decision support with partial truth

Education Ontologies: Teacher–Researcher–Professor fuzzy relations



🧩 Future Enhancements

 Domain filter (Movies / Health / Education / Animals)

 Import custom ontologies (JSON)

 Deploy to Render / Hugging Face Spaces

 Add persistent graph layout & saving

👨‍💻 Author

Ajay Kumar
GitHub: @ajay20-s

Inspired by the research paper

Similarity-Based Reasoning with Order-Sorted Feature Logic (CEDAR Extension)

📜 License

MIT License © 2025 Ajay Kumar
