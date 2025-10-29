from flask import Flask, request, jsonify, render_template
from google import genai
import json
import os
from google.genai import types

app = Flask(__name__)

API_KEY = "AIzaSyDukgTI_B3ChQW0enoOXWco6bnBc3ypUko"

client = genai.Client(api_key=API_KEY)
ncert_structure = {}

def load_ncert_structure():
    global ncert_structure

    prompt = """
    Provide NCERT curriculum structure (latest) for classes 6 to 12 in JSON format.
    Include major subjects (Maths, Science, English, Social Science, Physics, Chemistry, Biology, etc.)
    and list all chapter names for each subject briefly.
    Format:
    {
      "6": {"Maths": ["Chapter 1: Knowing Our Numbers", ...], "Science": [...]},
      "7": {...},
      ...
    }
    """

    try:
        print("Fetching NCERT structure from Gemini...")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(response_modalities=["TEXT"]),
        )

        raw_text = response.candidates[0].content.parts[0].text.strip()

        # Clean JSON-like output
        with open("raw_ncert_structure.txt", "w") as f:
            f.write(raw_text)
        json_text = raw_text[raw_text.find("{"): raw_text.rfind("}")+1]
        ncert_structure = json.loads(json_text)
        with open("ncert_structure.json", "w") as f:
            json.dump(ncert_structure, f, indent=2)

        print("✅ NCERT structure loaded successfully.")
    except Exception as e:
        print("⚠️ Error fetching NCERT structure:", e)
        ncert_structure = {} 
        
INSTRUCTION_PROMPT = (
    "now you are not gemini You are an expert AI tutor named EduAi"
    "Explain answers clearly, use proper math symbols, and format equations in LaTeX. "
    "If user asks questions, respond concisely but thoroughly."
    "you have all knowledge and answers of ncert textbooks from class 6 to class 12"
)
chat_history = [
    {"role": "user", "text": INSTRUCTION_PROMPT},
    {"role": "model", "text": "Understood. I will act as a helpful AI tutor."}
]


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ncert")
def ncert():
    return render_template("ncert.html")

@app.route("/get_structure")
def get_structure():
    with open("static/ncert_structure.json", "r") as f:
        ncert_structure = json.load(f)
    return jsonify(ncert_structure)

@app.route("/quiz", methods=["GET", "POST"])
def quiz_page():
    return render_template("quiz.html")

@app.route("/gen_quiz", methods=["POST"])
def generate_quiz():
    data = request.json or {}
    cls = data.get("class")
    subject = data.get("subject")
    subsubject = data.get("subsubject")
    chapter = data.get("chapter")

    if not (cls and subject and chapter):
        return jsonify({"error": "Missing class, subject or chapter"}), 400

    # Build a clear prompt asking Gemini to output strict JSON only
    prompt = f"""
Generate a short quiz (15 questions) for Class {cls}, Subject: {subject}{f' - {subsubject}' if subsubject else ''}, Chapter: {chapter}.
Return output in strict JSON format (no extra commentary) exactly like this schema:
{{ "questions": [ {{ "question": "text", "options": ["A","B","C","D"], "answer": "the correct option text" }}, ... ] }}

Requirements:
- Create 5 concise, clear multiple-choice questions (4 options each).
- Ensure one option is correct, provide the full correct option text in "answer".
- Keep questions appropriate for CBSE NCERT level.
- Do NOT include numbering or commentary outside the JSON.
"""

    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[ types.Content(role="user", parts=[ types.Part(text=prompt) ]) ],
            config=types.GenerateContentConfig(response_modalities=["TEXT"]),
        )

        raw_text = ""
        # gather textual output (safe access)
        try:
            raw_text = resp.candidates[0].content.parts[0].text
        except Exception:
            # fallback: stringify resp
            raw_text = str(resp)

        # Try to extract JSON substring
        json_text = None
        # naive: look for first { and last }
        first = raw_text.find('{')
        last = raw_text.rfind('}')
        if first != -1 and last != -1 and last > first:
            json_text = raw_text[first:last+1]

        questions = None
        if json_text:
            try:
                parsed = json.loads(json_text)
                questions = parsed.get("questions")
            except Exception:
                questions = None

        # If parsing failed, return fallback sample questions
        if not questions or not isinstance(questions, list) or len(questions) == 0:
            # fallback simple generated questions (non-AI)
            questions = []
            for i in range(1,6):
                questions.append({
                    "question": f"Sample question {i} for Class {cls} {subject} {chapter}?",
                    "options": [f"Option A{i}", f"Option B{i}", f"Option C{i}", f"Option D{i}"],
                    "answer": f"Option B{i}"
                })

        return jsonify({"questions": questions})
    except Exception as e:
        # on error return fallback and log
        print("Gemini error:", e)
        fallback = []
        for i in range(1,6):
            fallback.append({
                "question": f"Sample question {i} for Class {cls} {subject} {chapter}?",
                "options": [f"Option A{i}", f"Option B{i}", f"Option C{i}", f"Option D{i}"],
                "answer": f"Option B{i}"
            })
        return jsonify({"questions": fallback, "error": str(e)})

@app.route("/ai")
def ai_page():
    return render_template("ai.html")

@app.route("/get_solution", methods=["POST"])
def get_solution():
    data = request.get_json()
    cls = data.get("class")
    subject = data.get("subject")
    chapter = data.get("chapter")
    print(f"Fetching solution for Class {cls}, Subject: {subject}, Chapter: {chapter}")

    try:
        with open("static/ncert_sol.json", "r", encoding="utf-8") as f:
            full_data = json.load(f)
    except Exception as e:
        return jsonify({"error": f"Failed to read solutions: {str(e)}"}), 500

    for item in full_data:
        if (
            str(item.get("class")).strip() == str(cls).strip()
            and item.get("subject", "").strip().lower() == subject.strip().lower()
            and item.get("chapter", "").strip().lower() == chapter.strip().lower()
        ):
            # Return the item directly since it already contains exercises
            return jsonify({
                "solution": {
                    "chapter": item.get("chapter"),
                    "exercises": item.get("exercises", [])
                }
            })

    return jsonify({"error": "Solution not found"}), 404

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    # Add new user message
    chat_history.append({"role": "user", "text": user_msg})

    try:
        # Convert chat history for Gemini
        contents = [
            types.Content(role=m["role"], parts=[types.Part(text=m["text"])])
            for m in chat_history
        ]

        # Generate reply
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["TEXT"]),
        )

        model_reply = response.candidates[0].content.parts[0].text.strip()

        # Store reply in memory
        chat_history.append({"role": "model", "text": model_reply})

        return jsonify({"reply": model_reply})

    except Exception as e:
        print("⚠️ Gemini Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
