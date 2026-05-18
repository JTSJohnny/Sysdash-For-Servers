import os
import subprocess

SYSTEMD_DIR = "/etc/systemd/system"


def create_unit_file(name: str, filepath: str, start_cmd: str, port: int):
    unit = f"""[Unit]
Description={name}
After=network.target

[Service]
WorkingDirectory={filepath}
ExecStart={start_cmd}
Restart=always
RestartSec=5
Environment=PORT={port}

[Install]
WantedBy=multi-user.target
"""
    unit_path = os.path.join(SYSTEMD_DIR, f"{name}.service")

    with open(unit_path, "w") as f:
        f.write(unit)

    # Reload systemd, enable and start
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", name])
    subprocess.run(["systemctl", "start", name])


def add_app(
    name: str, sv_name: str, filepath: str, port: int, domain: str, start_cmd: str
):
    # Create systemd unit file
    create_unit_file(sv_name, filepath, start_cmd, port)

    # Create CF tunnel
    create_tunnel(sv_name, domain, port)

    # Add to DB
    db.execute("INSERT INTO services (name, status) VALUES (?, '')", (sv_name,))
    db.execute(
        "INSERT INTO apps (name, sv_name, sv_status, filepath, port, domain) VALUES (?, ?, '', ?, ?, ?)",
        (name, sv_name, filepath, port, domain),
    )
    db.commit()
