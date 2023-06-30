# -*- coding: utf-8 -*-
import logging
import os
import time
import traceback
from dotenv import load_dotenv
from flask import Flask, request, render_template
import urllib.request
import subprocess
import threading

app_start_time = int(time.time())

load_dotenv()

if os.name != 'nt':
    base_dir = os.path.dirname(os.path.realpath(__file__)).replace("/apps", "")
else:
    base_dir = os.path.dirname(os.path.realpath(__file__)).replace("\\apps", "")

app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

app.logger.info("App start time: {}".format(app_start_time))
app.logger.info("Base dir: {}".format(base_dir))


def dl_certificates(base_url: str, domain_name: str):
    cert_dir = os.path.join(base_dir, 'certs')
    domain_dir = os.path.join(cert_dir, domain_name)
    if not os.path.isdir(cert_dir):
        os.mkdir(cert_dir)
    if not os.path.isdir(domain_dir):
        os.mkdir(domain_dir)
    path_file_fullchain = os.path.join(domain_dir, "fullchain.pem")
    path_file_fullchain_temp = os.path.join(domain_dir, "fullchain.pem_temp")
    path_file_privkey = os.path.join(domain_dir, "privkey.pem")
    path_file_privkey_temp = os.path.join(domain_dir, "privkey.pem_temp")
    timestamp = int(time.time())
    is_ok = True
    try:
        urllib.request.urlretrieve("{}/fullchain.pem".format(base_url), path_file_fullchain_temp)
    except Exception:
        is_ok = False
        app.logger.error("Cannot download URL: {}, error:\n{}".format("{}/fullchain.pem".format(base_url), traceback.format_exc()))
    if is_ok:
        try:
            urllib.request.urlretrieve("{}/privkey.pem".format(base_url), path_file_privkey_temp)
        except Exception:
            is_ok = False
            app.logger.error("Cannot download URL: {}, error:\n{}".format("{}/privkey.pem".format(base_url), traceback.format_exc()))

    if is_ok:
        if os.path.isfile(path_file_fullchain):
            os.rename(path_file_fullchain, "{}_{}".format(path_file_fullchain, timestamp))
        if os.path.isfile(path_file_privkey):
            os.rename(path_file_privkey, "{}_{}".format(path_file_privkey, timestamp))
        os.rename(path_file_fullchain_temp, path_file_fullchain)
        os.rename(path_file_privkey_temp, path_file_privkey)

    return is_ok


def execute_renewal_scripts(hook_dir: str):
    items = os.listdir(hook_dir)

    def _run_background(file_path: str):
        th = threading.Thread(target=subprocess.Popen, args=([file_path],), daemon=True)
        th.start()

    for item in items:
        file_path = os.path.join(hook_dir, item)
        if item.split('.')[-1] in ('sh', 'bat') and os.path.isfile(file_path):
            app.logger.info("Run script: {}".format(file_path))
            _run_background(file_path)


@app.route('/')
def index():
    return render_template('index.html', menu='index')


@app.route('/certbot')
def webhook_certbot():
    domain = request.args.get('domain')
    token = request.headers.get('Authorization')
    if token != os.environ.get('APP_TOKEN'):
        return 'UNAUTHORIZED', 401
    path_renewal_hook = os.path.join(base_dir, "renewal_hooks")
    if not os.path.isdir(path_renewal_hook):
        os.mkdir(path_renewal_hook)
    if domain:
        if os.environ.get('CERTBOT_HOST'):
            is_ok = dl_certificates(os.environ.get('CERTBOT_HOST'), domain)
            if is_ok:
                execute_renewal_scripts(path_renewal_hook)
            return 'OK' if is_ok else 'FAILED', 200
        else:
            return 'MISSING_CONFIG', 200
    return 'BAD_REQUEST', 400


if __name__ == "__main__":
    debug = True if os.getenv('DEBUG') and os.getenv('DEBUG').lower() == 'true' else False
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 9000)), debug=debug)
