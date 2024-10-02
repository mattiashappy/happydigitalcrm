import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('user_message')
def handle_message(message):
    # Process the message from the user and generate a bot response
    response = f"Received your message: {message}"  # Replace this with actual chatbot logic
    emit('bot_response', response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get the port from the environment variable
    socketio.run(app, host='0.0.0.0', port=port)