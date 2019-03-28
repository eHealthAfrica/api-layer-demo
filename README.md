## Authentication & Routing Demo

In order to reliably implement multitenancy in a variety of solutions with flexible configurations, we needed some common components. This repository demonstrates how Keycloak and Kong can be used to protect microservices in a MT environment, supporting an arbitrary number of tenants and services, with different combinations of services per tenant.

#### Contents
 - Component Diagram
 - User Flow Diagram
 - Walkthrough
 - Extending

### Components
![components](https://github.com/eHealthAfrica/api-layer-demo/blob/master/docs/component.png)

### User Flow
![userflow](https://github.com/eHealthAfrica/api-layer-demo/blob/master/docs/user-flow.png)


### Walkthrough

 - Add `aether.local` to your `/etc/hosts` file as an alias to localhost.
   -  (cookies don't like to use localhost, and we use them extensively)
 - Run `setup_auth.sh`
 - One complete, you can visit http://aether.local/keycloak/auth/
   - Administrative KC user is : `admin`:`password`
   - This user can modify all realms (dev, dev2, master) from the master realm.
 - Start the demo service by running: `docker-compose up -d demo-service`
 - Let kong serve the demo service to the realm dev by running `docker-compose run auth register_service dev demo`
 - Visit http://aether.local/dev/demo/public/my-page to access an unprotected page
 - Visit http://aether.local/dev/demo/protected/user to access a protected page
   - User `user`: `password`
   - See that `user` has only `roles': ['user']`
 - Visit http://aether.local/dev/demo/protected/admin to access another protected page
   - Notice that the service returns a 401: `{"error": "user lacks one any of the following roles: ['admin']"}`
 - Logout from `user` by visiting: http://aether.local/dev/demo/logout
 - Log back in with credentials: `admin` : `password`
 - Visit http://aether.local/dev/demo/protected/admin to access another protected page
   - See that the admin has the proper credentials to view the page and no error occurs
 - Visit the demo service on realm dev2: http://aether.local/dev2/demo/
   - expect : `{"message":"no Route matched with those values"}`
 - Let kong serve the demo service to the realm dev2 by running `docker-compose run auth register_service dev2 demo`
 - Visit the demo service on realm dev2: http://aether.local/dev2/demo/
   - This realm also has a user `user` : `password`

You can then log in and out of the two realms, and be allowed or denied based on the policy. Changes made it the keycloak administrative interface (like giving `user` the role `admin`) will take up to 60 seconds for the services to pick up, based on the Kong-OIDC plugin caching policy.

### Extension

  - Realms are currently defined by json documents found in `/aether-auth/realm`
  - Available services are currently defined by json documents found in `/aether-auth/service`

Addind a valid artifact to either of those two and running setup will make it available. In the case of a service, you need to enable it by name for the realm in question using the `docker-compose run auth register_service {realm} {service}` command.

Any service you want to proxy must be available from inside docker at the url provided. I.E if you're trying to proxy something across docker-compose networks, take that into account.


   
 
