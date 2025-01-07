from flask import Flask, render_template, request, jsonify, url_for
from g4f.client import Client
from googletrans import Translator, LANGUAGES
import os
import Levenshtein

import fitz
import pytesseract
from g4f.client import Client
import pyttsx3
import time
# from syllabipy.sonoripy import SonoriPy
import speech_recognition as sr
import g4f.client  
from g4f.client import Client
import sys

from sympy import SympifyError, sympify

app = Flask(__name__)

client = Client()
translator = Translator()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

engine = pyttsx3.init()
engine.setProperty('rate', 150)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Default voice

def split_question_and_answer(text):
    """
    Split the given text into a question and an answer.
    """
    text = text.strip()
    parts = text.split("Answer:")
    question = parts[0].replace("Question:", "").strip()
    answer = parts[1].strip()
    return question, answer

def speak(text):
    """
    Convert text to speech.
    """
    engine.say(text)
    engine.runAndWait()

def get_answer_from_input(answer):
    """
    Capture the answer from the user's input.
    """
    return answer.strip().lower()

def fetch_quiz_question(topic):
    """
    Fetch a quiz question for a given topic.
    """
    prompt = (
        f"Generate a simple one quiz question related to the topic '{topic}'. "
        "Provide the response in the format: 'Question: [question text]. Answer: [answer]'."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.choices[0].message.content.strip()

        if "Question:" not in content or "Answer:" not in content:
            raise ValueError("The response format is incorrect. Ensure it contains both 'Question:' and 'Answer:'.")

        question, answer = split_question_and_answer(content)

        return question, answer

    except Exception as e:
        print(f"Error fetching quiz question: {e}")
        return None, None



engine = pyttsx3.init()

engine.setProperty('rate', 150)

voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  



# Function to syllabify and pronounce words
from syllabipy.sonoripy import SonoriPy  # Ensure you have the right SonoriPy import

def syllabify_and_pronounce(text):
    syllabified_words = []
    words = text.split()
    
    for word in words:
        clean_word = word.strip(".,:;!?")  # Remove punctuation
        syllable_parts = []

        # Skip syllabification for short words (2-4 letters)
        if len(clean_word) <= 2:
            syllable_parts.append(clean_word)  # Don't split short words
        else:
            # Syllabify using SonoriPy
            syllabified = SonoriPy(clean_word)
            syllable_parts.extend(syllabified)  # Add syllables to the list

        syllabified_words.append(" ".join(syllable_parts))  # Join syllables with space

    return syllabified_words



def summarize_content(content):
    """
    Generate a simplified summary of the content using GPT.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Summarize the following content simply: {content}"}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"


def split_question_and_answer(text):
    """
    Split the given text into a question and an answer.
    """
    text = text.strip()
    parts = text.split("Answer:")
    question = parts[0].replace("Question:", "").strip()
    answer = parts[1].strip()
    return question, answer

@app.route("/")
def home():
    """
    Render the home page.
    """
    return render_template("home.html")


@app.route("/summary_chatbot", methods=["GET", "POST"])
def summary_chatbot():
    """
    Summary Chatbot Page - Accepts text and returns summarized content.
    """
    if request.method == "POST":
        user_text = request.json.get("text", "")
        summary = summarize_content(user_text)
        return jsonify({"summary": summary})
    return render_template("summary_chatbot.html")


@app.route('/send_message', methods=['POST'])
def send_message():
    """
    Processes user messages and returns summarized or transformed content.
    """
    message = request.json.get('message', "No input provided.")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Reduce the code size and simplify it: {message}"}
            ],
        )
        reduced_code = response.choices[0].message.content.strip()
        return jsonify({'rows': reduced_code})
    except Exception as e:
        return jsonify({'error': str(e)})
    

@app.route("/code_chatbot")
def code_chatbot():

    return render_template("code_chatbot.html")


@app.route("/Whiteboard")
def Whiteboard():

    return render_template("Whiteboard.html")


@app.route('/pronunce')
def pronunce():
    return render_template('pronunce.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})

    if file:
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        tyu=[]
        pdf_document = fitz.open(file_path)
        syllabified_text = []
        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            extracted_text = page.get_text()
            print(extracted_text)
            tyu.append(str(extracted_text))
            words = extracted_text.split()
            syllables = []

            for word in words:
                clean_word = word.strip(".,:;!?")
                if len(clean_word) > 2:
                    syllabified = SonoriPy(clean_word)
                    syllables.append("-".join(syllabified))
                    syllables.append("denotes"+" "+str(clean_word))
                else:
                    syllables.append(clean_word)

            syllabified_text.extend(syllables)
        print(tyu)
        return jsonify({"syllabified_text": syllabified_text})


@app.route('/quiz')
def quiz():

    return render_template('quiz.html')

@app.route('/get_question', methods=['POST'])
def get_question():
    """
    Fetch a quiz question based on the topic.
    """
    topic = request.json['topic']
    question, answer = fetch_quiz_question(topic)
    if question and answer:
        return jsonify({'question': question, 'answer': answer})
    else:
        return jsonify({'error': 'Unable to fetch question'})
    


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """
    Submit the user's answer and check if it's correct.
    """
    user_answer = request.json['answer']
    correct_answer = request.json['correct_answer']
    
    if user_answer.lower() == correct_answer.lower():
        return jsonify({'response': 'Correct! Well done.'})
    else:
        return jsonify({'response': f"Incorrect. The correct answer is {correct_answer}."})
# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Default voice

# Pages
pages = {
    "chatbot": "summary_chatbot",
    "quiz": "quiz",
    "features": "#features",
    "contact": "#contact"
}

# Text-to-speech function
def speak(text):
    """
    Convert text to speech.
    """
    engine.say(text)
    engine.runAndWait()

# Navigation route
@app.route('/navigate', methods=['POST'])
def navigate():
    data = request.get_json()
    text = data['text'].lower()

    # Find the closest matching page based on Levenshtein distance
    closest_match = None
    min_distance = float('inf')

    for keyword, page in pages.items():
        distance = Levenshtein.distance(text, keyword)
        if distance < min_distance:
            min_distance = distance
            closest_match = page

    # Check if the closest match is found
    if closest_match:
        # If it's an anchor link, just return it as-is
        if closest_match.startswith('#'):
            page_url = closest_match
        else:
            page_url = url_for(closest_match)

        return jsonify({'success': True, 'page_url': page_url})
    else:
        return jsonify({'success': False, 'message': 'Page not found'})

# Continuous voice-controlled navigation
@app.route('/voice_control')
def voice_control():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    # Use text-to-speech to notify the user
    speak("Say the page you want to navigate to or a message to type. Say 'stop' to end.")

    while True:
        with microphone as source:
            print("Listening for command...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")

            # If "stop" is said, break the loop
            if "stop" in command:
                speak("Stopping voice control.")
                break

            # Check if the command is a navigation command (like 'go to chatbot')
            if "go to" in command:
                # Extract the page name (after 'go to')
                page_command = command.split("go to")[1].strip()
                data = {'text': page_command}
                response = navigate()  # Call the navigate route to find the page
                if response.json.get('success'):
                    speak(f"Navigating to {response.json.get('page_url')}")
                else:
                    speak("I couldn't understand the command. Try again.")

            # If it's a message to type (e.g., 'type hi hello world')
            elif "type" in command:
                message = command.split("type")[1].strip()
                # Assuming you want to send this message to the chatbot (or any text field)
                speak(f"Typing message: {message}")
                # Here you can simulate typing the message in a form and submitting it (this part depends on your UI)
                # For now, we'll just simulate a successful response
                speak(f"Message '{message}' sent!")

        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Please say it again.")
        except sr.RequestError as e:
            speak(f"Error with speech service: {e}")

    return jsonify({"success": True, "message": "Voice control ended."})
# def solve_math_question(math_question):
#     try:
#         # Attempt to parse and solve the math question
#         solution = sympify(math_question)
#         print(solution)
#         return str(solution)
#     except SympifyError:
#         print("INvalid")
#         return "Invalid math expression. Please try again."
#
# @app.route('/solve_math', methods=['POST'])
# def solve_math_question_route():
#     data = request.get_json()
#     math_question = data['question']
#     solution = solve_math_question(math_question)
#     return jsonify({"solution": solution})

if __name__ == "__main__":
    app.run(debug=True)
