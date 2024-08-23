from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

login_manager = LoginManager()
login_manager.init_app(app)

def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"error saving data: {e}")

users_file = 'data/users.json'
donations_file = 'data/donations.json'

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    users = load_data(users_file)
    if username in users:
        return User(username)
    return None

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=35)])
    submit = SubmitField('Register')

class DonationForm(FlaskForm):
    amount = DecimalField('Donation Amount', places=2, validators=[DataRequired()])
    submit = SubmitField('Donate')

    def validate_amount(form,field):
        if float(field.data) <= 0.00:
            raise ValidationError("Donation amount cannot be negative.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        users = load_data(users_file)
        username = form.username.data
        password = form.password.data
        if username in users and users[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        users = load_data(users_file)
        username = form.username.data
        password = form.password.data
        if username not in users:
            users[username] = password
            save_data(users_file, users)
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/donate', methods=['GET', 'POST'])
@login_required
def donate():
    form = DonationForm()
    if form.validate_on_submit():
        amount = form.amount.data
        donations = load_data(donations_file)
        if current_user.is_authenticated:
            username = current_user.id
            if username not in donations:
                donations[username] = []
            donations[username].append(float(amount))
            save_data(donations_file, donations)
            form = DonationForm(
                formdata=None
                                )
            flash(f'You have made a donation of ₹{amount:.2f}. Thank you.','success')
            return render_template('donate.html', form=form)
        # session.pop('message', None)
    return render_template('donate.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
