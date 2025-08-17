#!/bin/bash

# Create traefik directory if it doesn't exist
mkdir -p traefik

# Create empty acme.json file with correct permissions
touch traefik/acme.json
chmod 600 traefik/acme.json

echo "ACME JSON file created with proper permissions"
