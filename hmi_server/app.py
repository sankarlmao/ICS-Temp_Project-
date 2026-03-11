from flask import Flask, render_template, request, redirect, url_for, session
import requests
import os

app = Flask(__name__)
app.secret_key = 'super_secret_hmi_key'
SCADA_URL = 'http://scada-server:8080'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Vulnerable to SQLi concept or just hardcoded
        if username == 'admin' and password == 'admin123' or "' OR 1=1" in username:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid Credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        r = requests.get(SCADA_URL + '/')
        status = r.json().get('status', 'UNKNOWN')
    except:
        status = 'OFFLINE'
    return render_template('dashboard.html', status=status)

@app.route('/action/<cmd>')
def action(cmd):
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        if cmd == 'turn_off':
            requests.get(SCADA_URL + '/turn_off_power')
        elif cmd == 'wipe':
            requests.get(SCADA_URL + '/wipe_system')
    except:
        pass
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
