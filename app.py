import ast
import os

from datetime import datetime
from sqlalchemy import func, case
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from wtforms import StringField, RadioField, HiddenField, FormField
from wtforms.validators import InputRequired

##### добавим справочники дней недели, доступного времени и целей
dict_week_days = {'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда',
             'thu': 'Четверг', 'fri': 'Пятница', 'sat': 'Суббота', 'sun': 'Воскресенье'}

dict_time_ability = {'a': '1-2 часа в неделю', 'b': '3-5 часов в неделю',
                      'c': '5-7 часов в неделю', 'd': '7-10 часов в неделю'}

dict_goals = {"travel": ["для путешествий", "⛱"], "study": ["для учебы", "🏫"],
         "work": ["для работы", "🏢"], "relocate": ["для переезда", "🚜"],
         "developer": ["для программирования", "🔥"]}


##### формы для бронирования учителей и запроса на подбор
class ClientContacts(FlaskForm):
    clientName = StringField('Вас зовут',
                             [InputRequired(message='Эта информация нам нужна для обратной связи')])
    clientPhone = StringField('Ваш телефон',
                              [InputRequired(message='Эта информация нам нужна для обратной связи')])
    clientTeacher = HiddenField()
    clientWeekday = HiddenField()
    clientTime = HiddenField()


class ClientRequest(FlaskForm):
    clientAvailableTime = RadioField('Сколько времени есть?', default='a',
                                     choices=[(key, value) for key, value in dict_time_ability.items()])
    clientGoal = RadioField('Какая цель занятий?', default='travel',
                            choices=[(key, value[0]) for key, value in dict_goals.items()])
    clientName = StringField('Вас зовут',
                             [InputRequired(message='Эта информация нам нужна для обратной связи')])
    clientPhone = StringField('Ваш телефон',
                              [InputRequired(message='Эта информация нам нужна для обратной связи')])


############################## FLASK ################################
app = Flask(__name__)
app.secret_key = 'best_of_the_best_tutors'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)      # единожды запустить flask db init


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    about = db.Column(db.Text, unique=True)
    rating = db.Column(db.Float)
    picture = db.Column(db.Text, unique=True)
    price = db.Column(db.Integer, nullable=False)
    goals = db.Column(db.String(), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    slot = db.relationship("TeacherSlot", back_populates="teacher")
    booking = db.relationship("Booking", back_populates="teacher")


class TeacherSlot(db.Model):
    __tablename__ = "teacher_slots"

    id = db.Column(db.Integer, primary_key=True)
    week_day = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(5), nullable=False)
    is_available = db.Column(db.Boolean, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    teacher = db.relationship("Teacher", back_populates="slot")

    booking = db.relationship("Booking", uselist=False, back_populates="slot")


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    booking = db.relationship("Booking", back_populates="student")
    teacher_request = db.relationship("TeacherRequest", back_populates="student")


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    week_day = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(5), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    slot_id = db.Column(db.Integer, db.ForeignKey("teacher_slots.id"))

    teacher = db.relationship("Teacher", back_populates="booking")
    student = db.relationship("Student", back_populates="booking")
    slot = db.relationship("TeacherSlot", back_populates="booking")


class TeacherRequest(db.Model):
    __tablename__ = "teacher_requests"

    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String())
    time_ability = db.Column(db.String())
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    student = db.relationship("Student", back_populates="teacher_request")


# главная
@app.route('/')   # выводим 6 случайных преподавателей
@app.route('/<all>/')  # выводим всех преподавателей
def index(all=None):
    if all == 'all':
        n = db.session.query(Teacher).count()
    else:
        n = 6
    teachers = db.session.query(Teacher).order_by(func.random()).limit(n)
    goals = dict_goals
    return render_template('index.html', teachers=teachers, goals=goals)


# страница препадавателей с заданной целью
@app.route('/goals/<goal>/')
def goals(goal):
    teachers_db = db.session.query(Teacher)\
        .filter(Teacher.goals.like('%'+goal+'%'))\
        .order_by(Teacher.rating.desc()).all()
    return render_template('goal.html', goal=dict_goals[goal], teachers=teachers_db)


# страница преподавателя
@app.route('/profiles/<int:id_teacher>/')
def profiles(id_teacher):
    teacher_db = db.session.query(Teacher).get_or_404(id_teacher)
    teacher_slot = db.session.query(TeacherSlot)\
        .filter(TeacherSlot.teacher_id == int(id_teacher)).all()

    # Получаем занятые дни
    occupied_days = db.session.query(TeacherSlot.week_day)\
        .filter(TeacherSlot.teacher_id == int(id_teacher))\
        .group_by(TeacherSlot.week_day)\
        .having(func.sum(case([(TeacherSlot.is_available == True, 1)], else_=0)) == 0).all()
    occupied_days = [d[0] for d in occupied_days]

    return render_template('profile.html',
                           id=teacher_db.id,
                           name=teacher_db.name,
                           about=teacher_db.about,
                           picture=teacher_db.picture,
                           rating=teacher_db.rating,
                           price=teacher_db.price,
                           goals=ast.literal_eval(teacher_db.goals),
                           goals_ru=dict_goals,
                           teacher_slot=teacher_slot,
                           occupied_days=occupied_days,
                           dict_week_days=dict_week_days)


# заявка на подбор
@app.route('/request_teacher/', methods=['GET', 'POST'])
def request_teacher():
    form = ClientRequest()
    if request.method == 'POST':   # form.validate_on_submit():
        time_ability = dict_time_ability[form.clientAvailableTime.data]
        goal = form.clientGoal.data
        client_name = form.clientName.data
        client_phone = form.clientPhone.data

        student = Student(name=client_name, phone=client_phone)
        db.session.add(student)

        teacher_request = TeacherRequest(goal=goal, time_ability=time_ability, student=student)
        db.session.add(teacher_request)

        db.session.commit()

        return render_template('request_done.html', time_ability=time_ability,
                               goal=dict_goals[goal][0], client_name=client_name, client_phone=client_phone)
    return render_template('request.html', RequestForm=form)


#форма бронирования
@app.route('/booking/<int:id_teacher>/<week_day>/<time>/', methods=['GET', 'POST'])
def booking(id_teacher, week_day, time):
    teacher_db = db.session.query(Teacher).get_or_404(id_teacher)
    form = ClientContacts()
    if form.validate_on_submit():
        client_name = form.clientName.data
        client_phone = form.clientPhone.data
        week_day_hidden = form.clientWeekday.data
        time_hidden = form.clientTime.data
        id_teacher_hidden = form.clientTeacher.data

        student = Student(name=client_name, phone=client_phone)
        db.session.add(student)

        slot = db.session.query(TeacherSlot)\
            .filter(db.and_(TeacherSlot.teacher_id == id_teacher_hidden,
                    TeacherSlot.week_day == week_day_hidden,
                    TeacherSlot.time == time_hidden)).first()
        slot.is_available = False

        booking = Booking(week_day=week_day_hidden, time=time_hidden,
                          teacher_id=id_teacher_hidden, student=student, slot=slot)
        db.session.add(booking)

        db.session.commit()
        return render_template('booking_done.html',
                               name=client_name,
                               phone=client_phone,
                               id_teacher=id_teacher,
                               week_day_ru=dict_week_days[week_day],
                               time=time)
    return render_template('booking.html',
                           data_teacher=teacher_db,
                           id_teacher=id_teacher,
                           week_day=week_day,
                           dict_week_days=dict_week_days,
                           time=time, form=form)


if __name__ == '__main__':
    app.run()  # запустим сервер