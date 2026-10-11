# Deployment Guide: DigitalOcean

This document outlines how to deploy Inevitable to DigitalOcean. 

**IMPORTANT**: Inevitable executes repository code. Deploying this application to a public endpoint without strict execution isolation (e.g., cgroups, seccomp, rootless containers) is extremely dangerous. For public demonstrations, we strongly enforce `demo:local-fixture` as the only executable environment.

## 1. Prerequisites
- A DigitalOcean account.
- DigitalOcean App Platform or a Droplet.
- A free `TOGETHER_API_KEY` for Gemma 4 if you are using AI, or `mock` if you just want to run the fixture end-to-end.

---

## Option A: DigitalOcean App Platform (Recommended)

App Platform is the simplest, most secure way to deploy as it manages TLS, builds, and routing natively. 

**Expected Cost:** ~$10 - $20/month depending on instance size (minimum 1GB RAM recommended for Pytest execution).

1. Ensure your Inevitable repository is pushed to a GitHub or GitLab account.
2. In the DigitalOcean Console, go to **Apps** -> **Create App**.
3. Select your repository.
4. App Platform will detect the Dockerfiles. You should set up two components:
   - **Backend** (Web Service):
     - Source: `/backend`
     - Environment Variables:
       - `BACKEND_HOST`: `0.0.0.0`
       - `BACKEND_PORT`: `8080` (ensure this matches the exposed port)
       - `GEMMA_PROVIDER`: `together`
       - `TOGETHER_API_KEY`: `<your-key>`
       - `ENABLE_UNTRUSTED_EXECUTION`: `false` (CRITICAL for safety)
   - **Frontend** (Static Site or Web Service):
     - Source: `/frontend`
     - Environment Variables:
       - `VITE_API_URL`: `<URL of your deployed backend component>`
5. Deploy the app. The health check (`/health`) will automatically confirm the backend is up.

---

## Option B: Docker Compose on a Droplet

If you prefer maximum control or want to isolate the execution engine deeply into a sandbox on a raw VM.

**Expected Cost:** ~$6/month for a basic 1GB droplet.

1. Provision a DigitalOcean Droplet (Ubuntu 24.04).
2. SSH into the Droplet and install Docker and Docker Compose.
3. Clone your repository.
4. Create a `.env` file in the root based on `.env.example`:
   ```bash
   GEMMA_PROVIDER=together
   TOGETHER_API_KEY=your_key_here
   ```
5. Run the deployment:
   ```bash
   docker compose up -d --build
   ```
6. **Reverse Proxy & SSL**: You must configure NGINX and Let's Encrypt (`certbot`) to proxy port `8000` (backend) and `5173` (frontend) to public domains to avoid mixed-content SSL errors in modern browsers.

## 2. Resource Requirements & Limitations

- **Memory**: The backend requires at least 512MB RAM to clone Git repositories and spawn `pytest` processes in memory. 1GB is recommended.
- **CPU**: Repository cloning and AST parsing are CPU-bound. Basic droplets are sufficient for the `demo_repo` but may timeout on massive enterprise monorepos.
- **Storage**: The backend cleans up `tempfile` directories strictly per-request, meaning disk footprint is completely transient and negligible.

## 3. Demo Mode

If you deploy publicly, leave `ENABLE_UNTRUSTED_EXECUTION=false`. When evaluating the app, type `demo:local-fixture` in the frontend Repository URL input. The backend will automatically map this to the verified, sandboxed fixture that comes pre-packaged with the Docker container, fully demonstrating the end-to-end Gemma 4 pipeline without executing untrusted code on your infrastructure.
