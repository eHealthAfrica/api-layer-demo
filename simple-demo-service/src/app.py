from flask import Flask, render_template
import logging

from settings import APP_PORT
from auth import get_realm, require_role

app = Flask(__name__, template_folder='../templates')

try:
    handler = app.logger.handlers[0]
except IndexError:
    handler = logging.StreamHandler()
finally:
    handler.setFormatter(logging.Formatter('%(asctime)s [APP1] %(levelname)-8s %(message)s'))
    app.logger.addHandler(handler)
    log_level = logging.getLevelName('DEBUG')
    app.logger.setLevel(log_level)

# PUBLIC
# Whitelisted by KONG, no token/ realm will be available
@app.route(f"/public/")
@app.route(f"/public/<page>")
def public_route(page=None):
    content = {'success': f'this page {page or "/"} is public and not protected by KONG'}
    return render_template('./json.html', content=content)

# PROTECTED
# Requires token auth in KONG, or API gateway serves a 401
# If a valid token is presented, this page is served and we can inspect it

# User Route
# user group should be in the token // app handles this matching


@app.route(f"/")
@app.route(f"/protected/")
@app.route(f"/protected/user")
@require_role(['user', 'admin'])
@get_realm
def user_routes(realm, roles):
    content = {'realm': realm, 'roles': roles}
    return render_template('./json.html', content=content)

# Admin Route
# admin group should be in the token // app handles this matching


@app.route(f"/protected/admin")
@require_role(['admin'])
@get_realm
def admin_routes(realm, roles):
    content = {'realm': realm, 'roles': roles}
    return render_template('./json.html', content=content)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT)
