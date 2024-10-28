import customtkinter
from random import shuffle
from requests import get
from html import unescape

class QuestionFrame(customtkinter.CTkFrame):
    def __init__(self, parent, question, incorrect_answers, correct_answer):
        super().__init__(parent)

        self.question = customtkinter.CTkLabel(self, text=unescape(question))
        self.question.grid(row = 0, column = 1, padx = 10, pady = 10, sticky = "ew")
        self.answers = incorrect_answers
        self.answers.append(correct_answer)
        shuffle(self.answers)
        self.answer_buttons = []
        self.correct_answer = correct_answer
        self.id_variable = customtkinter.StringVar()

        for i, answer in enumerate(self.answers):
            new_button = customtkinter.CTkRadioButton(self, text = answer, variable = self.id_variable, value = answer, command = lambda: parent.nextQuestion(False))
            new_button.grid(row = i + 1, column = 1, padx = 10, pady = (10, 0), sticky = "ew")
            self.answer_buttons.append(new_button)

    def get(self):
        return self.id_variable.get()
    
    def set(self, answer):
        self.id_variable.set(answer)

class App(customtkinter.CTk):
    def __init__(self, title, x_size, y_size):
        super().__init__()

        self.title(title)
        self.geometry(f"{str(x_size)}x{str(y_size)}")
        self.grid_columnconfigure((0, 1, 2), weight = 1)
        self.grid_rowconfigure(0, weight = 1)

        # IMPLEMENT TIMER
        self.checkbox_frame2 = customtkinter.CTkFrame(self)
        self.checkbox_frame2.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = "nswe")

        # IMPLEMENT SHARE FUNCTION
        self.checkbox_frame3 = customtkinter.CTkFrame(self)
        self.checkbox_frame3.grid(row = 0, column = 2, padx = (0, 10), pady = 10, sticky = "nswe")

    def newQuiz(self, size):
        self.response_dict = get(f"https://opentdb.com/api.php?amount={size}").json()["results"]
        self.index = 0
        self.correct = 0
        self.size = size
        self.nextQuestion(True)

    def nextQuestion(self, first):
        if not first:
            answer = self.question_frame.get()
            if answer == self.correct_answer:
                self.correct += 1
            
            print(self.correct)

            self.question_frame.destroy()
            self.index += 1

        if int(self.index) == int(self.size):
            self.finishQuiz()
        else:
            self.question = unescape(self.response_dict[self.index]["question"])
            self.correct_answer = unescape(self.response_dict[self.index]["correct_answer"])
            self.incorrect_answers = unescape(self.response_dict[self.index]["incorrect_answers"])

            for i, answer in enumerate(self.incorrect_answers):
                self.incorrect_answers[i] = unescape(answer)

            self.question_frame = QuestionFrame(self, question=self.question, correct_answer=self.correct_answer, incorrect_answers=self.incorrect_answers)
            self.question_frame.grid(row = 0, column = 1, padx = (0, 10), pady = 10, sticky = "nswe")

    def finishQuiz(self):
        print(f"You got {self.correct}/{self.size} correct.")

app = App("My app", 600, 400)
app.newQuiz("10")
app.mainloop()