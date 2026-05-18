# SysDash

SysDash is an automated, personal server management dashboard. It simplifies the process of deploying local web applications to the public internet by automatically handling `systemd` daemon creation and `cloudflared` tunnel routing.
<img width="1910" height="999" alt="Dashboard" src="https://github.com/user-attachments/assets/2943a39b-8a1f-4ce3-b014-ce62c4cede39" />

## Features

- **Automated Deployments:** Convert any local application into a persistent background service using `systemd`.
- **Public Routing:** Instantly expose your applications to the internet with secure `cloudflared` tunnels.
- **Easy Management:** A clean, intuitive dashboard to Start, Stop, Restart, and Delete applications with a single click.
- **Zero Boilerplate:** No need to manually write `.service` files or YAML configuration for Cloudflare.

## Prerequisites

SysDash relies on your system's underlying tools. Ensure the following are installed:

### 1. `systemd`
Standard on most Linux distributions. You cannot install this, you must use an OS that supports it.

### 2. `uv` (Python Package Manager)
Install `uv` using the official script:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. `cloudflared` (Cloudflare Tunnel)
Download the daemon and authenticate it with your Cloudflare account:
```bash
# Download and install (Ubuntu/Debian example)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Authenticate with your Cloudflare account (this will open a browser link)
cloudflared tunnel login
```

## Installation & Running

Because SysDash needs to create systemd unit files in `/etc/systemd/system/` and manage system services, **it must be run as root**.

```bash
# Example command to start the server as root
sudo uv run uvicorn main:app --port=5001
```

Once running, access the dashboard at:
`http://localhost:5001`

## Usage

### 1. Dashboard
The main dashboard (`/`) displays all tracked applications along with their active statuses (`active`, `failed`, or `inactive`). You can control the lifecycle of any app using the Action buttons.

### 2. Adding an App
To deploy a new application, click **Add App** and fill in the required fields:
- **App Display Name**: Friendly name for the dashboard.
- **Systemd Service Name**: The internal lowercase identifier (e.g., `my-app`).
- **Filepath**: The absolute path to your code directory.
- **Port**: The local port your application listens on.
- **Domain**: The public domain to route to this app.
- **Start Command**: The terminal command to launch your app. (SysDash automatically wraps this in `bash` for complex commands).

### 3. Deleting an App
Clicking **Delete** on the dashboard safely performs a complete cleanup:
- Stops and disables the systemd service.
- Deletes the unit file and reloads the system daemon.
- Deletes the Cloudflare tunnel and cleans the routing configuration.
- Removes the application from the SysDash database.

## Architecture & Stack
- **Backend:** Python / FastAPI
- **Database:** SQLite (local `services.db`)
- **Frontend:** HTML + Jinja2 Templates (No JS frameworks)
- **Styling:** Matcha.css
- **Infrastructure:** Systemd + Cloudflared
