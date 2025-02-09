from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///responses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

# Database model for storing questions and answers
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(500), nullable=False)
    choice_a = db.Column(db.String(500), nullable=False)
    choice_b = db.Column(db.String(500), nullable=False)
    choice_c = db.Column(db.String(500), nullable=False)
    choice_d = db.Column(db.String(500), nullable=False)

# Database model for storing user responses
class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_answer = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    description = db.Column(db.String(1000), nullable=True)

@app.route('/')
def index():
    return redirect(url_for('start_review'))

@app.route('/start')
def start_review():
    # Select 5 random questions from the database
    questions = Question.query.all()
    random_questions = random.sample(questions, min(5, len(questions)))
    return render_template('review.html', questions=random_questions)

@app.route('/submit', methods=['POST'])
def submit():
    responses = []
    for question_id in request.form.getlist('question_id'):
        selected_answer = request.form.get(f'answer_{question_id}')
        description = request.form.get(f'description_{question_id}', '')

        question = Question.query.get(question_id)
        is_correct = selected_answer == question.correct_answer

        response = Response(
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
            description=description
        )
        responses.append(response)

    db.session.add_all(responses)
    db.session.commit()

    return redirect(url_for('thank_you'))

@app.route('/thank_you')
def thank_you():
    return "Thank you for your feedback!"


@app.route('/results')
def results():
    responses = Response.query.all()
    results_data = []
    
    for response in responses:
        question = Question.query.get(response.question_id)
        results_data.append({
            "question": question.question,
            "selected_answer": response.selected_answer,
            "correct_answer": question.correct_answer,
            "is_correct": response.is_correct,
            "description": response.description
        })
    
    return render_template('results.html', results=results_data)


@app.route('/import_excel', methods=['GET', 'POST'])
def import_excel():
    if request.method == 'POST':
        # Get the uploaded file
        file = request.files['file']
        if file:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(file)

            for _, row in df.iterrows():
                # Parse the 'answer' column to extract choices
                try:
                    choices = eval(row['answer'])  # Convert the string to a dictionary
                except Exception as e:
                    flash(f"Error parsing answers: {e}", 'danger')
                    return redirect(url_for('import_excel'))

                # Extract individual choices
                choice_a = choices.get('1', '')
                choice_b = choices.get('2', '')
                choice_c = choices.get('3', '')
                choice_d = choices.get('4', '')

                # Extract the correct choice number and match it to the text
                correct_choice_number = str(row['correct answer'])
                correct_answer = choices.get(correct_choice_number, '')

                # Add the question and choices to the database
                question = Question(
                    question=row['question'],
                    correct_answer=correct_answer,
                    choice_a=choice_a,
                    choice_b=choice_b,
                    choice_c=choice_c,
                    choice_d=choice_d
                )
                db.session.add(question)

            db.session.commit()
            flash('Questions imported successfully!', 'success')
            return redirect(url_for('index'))

    return '''
    <!doctype html>
    <title>Import Questions</title>
    <h1>Upload Excel File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == '__main__':
    # Initialize the database and run the application
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)

