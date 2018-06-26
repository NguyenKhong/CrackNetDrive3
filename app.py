from flask import Flask, render_template, redirect, url_for, \
                    request, send_from_directory, make_response, abort, send_file
from OpenSSL import SSL
import json
import random
import os
from _winreg import *
import subprocess
import argparse
import sys
import win32serviceutil
import threading
import time
import io
import shutil

app = Flask(__name__)

try:
    this_file = __file__
except NameError:
    this_file = sys.argv[0]


this_file = os.path.abspath(this_file)
CURRENT_DIR = os.path.dirname(this_file)
PATH_ITEMS = os.path.join(CURRENT_DIR, "json\\items.json")
PATH_PRODUCTS = os.path.join(CURRENT_DIR, "json\\products.json")

#build to executable
if getattr(sys, 'frozen', False):
    CURRENT_DIR = os.path.dirname(sys.executable)
    PATH_ITEMS = os.path.join(CURRENT_DIR, "json\\items.json")
    PATH_PRODUCTS = os.path.join(CURRENT_DIR, "json\\products.json")
    if not os.path.exists(PATH_ITEMS) and not os.path.exists(PATH_PRODUCTS):
        shutil.copytree(os.path.join(sys._MEIPASS, 'json'), os.path.join(CURRENT_DIR, 'json'))


@app.route("/")
def index():
    return redirect("/accounts/login/?next=/", code = 302)

@app.route('/<path:path>')
def proxy(path):
    #return "\n", 101
    abort(404)


@app.route("/accounts/login/", methods=['GET',])
def login():
    return 'OK'

@app.route('/api/v1/rest-auth/login/', methods=['POST'])
def auth_login():
    payload = '{"code": 0, "token": "9d1253d4acb57cb90d58b12b342967f7b2c0a2bf", "url": null}'
    resp = make_response(payload)
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route("/api/v1/me/products/")
def products():    
    resp = make_response(send_file(PATH_PRODUCTS))
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Set-Cookie'] = 'sessionid=nrbw43idxks9hfkqpsp0nwlpzbdlqi7p; expires=Wed, 06-Jun-2518 19:31:03 GMT; HttpOnly; Max-Age=1209600; Path=/'
    resp.headers['X-Bdrive-Session-Key'] = 'd90ab0a3b35a4d59bba2f0cfed1de192'
    return resp

@app.route("/api/v1/NetDrive3/items/", methods=["POST"])
def add_item():
    dataNew = request.get_json()
    dataNew['id'] = random.randint(1, 999999)
    with open(PATH_ITEMS, 'r+') as f:
        database = json.load(f)
        database['count'] += 1
        database['results'].append(dataNew)
        f.seek(0)
        f.truncate()
        json.dump(database, f)
    resp = make_response(json.dumps(dataNew))
    resp.headers['X-Bdrive-Session-Key'] = 'd90ab0a3b35a4d59bba2f0cfed1de192'
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route("/api/v1/NetDrive3/items/", methods=["GET"])
def get_item():
    if not os.path.exists(PATH_ITEMS): 
        with open(PATH_ITEMS, 'w') as f:
            f.write('{"count": 0, "previous": null, "results": [], "next": null}')
    resp = make_response(send_file(PATH_ITEMS))
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Set-Cookie'] = 'sessionid=nrbw43idxks9hfkqpsp0nwlpzbdlqi7p; expires=Wed, 06-Jun-2518 19:31:03 GMT; HttpOnly; Max-Age=1209600; Path=/'
    resp.headers['X-Bdrive-Session-Key'] = 'd90ab0a3b35a4d59bba2f0cfed1de192'
    return resp

@app.route("/api/v1/NetDrive3/items/<int:item_id>/", methods=['PATCH', 'DELETE'])
def items(item_id):
    item_id = int(item_id)
    if request.method == "PATCH":
        dataUpdate = request.get_json()
        dataUpdate['id'] = item_id
        with open(PATH_ITEMS, 'r+') as f:
            database = json.load(f)
            for i in xrange(len(database['results'])):
                if database['results'][i]['id'] == item_id:
                    database['results'][i] = dataUpdate
                    break
            f.seek(0)
            f.truncate()
            json.dump(database, f)

        resp = make_response(json.dumps(dataUpdate))
        resp.headers['X-Bdrive-Session-Key'] = 'd90ab0a3b35a4d59bba2f0cfed1de192'
        resp.headers['Content-Type'] = 'application/json'
        return resp

    if request.method == "DELETE":
        with open(PATH_ITEMS, 'r+') as f:
            database = json.load(f)
            for i in xrange(len(database['results'])):
                if database['results'][i]['id'] == item_id:
                    del database['results'][i]
                    database['count'] -= 1
                    break
            f.seek(0)
            f.truncate()
            json.dump(database, f)
            
        resp = make_response()
        resp.headers['X-Bdrive-Session-Key'] = 'd90ab0a3b35a4d59bba2f0cfed1de192'
        resp.headers['Set-Cookie'] = 'sessionid=nrbw43idxks9hfkqpsp0nwlpzbdlqi7p; expires=Wed, 06-Jun-2518 19:31:03 GMT; HttpOnly; Max-Age=1209600; Path=/'
        return resp, 204

