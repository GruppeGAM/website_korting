#!/usr/bin/env python3
"""
Deploy-Script: Löscht alte Dateien auf dem Server und lädt neue hoch.

Aufruf:
    python deploy.py staging   -> container.ga-cms.de (SSH-Key oder Passwort)
    python deploy.py prod      -> www.anwaelte-aalen.de (IONOS, Passwort)

Zugangsdaten (optional, sonst interaktive Passwortabfrage):
    DEPLOY_PASSWORD     SFTP-Passwort
    DEPLOY_KEY_FILE     Pfad zum privaten SSH-Key
    DEPLOY_KNOWN_HOSTS  Pfad zu einer known_hosts-Datei (Host-Key wird geprüft)
"""

import paramiko
import os
import sys
import getpass
import stat

LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

TARGETS = {
    "staging": {
        "host": "container.ga-cms.de",
        "user": "deploy",
        # Achtung: Inhalt dieses Ordners wird komplett ersetzt!
        "remote_dir": "/var/www/staging-korting",
        "keep": set(),
    },
    "prod": {
        "host": "home29819267.1and1-data.host",
        "user": "acc828869407",
        "remote_dir": ".",
        # Dateien/Ordner die NICHT gelöscht werden
        "keep": {".ssh", ".bash_history", ".htaccess", "logs"},
    },
}

# Lokale Dateien die hochgeladen werden
UPLOAD_FILES = ["index.html", "styles.css", "datenschutz.html", "impressum.html"]
UPLOAD_DIRS = ["images"]


def sftp_rm_recursive(sftp, remote_path):
    """Löscht einen Ordner rekursiv auf dem Server."""
    try:
        items = sftp.listdir_attr(remote_path)
    except Exception:
        return
    for item in items:
        item_path = remote_path + "/" + item.filename
        if stat.S_ISDIR(item.st_mode):
            # Schreibrechte sicherstellen
            try:
                sftp.chmod(item_path, 0o755)
            except Exception:
                pass
            sftp_rm_recursive(sftp, item_path)
            try:
                sftp.rmdir(item_path)
                print(f"  Ordner gelöscht: {item_path}")
            except Exception as e:
                print(f"  WARNUNG Ordner: {item_path} -> {e}")
        else:
            try:
                sftp.chmod(item_path, 0o644)
            except Exception:
                pass
            try:
                sftp.remove(item_path)
                print(f"  Datei gelöscht:  {item_path}")
            except Exception as e:
                print(f"  WARNUNG Datei: {item_path} -> {e}")


def sftp_upload_dir(sftp, local_path, remote_path):
    """Lädt einen lokalen Ordner rekursiv hoch."""
    try:
        sftp.mkdir(remote_path)
    except Exception:
        pass
    for item in os.listdir(local_path):
        local_item = os.path.join(local_path, item)
        remote_item = remote_path + "/" + item
        if os.path.isdir(local_item):
            sftp_upload_dir(sftp, local_item, remote_item)
        else:
            sftp.put(local_item, remote_item)
            print(f"  Hochgeladen: {remote_item}")


def check_host_key(transport, host):
    """Prüft den Host-Key gegen DEPLOY_KNOWN_HOSTS, falls gesetzt."""
    known_hosts = os.environ.get("DEPLOY_KNOWN_HOSTS")
    if not known_hosts:
        print("  HINWEIS: DEPLOY_KNOWN_HOSTS nicht gesetzt, Host-Key wird nicht geprüft.")
        return
    keys = paramiko.HostKeys(known_hosts)
    server_key = transport.get_remote_server_key()
    expected = keys.lookup(host)
    if not expected or expected.get(server_key.get_name()) != server_key:
        sys.exit(f"FEHLER: Host-Key von {host} stimmt nicht mit {known_hosts} überein!")


def connect(cfg):
    host, user = cfg["host"], cfg["user"]
    transport = paramiko.Transport((host, 22))
    transport.start_client()
    check_host_key(transport, host)

    key_file = os.environ.get("DEPLOY_KEY_FILE")
    if key_file:
        transport.auth_publickey(user, paramiko.Ed25519Key.from_private_key_file(key_file))
    else:
        password = os.environ.get("DEPLOY_PASSWORD") or getpass.getpass(
            f"SFTP-Passwort für {user}@{host}: "
        )
        transport.auth_password(user, password)
    return transport


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in TARGETS:
        sys.exit(f"Aufruf: python {sys.argv[0]} {'|'.join(TARGETS)}")
    target = sys.argv[1]
    cfg = TARGETS[target]
    print(f"=== Deploy nach {target} ({cfg['user']}@{cfg['host']}:{cfg['remote_dir']}) ===")

    transport = connect(cfg)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.chdir(cfg["remote_dir"])

    print("\n=== Schritt 1: Alte Dateien/Ordner löschen ===")
    items = sftp.listdir_attr(".")
    for item in items:
        if item.filename in cfg["keep"] or item.filename.startswith("."):
            print(f"  Behalten: {item.filename}")
            continue
        if stat.S_ISDIR(item.st_mode):
            sftp_rm_recursive(sftp, item.filename)
            try:
                sftp.rmdir(item.filename)
                print(f"  Ordner gelöscht: {item.filename}")
            except Exception as e:
                print(f"  WARNUNG Ordner: {item.filename} -> {e}")
        else:
            try:
                sftp.remove(item.filename)
                print(f"  Datei gelöscht:  {item.filename}")
            except Exception as e:
                print(f"  WARNUNG Datei: {item.filename} -> {e}")

    print("\n=== Schritt 2: Neue Dateien hochladen ===")
    missing = False
    for fname in UPLOAD_FILES:
        local = os.path.join(LOCAL_DIR, fname)
        if os.path.exists(local):
            sftp.put(local, fname)
            print(f"  Hochgeladen: {fname}")
        else:
            print(f"  FEHLER: {fname} nicht gefunden!")
            missing = True

    for dname in UPLOAD_DIRS:
        local = os.path.join(LOCAL_DIR, dname)
        if os.path.isdir(local):
            sftp_upload_dir(sftp, local, dname)
        else:
            print(f"  FEHLER: Ordner {dname} nicht gefunden!")
            missing = True

    sftp.close()
    transport.close()
    if missing:
        sys.exit("\n=== Fertig, aber mit Fehlern (siehe oben). ===")
    print("\n=== Fertig! Alle Dateien wurden erfolgreich übertragen. ===")


if __name__ == "__main__":
    main()
