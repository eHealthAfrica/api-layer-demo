#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import requests
import sys

from keycloak import KeycloakAdmin

from settings import (
    KONG_URL,
    KC_URL,
    KC_ADMIN_USER,
    KC_ADMIN_PASSWORD,
    KC_MASTER_REALM,
    KEYCLOAK_URL
)


def __post(url, data):
    res = requests.post(url, data=data)
    try:
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(data)
        print(res.status_code)
        print(res.json())
        raise e


def add_realm(realm, name, url):

    keycloak_admin = KeycloakAdmin(server_url=KC_URL,
                                   username=KC_ADMIN_USER,
                                   password=KC_ADMIN_PASSWORD,
                                   realm_name=KC_MASTER_REALM,
                                   verify=False)

    token = keycloak_admin.token['access_token']
    headers = {
        'content-type': 'application/json',
        'authorization': f'Bearer {token}',
    }

    client_id = f'{realm}-oidc'
    client_secret_url = f'{KC_URL}admin/realms/{realm}/clients/{client_id}/client-secret'
    res = requests.get(url=client_secret_url, headers=headers)
    try:
        res.raise_for_status()
        client_secret = res.json()['value']
        print(res.text)
    except Exception:
        raise ValueError('Could not get realm secret.')

    ROUTE_URL = f'{KONG_URL}/services/{name}/routes'
    data = {
        'paths': [f'/{realm}/{name}/*'],
        'strip_path': 'true',
    }
    route_info = __post(url=ROUTE_URL, data=data)
    protected_route_id = route_info['id']

    # TODO add OIDC plugin to realm
    auth_path = f'{KEYCLOAK_URL}realms/{realm}/protocol/openid-connect/auth'
    token_path = f'{KEYCLOAK_URL}realms/{realm}/protocol/openid-connect/token'
    user_path = f'{KEYCLOAK_URL}realms/{realm}/protocol/openid-connect/userinfo'
    logout_url = f'{KEYCLOAK_URL}realms/{realm}/protocol/openid-connect/logout'

    data = {
        'name': 'kong-oidc-auth',
        'config.authorize_url': auth_path,
        'config.scope': 'openid+profile+email+iss',
        'config.token_url': token_path,
        'config.client_id': f'{realm}-oidc',
        'config.client_secret': client_secret,
        'config.user_url': user_path,
        'config.email_key': 'email',
        'config.app_login_redirect_url': f'http://aether.local/{realm}/{name}/',
        'config.service_logout_url': logout_url,
        'config.cookie_domain': 'aether.local',
        'config.user_info_cache_enabled': 'true'
    }

    confirmation = __post(url=f'{KONG_URL}/routes/{protected_route_id}/plugins', data=data)
    print(json.dumps(confirmation, indent=2))

    PUBLIC_ROUTE_URL = f'{KONG_URL}/services/{name}-public/routes'
    data = {
        'paths': [f'/{realm}/{name}/public'],
        'strip_path': 'true',
    }
    __post(url=PUBLIC_ROUTE_URL, data=data)


def register_app(realm, name, url):
    # Register Client with Kong
    # Single API Service
    data = {
        'name': f'{name}',
        'url': f'{url}'
    }
    client_info = __post(url=f'{KONG_URL}/services/', data=data)
    client_id = client_info['id']

    data = {
        'name': f'{name}-public',
        'url': f'{url}/public'
    }
    __post(url=f'{KONG_URL}/services/', data=data)

    return client_id


if __name__ == '__main__':
    REALM_NAME = sys.argv[1]
    CLIENT_NAME = sys.argv[2]
    CLIENT_URL = sys.argv[3]

    print(f'Exposing Service {CLIENT_NAME} @ {CLIENT_URL} for realm {REALM_NAME}')
    try:
        register_app(REALM_NAME, CLIENT_NAME, CLIENT_URL)
    except Exception as err:
        print(f'could not register app: {err}')
    add_realm(REALM_NAME, CLIENT_NAME, CLIENT_URL)
    print(f'Service {CLIENT_NAME} from {CLIENT_URL} now being served by kong @ /{CLIENT_NAME}.')
