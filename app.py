from flask import Flask, render_template, redirect, request
from flask_wtf import FlaskForm, CsrfProtect
from wtforms import StringField, RadioField, HiddenField
from wtforms.validators import InputRequired, Email
import json
from numpy.random import default_rng
import numpy as np

##### получаем данные из json файла
with open('data.json', 'r') as f:
    lst_data = json.load(f)

##### добавим справочники дней недели и доступного времени
dict_week_days = {'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда',
             'thu': 'Четверг', 'fri': 'Пятница', 'sat': 'Суббота', 'sun': 'Воскресенье'}

dict_available_time = {'a': '1-2 часа в неделю', 'b': '3-5 часов в неделю',
                      'c': '5-7 часов в неделю', 'd': '7-10 часов в неделю'}


##### функция для добавления информации о клиентах в файл
def appending_json(file_name, appended_element):
    lst_data = []
    with open(file_name, 'r') as f:
        lst_data = json.load(f)
    lst_data.append(appended_element)
    with open(file_name, 'w') as f:
        json.dump(lst_data, f)


##### функция выдает всех учителей, у которых есть выбранная цель
def get_teachers(all_teachers_lst, goal):
    lst = []
    for i, teacher in enumerate(all_teachers_lst):
        if goal in teacher["goals"]:
            lst.append(teacher)
    return lst


##### формы для бронирования учителей и запроса на подбор
class ClientContacts(FlaskForm):
    clientName = StringField('Вас зовут', [InputRequired(message='Эта информация нам нужна для обратной связи')])
    clientPhone = StringField('Ваш телефон', [InputRequired(message='Эта информация нам нужна для обратной связи')])
    clientTeacher = HiddenField()
    clientWeekday = HiddenField()
    clientTime = HiddenField()

class ClientRequest(FlaskForm):
    clientAvailableTime = RadioField('Сколько времени есть?', default='a',
                                     choices=[(key, value) for key, value in dict_available_time.items()])
    clientGoal = RadioField('Какая цель занятий?', default='travel',
                            choices=[(key, value[0]) for key, value in lst_data[0].items()])


############################## FLASK ################################
app = Flask(__name__)
app.secret_key = 'the_best_of_the_best_tutors'

# csrf = CsrfProtect()
# app.config.from_object('config.settings')
# csrf.init_app(app)


#здесь будет главная
@app.route('/')   # выводим 6 случайных преподавателей
@app.route('/<all>/')  # выводим всех преподавателей
def index(all=None):
    if all == 'all':
        n = len(lst_data[1])
    else:
        n = 6
    rng = default_rng()
    teachers = rng.choice(lst_data[1], size=n, replace=False)
    goals = lst_data[0]
    return render_template('index.html', teachers=teachers, goals=goals)


#здесь будет цель <goal>
@app.route('/goals/<goal>/')
def goals(goal):
    teachers = get_teachers(lst_data[1], goal)
    # получаем индексы отсортированные по убыванию рейтинга
    ids_sorted = np.argsort(-np.array([teacher['rating'] for teacher in teachers]))
    # формируем отсортированный список учитилей
    teachers_sorted = []
    for i in ids_sorted:
        teachers_sorted.append(teachers[i])
    return render_template('goal.html', goal=lst_data[0][goal], teachers=teachers_sorted)


@app.route('/profiles/<int:id_teacher>/') #здесь будет преподаватель <id учителя>
def profiles(id_teacher):
    return render_template('profile.html',
                           teacher=lst_data[1][int(id_teacher)],
                           goals=lst_data[0],
                           dict_week_days=dict_week_days)


@app.route('/request_teacher/') #здесь будет заявка на подбор
def request_teacher():
    RequestForm = ClientRequest()
    ContactsForm = ClientContacts()
    return render_template('request.html', RequestForm=RequestForm, ContactsForm=ContactsForm)


@app.route('/request_teacher_done/', methods=['POST'])   #заявка на подбор отправлена
def request_teacher_done():
    RequestForm = ClientRequest()
    ContactsForm = ClientContacts()
    if request.method == 'POST':
        available_time = dict_available_time[RequestForm.clientAvailableTime.data]
        goal = lst_data[0][RequestForm.clientGoal.data][0]
        client_name = ContactsForm.clientName.data
        client_phone = ContactsForm.clientPhone.data
        d = {'client_name': client_name, 'client_phone': client_phone,
             'goal': goal, 'available_time': available_time}
        appending_json('client_applications.json', d)
        return render_template('request_done.html', available_time=available_time,
                               goal=goal, client_name=client_name, client_phone=client_phone)
    return render_template('request.html', RequestForm=RequestForm, ContactsForm=ContactsForm)


#здесь будет форма бронирования
#@app.route('/booking/', methods=['GET', 'POST'])
@app.route('/booking/<int:id_teacher>/<week_day>/<time>/', methods=['GET', 'POST'])
def booking(id_teacher, week_day, time):
    form = ClientContacts()
    if form.validate_on_submit():
        name = form.clientName.data
        phone = form.clientPhone.data
        week_day_hidden = form.clientWeekday.data
        time_hidden = form.clientTime.data
        id_teacher_hidden = form.clientTeacher.data
        d = {'clientName': name, 'clientPhone': phone,
             'id_teacher': id_teacher_hidden, 'week_day': week_day_hidden, 'time': time_hidden}
        appending_json('client_booking.json', d)
        return render_template('booking_done.html',
                               name=name,
                               phone=phone,
                               id_teacher=id_teacher,
                               week_day_ru=dict_week_days[week_day],
                               time=time)
    return render_template('booking.html',
                           data_teacher=lst_data[1][int(id_teacher)],
                           id_teacher=id_teacher,
                           week_day=week_day,
                           dict_week_days=dict_week_days,
                           time=time, form=form)

#@app.route('/booking_done/', methods=['GET', 'POST'])   #заявка отправлена
#def booking_done():
    # form = ClientContacts(request.form)
    # id_teacher = form.clientTeacher.data
    # client = request.form['clientName']
    # phone = form.clientPhone.data
    # week_day = form.clientWeekday.data
    # time = form.clientTime.data
    # appending_json('client_applications.json', d)
    # return render_template('booking_done.html',
    #                        client=client,
    #                        phone=phone,
    #                        week_day=week_day, time=time,
    #                        name_teacher=lst_data[1][int(id_teacher)]['name'])

if __name__ == '__main__':
    app.run()  # запустим сервер