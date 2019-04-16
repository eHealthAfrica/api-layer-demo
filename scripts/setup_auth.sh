#!/usr/bin/env bash
#
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
#
set -Eeuo pipefail

source ./scripts/aether_functions.sh

echo ""
echo "========================================================================="
echo "    Initializing Gateway environment, this will take about 60 seconds."
echo "========================================================================="
echo ""

docker-compose kill
create_docker_assets
source .env


DC_AUTH="docker-compose -f docker-compose.yml"
AUTH_CMD="$DC_AUTH run --rm auth"

function connect_to_keycloak {
    n=0
    until [ $n -ge 10 ]
    do
        $AUTH_CMD keycloak_ready && break
        echo "waiting for keycloak..."        
        sleep 3
    done
}

LINE="__________________________________________________________________"

echo "${LINE} Pulling docker images..."
docker-compose pull db
echo ""

docker-compose up -d db

# Initialize the kong & keycloak databases in the postgres instance

# THESE COMMANDS WILL ERASE PREVIOUS DATA!!!
rebuild_database kong     kong     ${KONG_PG_PASSWORD}
rebuild_database keycloak keycloak ${KEYCLOAK_PG_PASSWORD}
echo ""

echo "${LINE} Building custom docker images..."
docker-compose build --no-cache --force-rm --pull keycloak kong
$DC_AUTH       build --no-cache --force-rm --pull auth
echo ""


echo "${LINE} Preparing kong..."
#
# https://docs.konghq.com/install/docker/
#
# Note for Kong < 0.15: with Kong versions below 0.15 (up to 0.14),
# use the up sub-command instead of bootstrap.
# Also note that with Kong < 0.15, migrations should never be run concurrently;
# only one Kong node should be performing migrations at a time.
# This limitation is lifted for Kong 0.15, 1.0, and above.
docker-compose run kong kong migrations bootstrap 2>/dev/null || true
docker-compose run kong kong migrations up
echo ""
start_kong


echo "${LINE} Registering keycloak and minio in kong..."
$AUTH_CMD setup_auth
echo ""


echo "${LINE} Preparing keycloak..."
start_keycloak
connect_to_keycloak

echo "${LINE} Creating initial realms in keycloak..."
REALMS=( dev prod )
for REALM in "${REALMS[@]}"; do
    $AUTH_CMD add_realm         $REALM
    $AUTH_CMD add_oidc_client   $REALM
    $AUTH_CMD add_user          $REALM \
                                $KEYCLOAK_INITIAL_USER_USERNAME \
                                $KEYCLOAK_INITIAL_USER_PASSWORD            
    # create_kc_realm          $REALM
    # create_kc_kong_client    $REALM

    # create_kc_user  $REALM \
    #                 $KEYCLOAK_INITIAL_USER_USERNAME \
    #                 $KEYCLOAK_INITIAL_USER_PASSWORD

    echo "${LINE} Adding [demo] solution in kong..."
    $AUTH_CMD add_solution demo $REALM
done
echo ""

$DC_AUTH down
docker-compose kill
docker-compose down

echo ""
echo "========================================================================="
echo "                                 Done!"
echo "========================================================================="
echo ""
