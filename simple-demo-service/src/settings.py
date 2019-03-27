import os


def get(name, default=None):
    return os.environ.get(name.upper(), default)


HOST = get('BASE_HOST', 'aether.local')
APP_NAME = get('APP_NAME', 'demo-service')
APP_PORT = int(get('APP_PORT', 3013))
JWT_COOKIE = get('JWT_COOKIE', 'aether-jwt')
REALM_COOKIE = get('REALM_COOKIE', 'aether-realm')
KONG_URL = get('KONG_INTERNAL')
KC_URL = get('KEYCLOAK_INTERNAL', 'http://keycloak:8080/')  # internal
KC_URL = f'{KC_URL}/keycloak/auth/'

KEYCLOAK_URL = f'{HOST}/keycloak/auth/'
KC_ADMIN_USER = 'admin'
KC_ADMIN_PASSWORD = 'password'
KC_MASTER_REALM = 'master'
