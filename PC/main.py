import os
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify
import psutil
import subprocess

SESSION_FILE = 'sessions.json'
app = Flask(__name__)

session_data = {
    'start_time': time.time(),
    'sessions': []
}

def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                session_data['sessions'] = data.get('sessions', [])
            except Exception:
                session_data['sessions'] = []

def save_sessions():
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump({'sessions': session_data['sessions']}, f, ensure_ascii=False, indent=2)

def start_session():
    session_data['start_time'] = time.time()
    load_sessions()

def end_session():
    end_time = time.time()
    start_time = session_data.get('start_time', end_time)
    session = {
        'start': datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
        'end': datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S'),
        'duration': str(timedelta(seconds=int(end_time - start_time)))
    }
    session_data['sessions'].append(session)
    save_sessions()

def get_main_programs():
    names = set()
    for proc in psutil.process_iter(['name']):
        name = proc.info['name']
        if name and name.lower() not in ['system idle process', 'system', 'svchost.exe', 'explorer.exe', 'python.exe', 'pythonw.exe']:
            names.add(name)
    return sorted(list(names))

@app.route('/status')
def status():
    uptime_sec = int(time.time() - session_data['start_time'])
    uptime = str(timedelta(seconds=uptime_sec))
    session_duration = uptime  
    return jsonify({
        'status': 'online',
        'uptime': uptime,
        'start_time': datetime.fromtimestamp(session_data['start_time']).strftime('%Y-%m-%d %H:%M:%S'),
        'session_duration': session_duration
    })

@app.route('/programs')
def programs():
    return jsonify({'programs': get_main_programs()})

@app.route('/shutdown')
def shutdown():
    threading.Thread(target=shutdown_pc).start()
    return jsonify({'result': 'ok'})

@app.route('/reboot')
def reboot():
    threading.Thread(target=reboot_pc).start()
    return jsonify({'result': 'ok'})

@app.route('/sleep')
def sleep():
    threading.Thread(target=sleep_pc).start()
    return jsonify({'result': 'ok'})

@app.route('/sessions')
def sessions():
    load_sessions()
    return jsonify({'sessions': session_data['sessions']})

def shutdown_pc():
    end_session()
    if os.name == 'nt':
        os.system('shutdown /s /t 1')
    else:
        os.system('shutdown -h now')

def reboot_pc():
    end_session()
    if os.name == 'nt':
        os.system('shutdown /r /t 1')
    else:
        os.system('reboot')

def sleep_pc():
    end_session()
    if os.name == 'nt':
        subprocess.call(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
    else:
        os.system('systemctl suspend')

def on_exit():
    end_session()

import atexit
atexit.register(on_exit)

if __name__ == '__main__':
    start_session()
    app.run(host='0.0.0.0', port=5000, debug=False)
