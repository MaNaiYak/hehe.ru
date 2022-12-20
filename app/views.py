import os

from flask import render_template, flash, redirect, url_for, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

from app import app

from app.forms import LoginForm, RegistrationForm, VacancyForm, SearchForm, ResumeForm
from app.models import Employer, Candidate, Vacancy, City, Position, Response, Resume


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        if form.is_employer.data:
            # логинизация для Employe
            user = Employer.get_by_email(form.email.data)
            session['role'] = 'employer'
        else:
            # логинизация для Candidate
            user = Candidate.get_by_email(form.email.data)
            session['role'] = 'candidate'
        if user is None or not user.check_password(form.password.data):
            flash('invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='login', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session['role'] = None
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.is_employer.data:
            print('empl')
            user = Employer(0, form.email.data, form.FIO.data, form.company.data, form.phone_number.data)
            user.set_password(form.password.data)
            if not Employer.add(user):
                abort(500)
        else:
            print('cand')
            user = Candidate(0, form.email.data, form.FIO.data, form.phone_number.data)
            user.set_password(form.password.data)
            if not Candidate.add(user):
                abort(500)
        flash('you are registered')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/add_vacancy', methods=['GET', 'POST'])
@login_required
def add_vacancy():
    if session['role'] != 'employer':
        return redirect(url_for('index'))
    form = VacancyForm()
    # получаем из базы списки и передаём их как варианты выбора
    cities = City.get_all()
    if cities is None:
        cities = []
    form.city.choices = cities
    # оже самое для позиций
    positions = Position.get_all()
    if positions is None:
        positions = []
    form.position.choices = positions
    if form.validate_on_submit():
        vacancy = Vacancy(0, current_user.id, form.position.data, form.city.data,
                          form.description.data, form.salary.data)
        print('объект вакансии создан')
        if not Vacancy.add(vacancy):
            abort(500)
        flash('вакансия добавлена успешно')
        return redirect(url_for('employer_vacancies'))
    return render_template('add_vacancy.html', title='add vacancy', form=form)


@app.route('/employer/<employer_id>')
@login_required
def employer_profile(employer_id):
    vacancies = Vacancy.get_all_by_employer_id(employer_id)
    employer = Employer.get_by_id(employer_id)
    if vacancies is None:
        vacancies = []
    return render_template('employer_vacancies.html', title='employer vacancies', vacancies=vacancies,
                           employer=employer)


@app.route('/vacancy/<vacancy_id>')
def vacancy(vacancy_id):
    vac = Vacancy.get_by_id(vacancy_id)
    responses = None
    is_employer = False
    is_response = False
    if current_user.is_authenticated:
        if session['role'] == 'employer':
            is_employer = True
            if vac.employer_id == current_user.id:
                responses = Response.get_by_vacancy_id(vacancy_id)
            is_response = None
        else:
            is_employer = False
            is_response = Response.is_response(current_user.id, vacancy_id)
            if is_response is None:
                abort(500)
    return render_template('vacancy.html', title='vacancy', is_employer=is_employer,
                           responses=responses, vacancy=vac, is_response=is_response)


@app.route('/to_response/<vacancy_id>')
@login_required
def to_response(vacancy_id):
    if session['role'] != 'candidate':
        flash('not a candidate cant to response on vacancy')
        return redirect(url_for('index'))
    if not Response.add(current_user.id, vacancy_id):
        abort(500)
    return redirect(url_for('vacancy', vacancy_id=vacancy_id))


@app.route('/candidate/<candidate_id>')
@login_required
def candidate_profile(candidate_id):
    is_candidate = False
    # если другой кандидат пытается посмтореть чужой профиль
    if session['role'] == 'candidate' and int(current_user.id) != int(candidate_id):
        print(f'redirect user_id = {current_user.id}')
        return redirect(url_for('index'))
    elif session['role'] == 'candidate':
        is_candidate = True
    candidate = Candidate.get_by_id(candidate_id)
    resume = Resume.get_by_candidate_id(candidate_id)
    return render_template('candidate_profile.html', title='candidate profile', candidate=candidate, resume=resume,
                           is_candidate=is_candidate)


@app.route('/edit_resume', methods=['GET', 'POST'])
@login_required
def edit_resume():
    if session['role'] != 'candidate':
        return redirect(url_for('index'))
    form = ResumeForm()

    cities = City.get_all()
    if cities is None:
        cities = []
    cities.insert(0, (0, '-'))
    form.city.choices = cities
    positions = Position.get_all()
    if positions is None:
        positions = []
    positions.insert(0, (0, '-'))
    form.position.choices = positions

    if form.validate_on_submit():
        position_id = form.position.data
        if position_id == 0:
            position_id = None
        city_id = form.city.data
        if city_id == 0:
            city_id = None
        resume = Resume(0, current_user.id, position_id, city_id, form.description.data, form.salary.data)

        if Resume.get_by_candidate_id(current_user.id) is None:
            # резюме ещё не существует -> создаём его
            if not Resume.add(resume):
                abort(500)
        else:
            # резюме существует -> обновляем его
            if not Resume.update(resume):
                abort(500)
        return redirect(url_for('candidate_profile', candidate_id=current_user.id))
    elif request.method == 'GET':
        old_resume = Resume.get_by_candidate_id(current_user.id)
        if old_resume is not None:
            form.description.data = old_resume.description
            form.salary.data = old_resume.salary
            form.city.data = old_resume.city_id
            form.position.data = old_resume.position_id
    return render_template('edit_resume.html', title='Edit Resume', form=form)


@app.route('/all_vacancies', methods=['GET', 'POST'])
def vacancy_searching():
    form = SearchForm()

    cities = City.get_all()
    if cities is None:
        cities = []
    cities.insert(0, (0, '-'))
    form.city.choices = cities

    positions = Position.get_all()
    if positions is None:
        positions = []
    positions.insert(0, (0, '-'))
    form.position.choices = positions

    employers = Employer.get_all()
    if employers is None:
        employers = []
    employers.insert(0, (0, '-'))
    form.employer.choices = employers

    if form.validate_on_submit():
        employer_id = form.employer.data
        if employer_id == 0:
            employer_id = None
        position_id = form.position.data
        if position_id == 0:
            position_id = None
        city_id = form.city.data
        if city_id == 0:
            city_id = None
        string = form.key_word.data
        if string == '':
            key_words = None
        else:
            key_words = string.strip().split()
        min_salary = form.min_salary.data
        vacancies = Vacancy.get_all_with_params(with_params=True, employer_id=employer_id,
                                                position_id=position_id, city_id=city_id,
                                                key_words=key_words, min_salary=min_salary)
        return render_template('vacancy_searching.html', title='Searching', form=form, vacancies=vacancies)
    vacancies = Vacancy.get_all_with_params()
    form.min_salary.data = 0
    return render_template('vacancy_searching.html', title='Searching', form=form, vacancies=vacancies)


'''
Employer - создать вакансию + , просматривать список своих вакансий + и откликнувшихся узеров (их профили) +
 (осатлось сделать переход на вакансию и просмотр по ней юзеров) +

(сделать юзерам лк с резюме)
Candidate - откликнуться на вакансию + , создать резюме, просматривать все вакансии и филтровать по типу +
+ текстовый поиск по описанию и названию + 

прошло сели 20:50 закончили 3:30 => уже 6:40

начало: 14:50 - 22 => 7:10
7:10 + 6:40 - 1 = 12:50
ну и минус час где-то 

осталось 
создание и редактирование реземе + 
и ссылки для наигации 
и профиль компании + 

'''

