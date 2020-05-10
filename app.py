from flask import Flask, render_template, redirect, request
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired, Email
import json

with open('data.json', 'r') as f:
    lst_data = json.load(f)

dict_week_days = {'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда',
             'thu': 'Четверг', 'fri': 'Пятница', 'sat': 'Суббота', 'sun': 'Воскресенье'}

class ClientContacts(FlaskForm):
    clientName = StringField('Вас зовут', [InputRequired()])
    clientPhone = StringField('Ваш телефон', [InputRequired()])


app = Flask(__name__)
app.secret_key = 'beatles'

@app.route('/')  #здесь будет главная
def index():
    return render_template('index.html')

@app.route('/goals/<goal>/') #здесь будет цель <goal>
def goals(goal):
    return render_template('goal.html')

@app.route('/profiles/<int:id_teacher>/') #здесь будет преподаватель <id учителя>
def profiles(id_teacher):
    return render_template('profile.html',
                           data_teacher=lst_data[1][int(id_teacher)],
                           goals=lst_data[0],
                           dict_week_days=dict_week_days)

@app.route('/request_teacher/') #здесь будет заявка на подбор
def request_teacher():
    return render_template('request.html')

@app.route('/request_done/')   #заявка на подбор отправлена
def request_done():
    return render_template('request_done.html')

#здесь будет форма бронирования <id учителя
@app.route('/booking/<int:id_teacher>/<week_day>/<int:time>/', methods=['GET','POST'])
def booking(id_teacher, week_day, time):
    form = ClientContacts()
    #if request.method == 'POST':
    #    return render_template('booking_done.html',
    #                           name=form.clientName.data,
    #                           phone=form.clientPhone.data)
                               #data_teacher=lst_data[1][int(id_teacher)],
                               #week_day_rus=dict_week_days[week_day],
                               #time=time)
    return render_template('booking.html',
                           data_teacher=lst_data[1][int(id_teacher)],
                           week_day=week_day,
                           dict_week_days=dict_week_days,
                           time=time, form=form)

@app.route('/booking_done/', methods=['GET', 'POST'])   #заявка отправлена
def booking_done():
    form = ClientContacts()
    #id_teacher = form.clientTeacher.data
    #client = request.form['clientName']
    phone = form.clientPhone.data
    #week_day = form.clientWeekday.data
    #time = form.clientTime.data
    return render_template('booking_done.html',
                           #client=client,
                           phone=phone)
        #                   week_day=week_day, time=time,
        #                   name_teacher=lst_data[1][int(id_teacher)]['name'])

if __name__ == '__main__':
    app.run()  # запустим сервер