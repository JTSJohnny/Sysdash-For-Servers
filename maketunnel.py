import yaml
import subprocess
import os

CLOUDFLARED_CONFIG = os.path.expanduser("~/.cloudflared/config.yml")


def create_tunnel(name: str, hostname: str, port: int):
    # Create tunnel
    subprocess.run(["cloudflared", "tunnel", "create", name])

    # Create DNS CNAME record
    subprocess.run(["cloudflared", "tunnel", "route", "dns", name, hostname])

    # Update config.yml
    if os.path.exists(CLOUDFLARED_CONFIG):
        with open(CLOUDFLARED_CONFIG, "r") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {"ingress": [{"service": "http_status:404"}]}

    if "ingress" not in config:
        config["ingress"] = [{"service": "http_status:404"}]

    config["ingress"].insert(
        -1, {"hostname": hostname, "service": f"http://localhost:{port}"}
    )

    with open(CLOUDFLARED_CONFIG, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Restart cloudflared to pick up new config
    subprocess.run(["systemctl", "restart", "cloudflared"])


def delete_tunnel(name: str, hostname: str):
    subprocess.run(["cloudflared", "tunnel", "delete", "-f", name])

    if os.path.exists(CLOUDFLARED_CONFIG):
        with open(CLOUDFLARED_CONFIG, "r") as f:
            config = yaml.safe_load(f) or {}
            
        if "ingress" in config:
            config["ingress"] = [i for i in config["ingress"] if i.get("hostname") != hostname]
            with open(CLOUDFLARED_CONFIG, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
                
    subprocess.run(["systemctl", "restart", "cloudflared"])
