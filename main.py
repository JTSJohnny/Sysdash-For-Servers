from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sql_tweaks import setup_db
import subprocess
import os
from maketunnel import create_tunnel, delete_tunnel

db = setup_db("services.db")

db.execute(
    "CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY, name TEXT UNIQUE, status TEXT)"
)

db.execute(
    """CREATE TABLE IF NOT EXISTS apps (
        id INTEGER PRIMARY KEY, 
        name TEXT,
        sv_name TEXT,
        sv_status TEXT,
        filepath TEXT,
        port INTEGER,
        domain TEXT,
        FOREIGN KEY (sv_name) REFERENCES services(name)
    )"""
)

db.execute(
    "CREATE TABLE IF NOT EXISTS cftnl (id INTEGER PRIMARY KEY, name TEXT, cfgstring TEXT)"
)

db.commit()


def get_services():
    services = db.execute("SELECT * FROM services").fetchall()
    for service in services:
        result = subprocess.run(
            ["systemctl", "is-active", service["name"]], capture_output=True, text=True
        )
        service["status"] = result.stdout.strip()
        db.execute(
            "UPDATE apps SET sv_status = ? WHERE sv_name = ?",
            (service["status"], service["name"]),
        )
    db.commit()
    print("Services", services)
    return services


def get_apps():
    apps = db.execute("SELECT * FROM apps").fetchall()
    print("Apps", apps)
    return apps


app = FastAPI(docs_url=None, redoc_url="/docs", title="API For SysDash")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SYSTEMD_DIR = "/etc/systemd/system"


def create_unit_file(name: str, filepath: str, start_cmd: str, port: int):
    if not start_cmd.strip().startswith(("/bin/bash", "bash", "/bin/sh", "sh")):
        escaped_cmd = start_cmd.replace("'", "'\\''")
        start_cmd = f"/bin/bash -c '{escaped_cmd}'"

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


@app.get("/")
async def dash(request: Request):
    get_services()
    return templates.TemplateResponse(request, "dash.html", {"apps": get_apps()})


@app.get("/serv_restart/{name}")
async def serv_restart(name: str):
    app_row = db.execute("SELECT sv_name FROM apps WHERE name = ?", (name,)).fetchone()
    subprocess.run(["systemctl", "restart", app_row["sv_name"]])
    return RedirectResponse(url="/")


@app.get("/serv_stop/{name}")
async def serv_stop(name: str):
    app_row = db.execute("SELECT sv_name FROM apps WHERE name = ?", (name,)).fetchone()
    subprocess.run(["systemctl", "stop", app_row["sv_name"]])
    return RedirectResponse(url="/")


@app.get("/serv_start/{name}")
async def serv_start(name: str):
    app_row = db.execute("SELECT sv_name FROM apps WHERE name = ?", (name,)).fetchone()
    subprocess.run(["systemctl", "start", app_row["sv_name"]])
    return RedirectResponse(url="/")


@app.get("/serv_delete/{name}")
async def serv_delete(name: str):
    app_row = db.execute("SELECT * FROM apps WHERE name = ?", (name,)).fetchone()
    if not app_row:
        return RedirectResponse(url="/")

    sv_name = app_row["sv_name"]
    domain = app_row["domain"]

    # Stop and disable systemd service
    subprocess.run(["systemctl", "stop", sv_name])
    subprocess.run(["systemctl", "disable", sv_name])

    # Remove unit file
    unit_path = os.path.join(SYSTEMD_DIR, f"{sv_name}.service")
    if os.path.exists(unit_path):
        os.remove(unit_path)
    subprocess.run(["systemctl", "daemon-reload"])

    # Delete tunnel
    delete_tunnel(sv_name, domain)

    # Delete from DB
    db.execute("DELETE FROM apps WHERE name = ?", (name,))
    db.execute("DELETE FROM services WHERE name = ?", (sv_name,))
    db.commit()

    return RedirectResponse(url="/")


@app.post("/flow/steps/1/")
async def flow_step_1(name: str, port: int, domain: str):
    create_tunnel(name, port, domain)
    return RedirectResponse(url="/flow/steps/2/")


@app.get("/flow/steps/2/")
async def flow_step_2(request: Request):
    return templates.TemplateResponse(request, "flow/steps/2.html")


@app.get("/add_app")
async def add_app_page(request: Request):
    return templates.TemplateResponse(request, "add_app.html", {})


@app.post("/add_app")
async def add_app_post(
    name: str = Form(...),
    sv_name: str = Form(...),
    filepath: str = Form(...),
    port: int = Form(...),
    domain: str = Form(...),
    start_cmd: str = Form(...),
):
    add_app(name, sv_name, filepath, port, domain, start_cmd)
    return RedirectResponse(url="/", status_code=303)
