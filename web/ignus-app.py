import sys, os, os.path, logging
from flask import Flask, url_for, g
from inetlab.auth import synauth
from google.cloud import firestore

from views import home

app = Flask(__name__, template_folder='t', static_folder='static')
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'tGBMMn156JsJ07?+e9>u976O@4u<enBYaJotvC]Rpc>vKONJv5'
# This is to preserve order of keys in OrderedDict when passing through `tojson`
app.config['JSON_SORT_KEYS'] = False

# You might want to add your own serialization for Date, Decimal, datetime, etc.
# app.json_encoder = myEncoder

# Add globals to be available in HTML templates, under namespace 'lib', e.g. 'lib.is_dev'
app.add_template_global({
    # TODO: add real function
    'is_dev' : lambda: True,
    'create_logout_url' : (lambda: url_for('logout')),
        }, name='lib')

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

app.add_url_rule('/', 'home', view_func=home.main, methods=['GET'])

app.add_url_rule('/auth', 'authorized', view_func=synauth.authorized, methods=['GET'])
app.add_url_rule('/token', 'token', view_func=synauth.token, methods=['POST'])
app.add_url_rule('/logout', 'logout', view_func=synauth.logout, methods=['GET'])


@app.before_request
def create_session():
    g.db = firestore.Client()

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
