# Deployment Guide for Personal Voice Assistant API

This guide explains how to deploy the Personal Voice Assistant API with SSL support using Docker and Traefik.

## Prerequisites

- Docker and Docker Compose installed on your server
- Domain name pointing to your server (api.deliverycouple.com)
- Open ports 80 and 443 on your server firewall

## Deployment Steps

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd personal-voice-assistant
```

### 2. Configure Environment Variables

Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file and fill in your configuration values.

### 3. Configure Traefik

Edit the `traefik/traefik.yml` file and replace `your-email@example.com` with your actual email address for Let's Encrypt notifications.

### 4. Initialize ACME JSON File

Run the initialization script to create the ACME JSON file with proper permissions:

```bash
chmod +x init-acme.sh
./init-acme.sh
```

### 5. Build and Start the Services

```bash
docker-compose up -d
```

This command will:
- Build the FastAPI application Docker image
- Start the Traefik reverse proxy
- Configure SSL certificates automatically via Let's Encrypt

### 6. Verify Deployment

- API should be accessible at: https://api.deliverycouple.com/
- Traefik dashboard (if enabled) at: http://your-server-ip:8080/

## Troubleshooting

### SSL Certificate Issues

If Let's Encrypt fails to issue certificates:

1. Check that ports 80 and 443 are open and accessible
2. Verify that your domain points to the correct IP address
3. Check Traefik logs: `docker-compose logs traefik`

### API Connection Issues

If the API is not accessible:

1. Check FastAPI logs: `docker-compose logs api`
2. Verify the API container is running: `docker-compose ps`

## Maintenance

### Updating the Application

To update the application:

```bash
git pull
docker-compose down
docker-compose up -d --build
```

### SSL Certificate Renewal

Let's Encrypt certificates are automatically renewed by Traefik when they approach expiration.
