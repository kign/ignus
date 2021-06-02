import sys, os, os.path, logging
from flask import Flask, url_for, g
from inetlab.auth import synauth, synlogin

synauth.setup_endpoints('home', 'home')
synlogin.setup_partners(google_client_id=os.getenv('GOOGLE_CLIENT_ID'),
                        microsoft_client_id=os.getenv('MS_CLIENT_ID'),
                        microsoft_client_secret=os.getenv('MS_CLIENT_SECRET'))

from views import vmain
from lib.firestore_driver import Backend

app = Flask(__name__, template_folder='t', static_folder='static')
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'tGBMMn156JsJ07?+e9>u976O@4u<enBYaJotvC]Rpc>vKONJv5'
# This is to preserve order of keys in OrderedDict when passing through `tojson`
app.config['JSON_SORT_KEYS'] = False

# You might want to add your own serialization for Date, Decimal, datetime, etc.
# app.json_encoder = myEncoder

# Add globals to be available in HTML templates, under namespace 'lib', e.g. 'lib.is_dev'
# See GAE environment variables here: https://cloud.google.com/appengine/docs/standard/python3/runtime
app.add_template_global({
    # TODO: add real function
    'is_dev' : lambda: not os.getenv('GAE_ENV', '').startswith('standard'),
    'create_logout_url' : (lambda: url_for('logout')),
        }, name='lib')

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

app.add_url_rule('/', 'home', view_func=vmain.home, methods=['GET'])
app.add_url_rule('/<string:shid>', 'redirect', view_func=vmain.shid_redirect, methods=['GET'])
app.add_url_rule('/u/about', 'about', view_func=vmain.about, methods=['GET'])
app.add_url_rule('/ajax/verify_shid', 'ajax_verify_shid', view_func=vmain.ajax_verify_shid, methods=['GET'])
app.add_url_rule('/ajax/url_add', 'ajax_url_add', view_func=vmain.ajax_url_add, methods=['POST'])
app.add_url_rule('/ajax/update_expire', 'ajax_update_expire', view_func=vmain.ajax_update_expire, methods=['POST'])
app.add_url_rule('/url/<string:shid>', 'shid_view', view_func=vmain.shid_view, methods=['GET'])
app.add_url_rule('/p/remove', 'shid_remove', view_func=vmain.shid_remove, methods=['POST'])

app.add_url_rule('/u/auth', 'authorized', view_func=synauth.authorized, methods=['GET'])
app.add_url_rule('/u/token', 'token', view_func=synauth.token, methods=['POST'])
app.add_url_rule('/u/logout', 'logout', view_func=synauth.logout, methods=['GET'])

with open('secrets/priv.txt') as fh :
    if app.config['DEBUG'] :
        print(f"Reading %r" % 'secrets/priv.txt')
    priv_users = fh.read().splitlines()

@app.before_request
def create_session():
    g.db = Backend ()
    g.priv_users = priv_users
    g.maintenance = False
    g.is_dev = not os.getenv('GAE_ENV', '').startswith('standard')

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    pass


if __name__ == "__main__":
    import argparse
    from inetlab.cli.colorterm import add_coloring_to_emit_ansi
    from inetlab.gae.dbgyamlenv import set_env_from_yaml

    default_log_level = "debug"
    default_port = 8081

    parser = argparse.ArgumentParser(description="Run app via system Python")
    parser.add_argument('--log', '--log_level', dest='log_level',
                        help="Logging level (default = %s)" % default_log_level,
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        default=default_log_level)
    parser.add_argument('-p', '--port', type=int, default=default_port, help="Port (default = %s)" % default_port)

    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d %(message)s",
                        level=getattr(logging, args.log_level.upper(), None),
                        datefmt='%H:%M:%S')
    logging.StreamHandler.emit = add_coloring_to_emit_ansi(logging.StreamHandler.emit)

    set_env_from_yaml ("app.yaml")

    logging.info("Starting in CLI debug mode")
    app.run(host='0.0.0.0', debug=True, port=args.port)
