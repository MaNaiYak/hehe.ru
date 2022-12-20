import os
from datetime import datetime

from flask import session
from typing import List
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


from app import login, app

import psycopg2


class DataBase(object):
    _db_name = app.config['DB_NAME']
    _db_user = app.config['DB_USER']
    _user_password = app.config['USER_PASSWORD']
    _db_host = app.config['DB_HOST']
    _db_port = app.config['DB_PORT']

    _connection: psycopg2 = None

    @classmethod
    def _to_connect(cls):
        try:
            cls._connection = psycopg2.connect(
                database=cls._db_name,
                user=cls._db_user,
                password=cls._user_password,
                host=cls._db_host,
                port=cls._db_port,
            )
        except psycopg2.OperationalError as ex:
            print(f"{ex}")
        except Exception as ex:
            print(f'{ex}')
        else:
            print("connection is successful")
        return

    @classmethod
    def execute_query(cls, query: str, is_returning: bool = False):
        print(query)
        if cls._connection is None:
            cls._to_connect()
        cls._connection.autocommit = True
        cursor = cls._connection.cursor()
        try:
            cursor.execute(query)
            if is_returning:
                result = cursor.fetchall()
        except psycopg2.OperationalError as ex:
            print(f'{ex}')
        except Exception as ex:
            print(f'{ex}')
        else:
            print("the query is executed")
            if is_returning:
                return result
            else:
                return True
        finally:
            cursor.close()
        return None


class City(object):
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    @classmethod
    def get_all(cls):
        query = '''
        SELECT *
        FROM city'''
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        return result

    @classmethod
    def get_by_id(cls, id: int):
        query = '''
        SELECT * FROM city
        WHERE id = {}'''.format(id)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        arguments = result[0]
        return City(* arguments)


class Employer(UserMixin):
    def __init__(self,
                 id: int,
                 email: str,
                 FIO: str,
                 company: str,
                 phone: str,
                 password_hash: str = None):
        self.id = id
        self.email = email
        self.FIO = FIO
        self.company = company
        self.phone = phone
        self.password_hash = password_hash

    def tuple(self):
        return (self.email, self.FIO, self.company,
                self.phone, self.password_hash)

    @classmethod
    def get_all(cls):
        query = '''
        SELECT id, company
        FROM employer '''
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        return result

    @classmethod
    def get_by_email(cls, email):
        query = '''
        SELECT * FROM employer
        WHERE email = '{}' '''.format(email)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        arguments = result[0]
        return Employer(* arguments)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_id(cls, id: int):
        query = '''
        SELECT * FROM employer
        WHERE id = {}'''.format(id)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        arguments = result[0]
        return Employer(* arguments)

    @classmethod
    def add(cls, employer):
        query = '''
        INSERT INTO employer (email, FIO, company, phone_number, password_hash)
        VALUES {}'''.format(employer.tuple())
        return DataBase.execute_query(query)


class Specialization(object):
    pass


class Position(object):
    def __init__(self, id: int, specialization_id: int, name: str):
        self.id = id
        self.specialization_id = specialization_id
        self.name = name

    @classmethod
    def get_all(cls):
        query = '''
        SELECT id, name 
        FROM position'''
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        return result

    @classmethod
    def get_by_id(cls, id: int):
        query = '''
        SELECT * FROM position
        WHERE id = {}'''.format(id)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        arguments = result[0]
        return Position(* arguments)


class Vacancy(object):
    def __init__(self,
                 id: int,
                 employer_id: int,
                 position_id: int,
                 city_id: int,
                 description: str,
                 salary: int):
        self.id = id
        self.employer_id = employer_id
        self.position_id = position_id
        self.city_id = city_id
        self.description = description
        self.salary = salary
        self.employer = None
        self.position = None
        self.city = None

    def tuple(self):
        return (self.employer_id,
                self.position_id,
                self.city_id,
                self.description,
                self.salary)

    @classmethod
    def add(cls, vacancy):
        query = '''
        INSERT INTO vacancy (employer_id, position_id, city_id, description, salary)
        VALUES {}'''.format(vacancy.tuple())
        return DataBase.execute_query(query)

    @classmethod
    def get_all_with_params(cls,
                            with_params: bool = False,
                            employer_id: int = None,
                            position_id: int = None,
                            city_id: int = None,
                            key_words: list = None,
                            min_salary: int = None):
        query = '''
        SELECT * FROM vacancy
        INNER JOIN employer ON vacancy.employer_id = employer.id
        INNER JOIN position ON vacancy.position_id = position.id
        INNER JOIN city ON vacancy.city_id = city.id 
        '''
        and_flag = False
        if with_params:
            query += '\nWHERE '
            if employer_id is not None:
                query += ' vacancy.employer_id = {} \n'.format(employer_id)
                and_flag = True
            if position_id is not None:
                if and_flag:
                    query += ' and '
                query += ' vacancy.position_id = {} \n'.format(position_id)
                and_flag = True
            if city_id is not None:
                if and_flag:
                    query += ' and '
                query += ' vacancy.city_id = {} \n'.format(city_id)
                and_flag = True
            if min_salary is not None:
                if and_flag:
                    query += ' and '
                query += ' vacancy.salary >= {} \n'.format(min_salary)
                and_flag = True
            if key_words is not None:
                if and_flag:
                    query += ' and '
                gen_str = ''
                flag = False
                for word in key_words:
                    if flag:
                        gen_str += ' and '
                    gen_str += " vacancy.description LIKE '%{}%' ".format(word)
                    flag = True
                query += gen_str

        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        vacancies = []
        for item in result:
            vacancy = Vacancy(* item[:6:1])
            vacancy.employer = Employer(* item[6:12:1])
            vacancy.position = Position(* item[12:15:1])
            vacancy.city = City(* item[15::1])
            vacancies.append(vacancy)
        return vacancies

    @classmethod
    def get_all_by_employer_id(cls, employer_id):
        query = '''
        SELECT * FROM vacancy
        INNER JOIN employer ON vacancy.employer_id = employer.id
        INNER JOIN position ON vacancy.position_id = position.id
        INNER JOIN city ON vacancy.city_id = city.id
        WHERE employer_id = {}'''.format(employer_id)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        vacancies = []
        for item in result:
            vacancy = Vacancy(* item[:6:1])
            vacancy.employer = Employer(* item[6:12:1])
            vacancy.position = Position(* item[12:15:1])
            vacancy.city = City(* item[15::1])
            vacancies.append(vacancy)
        return vacancies

    @classmethod
    def get_by_id(cls, id):
        query = '''
        SELECT * FROM vacancy
        INNER JOIN employer ON vacancy.employer_id = employer.id
        INNER JOIN position ON vacancy.position_id = position.id
        INNER JOIN city ON vacancy.city_id = city.id
        WHERE vacancy.id = {}'''.format(id)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        item = result[0]
        vacancy = Vacancy(* item[:6:1])
        vacancy.employer = Employer(* item[6:12:1])
        vacancy.position = Position(* item[12:15:1])
        vacancy.city = City(* item[15::1])
        return vacancy


