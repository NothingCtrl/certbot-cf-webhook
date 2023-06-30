# Certbot SSL WEBHOOK

This app work along with [`certbot-cf-wildcard`](https://github.com/NothingCtrl/certbot-cf-wildcard) project for remote 
trigger download certificates when it renew, a web-hook call will make this app process download 
certificates to `certs` folder. After download success, it will execute all files have extension `.sh` or `.bat` 
store in `renewal_hooks/` folder (example: script to reload nginx), all scripts must mark _executable_.

### How to

* Create `.env` file from template `.env_example`, notes:
    * `CERTBOT_HOST`: URL of `certbot-cf-wildcard` app to download certificate files
    * `APP_TOKEN`: this app token to allow remote trigger certificate download
    * `PORT`: Application listen port
* Optional: Create a `renewal_hooks` folder, add script(s) you need to execute when web-hook trigger
  * The script file must have extension `sh` or `bat`
  * On Linux, run `chmod +x` on script file to make it executable
* Setup app environment (only support `python 3.5+`):
    ```sh
    #!/bin/bash
    virtualenv venv
    source venv/bin/activate
    pip intall -r requirements.txt
    ```
* Start web server on port `9000`: 
    ```sh
    #!/bin/bash
    CURRENT=`pwd`
    PORT=9000
    source venv/bin/activate
    gunicorn --bind 0.0.0.0:$PORT wsgi:app
    ```
* On server run `certbot-cf-wildcard` app, add a script in `renewal_hooks` folder, example:
    ```sh
    #!/bin/bash
    /usr/bin/curl --retry 3 --connect-timeout 10 -A "certbot-cf-wildcard" -H "Authorization: just-me" http://this-server-ip:9000/certbot?domain=foo.bar
    ```
  