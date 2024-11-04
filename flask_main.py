from flask import Flask, render_template, request, redirect, url_for, session
from requests import get
from html import unescape
from random import shuffle
import sqlite3

# Sets up the Flask application.
app = Flask(__name__)
app.secret_key = 'secret_key'

# The home page, where users will choose what they want to do.
@app.route("/")
def home():
    return render_template("home.html")

# This function doesn't display a page, but sets up the quiz with the desired options before rerouting to the quiz proper.
@app.route("/quiz-reroute", methods=["GET", "POST"])
def quizReroute():
    # Gets the desired category and difficulty from the form.
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

    # This adds the questions to the session, so they will be remembered as the user is redirected, along with the current question index and the number of correct answers.
    session["questions_list"] = questions_list
    session["index"] = 0
    session["correct"] = 0
    session["quiz_size"] = size

    # Redirects to the quiz page, which will cycle through questions until all ten questions have been answered.
    return redirect(url_for('quiz'))

# The quiz page, where users will actually take the quiz one question at a time.
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    # Executes if the user has already answered a question. If not, the first question will display.
    if request.method == "POST":

        # Gets the answer and index of that answer.
        answer = request.form.get("flexRadioDefault")
        answer_index = session["questions_list"][session["index"]]["answers"].index(answer)

        # If the answer is correct, increment the correct counter and add a green checkmark emoji for displaying the answers at the end of the quiz.
        if answer == session["questions_list"][session["index"]]["correct_answer"]:
            session["correct"] += 1
            session["questions_list"][session["index"]]["answers"][answer_index] += unescape(" &#9989;")

        # If the answer is incorrect, add a red X emoji to the incorrect answer and point to the correct answer for displaying later.
        else:
            correct_index = session["questions_list"][session["index"]]["answers"].index(session["questions_list"][session["index"]]["correct_answer"])
            session["questions_list"][session["index"]]["answers"][correct_index] += unescape(" &larr; Correct")
            session["questions_list"][session["index"]]["answers"][answer_index] += unescape(" &#10060;")

        # Moves to the next question.
        session["index"] += 1

    # If the quiz has ended, reroute to the end page.
    if session["index"] == session["quiz_size"]:
        return redirect(url_for("quiz_completed"))

    # If not, display the next question.
    else:
        question_dict = session["questions_list"][session["index"]]
        return render_template("quiz.html", question_dict=question_dict)

# The page users see after completing a quiz, showing the number of correct answers and which questions they got right and wrong.
@app.route("/quiz-completed", methods=["GET", "POST"])
def quiz_completed():
    # Get all the necessary variables from the session and display the page.
    correct = session["correct"]
    quiz_size = session["quiz_size"]
    questions_list = session["questions_list"]
    return render_template("quiz_completed.html", correct=correct, quiz_size=quiz_size, questions_list=questions_list)

# The page where users are able to make their own quizzes.
@app.route("/create-quiz", methods=["GET", "POST"])
def create_quiz():
    # Get the desired length of the quiz and display the page.
    session["new_quiz_size"] = int(request.form.get("size"))
    return render_template("create_quiz.html", size=session["new_quiz_size"])

# This isn't a page that's shown to the user, just an easy way of dealing with the newly created quiz.
@app.route("/create-quiz-reroute", methods=["GET", "POST"])
def create_quiz_reroute():

    # Gets the size of the new quiz.
    size = session["new_quiz_size"]

    # Find the max quiz ID of the current quizzes; the new quiz will have an ID that is one more than the previous max.
    connection = sqlite3.connect("user_quizzes.db")
    cursor = connection.cursor()
    quiz_id = cursor.execute("SELECT MAX(QuizID) FROM Quizzes").fetchone()[0] + 1
    cursor.close()
    connection.commit()
    connection.close()

    # Iterates through each new question and adds to the database of quizzes.
    for i in range(size):

        # Gets the question and answers.
        new_question = request.form.get(f"question_{i}")
        new_correct = request.form.get(f"correct_{i}")
        new_incorrect1 = request.form.get(f"incorrect1_{i}")

        # Makes sure the question, correct answer, and at least one incorrect answer are present.
        if new_question == "" or new_correct == "" or new_incorrect1 == "":
            return redirect(url_for('create_quiz'))

        # Prepares the data in a format SQLite3 will accept.
        question = [new_question, new_correct, new_incorrect1, request.form.get(f"incorrect2_{i}"), request.form.get(f"incorrect3_{i}"), quiz_id]
        
        # Adds the question to the table. The table is a list of every question from every created quiz. Questions in a quiz are linked to each other through the QuizID value.
        connection = sqlite3.connect("user_quizzes.db")
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Quizzes (Question, CorrectAnswer, IncorrectAnswer1, IncorrectAnswer2, IncorrectAnswer3, QuizID) VALUES (?, ?, ?, ?, ?, ?)", question)
        cursor.close()
        connection.commit()
        connection.close()

    return render_template("create_quiz_reroute.html", code=quiz_id)

# Another reroute, which isn't shown to the user, but instead redirects to the quiz page, after formatting the quiz questions from the custom quiz.
@app.route("/custom-quiz-reroute", methods=["GET", "POST"])
def custom_quiz_reroute():
    # Gets the QuizID of the requested quiz.
    quiz_id = int(request.form.get("code"))
    
    # Gets all the questions from that quiz in the table.
    connection = sqlite3.connect("user_quizzes.db")
    cursor = connection.cursor()
    questions_dirty = cursor.execute("SELECT * FROM Quizzes WHERE QuizID = ?", (quiz_id,)).fetchall()
    cursor.close()
    connection.commit()
    connection.close()
    
    # Formats the quiz in a way the quiz page will like.
    questions_list = []
    for question in questions_dirty:
        new_dict = {}

        # The question and correct answer are moved over to a dictionary.
        new_dict["question"] = question[1]
        new_dict["correct_answer"] = question[2]

        # The correct answer is inserted into the incorrect answers and shuffled.
        answers = list(question[3:6])
        answers.append(new_dict["correct_answer"])
        shuffle(answers)

        # Adds the answers to the dictionary.
        new_dict["answers"] = answers

        # Removes any blank answers, since not all incorrect answers are required.
        while "" in answers:
            answers.remove("")

        # Adds the question dictionary to the overall list of questions.
        questions_list.append(new_dict)

    # This adds the questions to the session, so they will be remembered, along with the current question index and the number of correct answers.
    session["questions_list"] = questions_list
    session["index"] = 0
    session["correct"] = 0
    session["quiz_size"] = len(questions_dirty)

    # Redirects to the quiz page, which will cycle through questions until all ten questions have been answered.
    return redirect(url_for('quiz'))