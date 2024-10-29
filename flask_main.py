from flask import Flask, render_template, request, redirect, url_for, session
from requests import get
from html import unescape
from random import shuffle

app = Flask(__name__)
app.secret_key = 'secret_key'

# The home page, where users will choose settings for the quiz.
@app.route("/")
def home():
    return render_template("home.html")

# This function doesn't display a page, but sets up the quiz with the desired options before rerouting to the quiz proper.
@app.route("/quiz-reroute", methods=["GET", "POST"])
def quizReroute():
    # Gets the desired category and difficulty from the form
    category = request.form.get("category")
    difficulty = request.form.get("difficulty")
    size = int(request.form.get("size"))

    # Makes a call to the API with the given size, category, and difficulty, and converts into a dictionary of questions.
    questions_list_dirty = get(f"https://opentdb.com/api.php?amount={size}&category={category}&difficulty={difficulty}").json()["results"]

    # Cleans up the question dictionary to fit the app requirements.
    questions_list = []
    for question_dict in questions_list_dirty:
        new_dict = {}

        # These variables stay the same, but some HTML codes need to be converted to normal text.
        new_dict["question"] = unescape(question_dict["question"])
        new_dict["correct_answer"] = unescape(question_dict["correct_answer"])

        # The correct answer is be inserted into the incorrect answers and shuffled. These also need to be converted to normal text.
        answers = question_dict["incorrect_answers"]
        for i, answer in enumerate(answers):
            answers[i] = unescape(answer)
        answers.append(new_dict["correct_answer"])
        shuffle(answers)

        # Adds the reformatted question to the list of questions.
        new_dict["answers"] = answers
        questions_list.append(new_dict)

    # This adds the questions to the session, so they will be remembered, along with the current question index and the number of correct answers.
    session["questions_list"] = questions_list
    session["index"] = 0
    session["correct"] = 0
    session["quiz_size"] = size

    # Redirects to the quiz page, which will cycle through questions until all ten questions have been answered.
    return redirect(url_for('quiz'))

# The quiz page, where users will actually take the quiz one question at a time.
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        if request.form.get("flexRadioDefault") == session["questions_list"][session["index"]]["correct_answer"]:
            session["correct"] += 1

        session["index"] += 1

        if session["index"] == session["quiz_size"]:
            return redirect(url_for("quiz_completed"))
        

    question_dict = session["questions_list"][session["index"]]
    return render_template("quiz.html", question_dict=question_dict)

@app.route("/quiz-completed", methods=["GET", "POST"])
def quiz_completed():
    correct = session["correct"]
    quiz_size = session["quiz_size"]
    print(session["questions_list"])
    return render_template("quiz_completed.html", correct=correct, quiz_size=quiz_size)