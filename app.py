from flask import Flask, redirect, render_template, request, jsonify, session, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, login_user, logout_user
from models import db, User, Room, Message
from config import Config
from flask_login import LoginManager




app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Укажите имя представления для страницы авторизации


app.secret_key = 'ASDQWER'  # Для работы сессий


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Загрузка пользователя по ID


@app.before_request
def create_tables():
    db.create_all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Проверяем наличие пользователя в базе данных
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            session['username'] = username
            flash('Вы успешно вошли')
            return redirect(url_for('chat'))
        else:
            flash('Невеное имя пользвателя или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    rooms_list = [{'id': room.id, 'name': room.name} for room in rooms]
    return jsonify(rooms_list)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Проверяем, существует ли пользователь
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))

        # Создаем нового пользователя
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Вы успешно зарегистрировались! Теперь войдите в систему.')
        return redirect(url_for('login'))

    return render_template('register.html')

@socketio.on('new_room')
def new_room(data):
    room_name = data['room_name']
    if not Room.query.filter_by(name=room_name).first():
        room = Room(name=room_name)
        db.session.add(room)
        db.session.commit()
        socketio.emit('room_list_updated', {'room_name': room_name})


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    
    # Отправка истории сообщений пользователю
    room_obj = Room.query.filter_by(name=room).first()
    if room_obj:
        messages = Message.query.filter_by(room_id=room_obj.id).order_by(Message.timestamp.desc()).limit(50).all()
        
        history = [
            {
                'username': msg.user.username, 
                'content': msg.content, 
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for msg in messages
        ]
        # Отправляем историю сообщений только присоединившемуся пользователю
        send({'history': history}, to=request.sid)

    # Уведомление о входе в комнату
    send({'username': username, 'message': f"{username} has entered the room."}, to=room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(f"{username} has left the room.", to=room)

@socketio.on('message')
def on_message(data):
    username = data['username']
    room = data['room']
    content = data['message']
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    room_obj = Room.query.filter_by(name=room).first()
    if not room_obj:
        room_obj = Room(name=room)
        db.session.add(room_obj)
        db.session.commit()
    message = Message(user_id=user.id, room_id=room_obj.id, content=content)
    db.session.add(message)
    db.session.commit()
    send({'username': username, 'message': content}, to=room)
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True) 