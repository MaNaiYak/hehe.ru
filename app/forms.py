
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed

from wtforms import StringField, PasswordField, EmailField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Email

import phonenumbers

from app.models import Employer, Candidate


class LoginForm(FlaskForm):
    email = EmailField('Email address', validators=[DataRequired(), Email()])
    is_employer = BooleanField('is Employer ?')
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('remember ?')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email address', validators=[DataRequired(), Email()])
    FIO = StringField('FIO', validators=[DataRequired()])
    phone_number = StringField('Phone', validators=[DataRequired()])
    is_employer = BooleanField('is Employer ?')
    company = StringField('write your company if you is Employer')
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_phone_number(self, phone_number):
        try:
            p = phonenumbers.parse(phone_number.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Invalid phone number')

    def validate_email(self, email):
        if self.is_employer:
            user = Employer.get_by_email(email.data)
        else:
            user = Candidate.get_by_email(email.data)
        if user is not None:
            raise ValidationError('use different email')

    def validate_company(self, company):
        if self.is_employer.data and company.data == '':
            raise ValidationError('if you are Employer, you must to write company name')
        else:
            return


class VacancyForm(FlaskForm):
    position = SelectField('должность', coerce=int)
    city = SelectField('город', coerce=int)
    description = TextAreaField('описание', validators=[DataRequired()])
    salary = IntegerField('зарплата', validators=[DataRequired()])
    submit = SubmitField('Add Vacancy')


class SearchForm(FlaskForm):
    employer = SelectField('работодатель', coerce=int)
    position = SelectField('должность', coerce=int)
    city = SelectField('город', coerce=int)
    key_word = StringField('поиск по словам')
    min_salary = IntegerField('минимальная зп')
    submit = SubmitField('Поиск')


class ResumeForm(FlaskForm):
    position = SelectField('должность', coerce=int)
    city = SelectField('город', coerce=int)
    description = TextAreaField('описание', validators=[DataRequired()])
    salary = IntegerField('зарплата', validators=[DataRequired()])
    submit = SubmitField('Edit Resume')