@app.route('/api/v1/sso_guard/')
def sso_guard():
    payload = '{"guard":"MTUyNzUyODA3LTI3Ljc0LjI1NS4yNDE=","encoding":"sha3-256","format":"token-guard"}'
    resp = make_response(payload)
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Set-Cookie'] = 'sessionid=nrbw43idxks9hfkqpsp0nwlpzbdlqi7p; expires=Wed, 06-Jun-2518 19:31:03 GMT; HttpOnly; Max-Age=1209600; Path=/'
    return resp

def crackNetDrive():
    try:
        os.system('taskkill /f /im ndagent.exe')
        os.system('taskkill /f /im nd3svc.exe')
        os.system('taskkill /f /im NetDrive.exe')
        os.system('taskkill /f /im ndmnt.exe')

        key = OpenKey(HKEY_LOCAL_MACHINE, r'SOFTWARE\Bdrive Inc\NetDrive3')
        DirNetDrive = QueryValue(key, 'Path')
        shutil.copy2(os.path.join(DirNetDrive, 'NetDrive.exe'), os.path.join(DirNetDrive, 'NetDrive.exe.bak'))
        shutil.copy2(os.path.join(DirNetDrive, 'ndagent.exe'), os.path.join(DirNetDrive, 'ndagent.exe.bak'))
        with open(os.path.join(DirNetDrive, 'NetDrive.exe'), 'rb+') as f:
            f.seek(0x1AF51C)
            f.write('://127.0.0.1:52221')

        with open(os.path.join(DirNetDrive, 'ndagent.exe'), 'rb+') as f:
            f.seek(0x103A70)
            f.write('://127.0.0.1:52221')
        
        pathFileHosts = os.path.join(os.environ['windir'], r'System32\drivers\etc\hosts')
        if not os.path.exists(pathFileHosts):
            with open(pathFileHosts, "a+") as f:
                f.write('127.0.0.1 localhost\r\n')

        with open(pathFileHosts, "a+") as f:
            f.write('\r\n127.0.0.1 push.bdrive.com\r\n')
        os.system('gpupdate /force')
        

    except Exception as e:
        print ("Crack failed - %s" % e)
        return

    print "Crack OK"
    try:
        win32serviceutil.StartService('NetDrive3_Service_x64_NetDrive3')
    except:
        win32serviceutil.StartService('NetDrive3_Service_NetDrive3')
    win32serviceutil.StartService('NetDrive3 Agent')
    subprocess.Popen([os.path.join(DirNetDrive, 'NetDrive.exe'),], cwd = DirNetDrive)

def startNetDrive3():
    time.sleep(5)
    try:
        win32serviceutil.StartService('NetDrive3_Service_x64_NetDrive3')
    except:
        win32serviceutil.StartService('NetDrive3_Service_NetDrive3')
    win32serviceutil.StartService('NetDrive3 Agent')
    key = OpenKey(HKEY_LOCAL_MACHINE, r'SOFTWARE\Bdrive Inc\NetDrive3')
    DirNetDrive = QueryValue(key, 'Path')
    subprocess.Popen([os.path.join(DirNetDrive, 'NetDrive.exe'),], cwd = DirNetDrive)

def runServer():
    os.system('taskkill /f /im ndagent.exe')
    os.system('taskkill /f /im nd3svc.exe')
    os.system('taskkill /f /im NetDrive.exe')
    os.system('taskkill /f /im ndmnt.exe')
    thread = threading.Thread(target = startNetDrive3)
    thread.setDaemon(True)
    thread.start()
    app.run(threaded = True, debug = False, port = 52221, host = '127.0.0.1')#, ssl_context=(PATH_CERT, PATH_KEY))

    

def RunAtStartup():
    try:
        key = OpenKey(HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, KEY_WRITE)
        SetValueEx(key, 'AutoServerNetDrive3', 0, REG_SZ, sys.executable)
        CloseKey(key)
        return True
    except WindowsError:
        return False


def RemoveRunAtStartup():
    try:
        key = OpenKey(HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, KEY_WRITE)
        DeleteValue(key, 'AutoServerNetDrive3')
        CloseKey(key)
        return True
    except WindowsError:
        return False

def main():
    description = """\
Please enter -a or --auto to crack NetDrive3

If no arguments, program will run the fake server\
    """
    parser = argparse.ArgumentParser(description = description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', '--auto', action = 'store_true', help = 'Auto crack NetDrive3')
    parser.add_argument('-s', '--startup', action = 'store_true', help = 'Run at startup')
    parser.add_argument('-r', '--remove', action = 'store_true', help = 'Remove run at startup')
    args = parser.parse_args()

    if args.auto:
        crackNetDrive()

    if args.startup:
        if RunAtStartup():
            print "StartUp OK"
            return
        print "StartUp Failed"
        return

    if args.remove:
        if RemoveRunAtStartup():
            print "Remove OK"
            return
        print "Remove Failed"
        return

    print "Please enter --help for infomation."
    runServer()

if __name__ == '__main__':
    main()