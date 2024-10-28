from requests import get
from html import unescape
from random import shuffle
from string import ascii_lowercase

response = get("https://opentdb.com/api_token.php?command=request")

response_dict = response.json()

token = response_dict["token"]

url = f"https://opentdb.com/api.php?amount=10&token={token}"

response = get(url)

response_dict = response.json()

questions_list = response_dict["results"]

for question_dict in questions_list:
    question = question_dict["question"]
    correct_answer = question_dict["correct_answer"]
    answers = question_dict["incorrect_answers"]
    answers.append(correct_answer)
    shuffle(answers)

    print(unescape(question))
    print()

    for i in range(len(answers)):
        print(f"\t{ascii_lowercase[i]}) " + unescape(answers[i]))

    print()