class Candidate(UserMixin):
    def __init__(self,
                 id: int,
                 email: str,
                 FIO: str,
                 phone: str,
                 password_hash: str = None):
        self.id = id
        self.email = email
        self.FIO = FIO
        self.phone = phone
        self.password_hash = password_hash
        self.resume = None

    def tuple(self):
        return (self.email, self.FIO, self.phone, self.password_hash)

    @classmethod
    def get_by_email(cls, email):
        query = '''
        SELECT * FROM candidate
        WHERE email = '{}' '''.format(email)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        arguments = result[0]
        return Candidate(* arguments)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_id(cls, id: int):
        query = '''
        SELECT * FROM candidate
        WHERE id = {}'''.format(id)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        arguments = result[0]
        return Candidate(* arguments)

    @classmethod
    def add(cls, employer):
        query = '''
        INSERT INTO candidate (email, FIO, phone_number, password_hash)
        VALUES {}'''.format(employer.tuple())
        return DataBase.execute_query(query)


class Response(object):
    def __init__(self, candidate_id: int, vacancy_id: int, response_date: datetime):
        self.candidate_id = candidate_id
        self.vacancy_id = vacancy_id
        self.response_date = response_date
        self.candidate = None

    @classmethod
    def add(cls, candidate_id: int, vacancy_id: int):
        query = '''
        INSERT INTO response (candidate_id, vacancy_id, response_date)
        VALUES ({}, {}, '{}' )'''.format(candidate_id, vacancy_id, str(datetime.now()))
        return DataBase.execute_query(query)

    @classmethod
    def get_by_vacancy_id(cls, vacancy_id: int):
        query = '''
        SELECT * FROM response INNER JOIN candidate ON response.candidate_id = candidate.id
        WHERE vacancy_id = {}'''.format(vacancy_id)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        responses = []
        for item in result:
            response = Response(* item[0:3:1])
            response.candidate = Candidate(* item[3::1])
            responses.append(response)
        return responses

    @classmethod
    def is_response(cls, candidate_id: int, vacancy_id: int):
        query = '''
        SELECT * FROM response
        WHERE candidate_id = {} and vacancy_id = {}'''.format(candidate_id, vacancy_id)
        result = DataBase.execute_query(query, True)
        if result is None:
            return None
        elif len(result) == 0:
            return False
        else:
            return True


class Resume(object):
    def __init__(self, id: int, candidate_id: int,
                 position_id: int, city_id: int,
                 description: str, salary: int):
        self.id = id
        self.candidate_id = candidate_id
        self.position_id = position_id
        self.city_id = city_id
        self.description = description
        self.salary = salary
        self.position = None
        self.city = None

    def tuple(self):
        return (self.candidate_id, self.position_id,
                self.city_id, self.description, self.salary)

    @classmethod
    def add(cls, resume):
        query = '''
        INSERT INTO resume (candidate_id, position_id, city_id, description, salary)
        VALUES {} '''.format(resume.tuple())
        return DataBase.execute_query(query)

    @classmethod
    def update(cls, resume):
        query = '''
        UPDATE resume
        SET position_id = {}, city_id = {} , description = '{}', salary = {}
        WHERE candidate_id = {} '''.format(resume.position_id, resume.city_id,
                                           resume.description, resume.salary, resume.candidate_id)
        return DataBase.execute_query(query)

    @classmethod
    def get_by_candidate_id(cls, candidate_id):
        query = '''SELECT * FROM resume
        INNER JOIN position ON resume.position_id = position.id
        INNER JOIN city ON resume.city_id = city.id
        WHERE candidate_id = {} '''.format(candidate_id)
        result = DataBase.execute_query(query, True)
        if result is None or len(result) == 0:
            return None
        arguments = result[0]
        resume = Resume(* arguments[:6])
        resume.position = Position(* arguments[6:9])
        resume.city = City(* arguments[9:])
        return resume


@login.user_loader
def load_user(id: str):
    if session['role'] == 'employer':
        user = Employer.get_by_id(int(id))
    elif session['role'] == 'candidate':
        user = Candidate.get_by_id(int(id))
    else:
        user = None
    print(f'user {user} loaded')
    return user
