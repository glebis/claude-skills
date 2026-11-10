#!/bin/sh
# Runs the browser flow against a server already listening on 4174, or on PORT.
# SHOTS sets where screenshots go. Local proxies are bypassed for 127.0.0.1.
unset HTTP_PROXY http_proxy HTTPS_PROXY https_proxy
NODE_PATH="$(npm root -g)" SHOTS="${SHOTS:-.}" exec node "$(dirname "$0")/flow.cjs"
