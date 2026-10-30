#!/usr/bin/env python3
"""
Deploy-Script für Production (www.anwaelte-aalen.de, IONOS):
Baut die Seite (build.sh), prüft sie, löscht alte Dateien auf dem Server
und lädt den Build hoch.

Staging wird per rsync aus GitHub Actions ausgeliefert, nicht über dieses Script.

Zugangsdaten (optional, sonst interaktive Passwortabfrage):
    DEPLOY_PASSWORD     SFTP-Passwort
    DEPLOY_KNOWN_HOSTS  Pfad zu einer known_hosts-Datei (Host-Key wird geprüft)
"""

import paramiko
import os
import sys
import getpass
import stat
import subprocess

HOST = "home29819267.1and1-data.host"
USER = "acc828869407"
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(LOCAL_DIR, "_site")

# Dateien/Ordner die NICHT gelöscht werden
KEEP = {".ssh", ".bash_history", ".htaccess", "logs"}

PROD_URL = "https://www.anwaelte-aalen.de/"
STAGING_HOST = "container.ga-cms.de"


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


def build_and_check():
    """Baut die Seite und stellt sicher, dass sie für Production taugt."""
    subprocess.run([os.path.join(LOCAL_DIR, "build.sh"), BUILD_DIR], check=True)

    errors = []
    for root, _, files in os.walk(BUILD_DIR):
        for fname in files:
            if not fname.endswith((".html", ".css")):
                continue
            path = os.path.join(root, fname)
            with open(path, encoding="utf-8") as f:
                if STAGING_HOST in f.read():
                    errors.append(f"{os.path.relpath(path, BUILD_DIR)} enthält {STAGING_HOST}")

    with open(os.path.join(BUILD_DIR, "index.html"), encoding="utf-8") as f:
        index = f.read()
    for needle in ('content="index, follow"', f'og:url" content="{PROD_URL}"'):
        if needle not in index:
            errors.append(f"index.html: {needle} fehlt")

    if errors:
        sys.exit("FEHLER: Build ist nicht für Production geeignet:\n  " + "\n  ".join(errors))
    print("  Build-Prüfung OK")


def check_host_key(transport):
    """Prüft den Host-Key gegen DEPLOY_KNOWN_HOSTS, falls gesetzt."""
    known_hosts = os.environ.get("DEPLOY_KNOWN_HOSTS")
    if not known_hosts:
        print("  HINWEIS: DEPLOY_KNOWN_HOSTS nicht gesetzt, Host-Key wird nicht geprüft.")
        return
    keys = paramiko.HostKeys(known_hosts)
    server_key = transport.get_remote_server_key()
    expected = keys.lookup(HOST)
    if not expected or expected.get(server_key.get_name()) != server_key:
        sys.exit(f"FEHLER: Host-Key von {HOST} stimmt nicht mit {known_hosts} überein!")


def main():
    print("=== Schritt 0: Build erstellen und prüfen ===")
    build_and_check()

    transport = paramiko.Transport((HOST, 22))
    transport.start_client()
    check_host_key(transport)
    password = os.environ.get("DEPLOY_PASSWORD") or getpass.getpass(
        f"SFTP-Passwort für {USER}@{HOST}: "
    )
    transport.auth_password(USER, password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    print("\n=== Schritt 1: Alte Dateien/Ordner löschen ===")
    items = sftp.listdir_attr(".")
    for item in items:
        if item.filename in KEEP or item.filename.startswith("."):
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
    for item in os.listdir(BUILD_DIR):
        local = os.path.join(BUILD_DIR, item)
        if os.path.isdir(local):
            sftp_upload_dir(sftp, local, item)
        else:
            sftp.put(local, item)
            print(f"  Hochgeladen: {item}")

    sftp.close()
    transport.close()
    print("\n=== Fertig! Alle Dateien wurden erfolgreich übertragen. ===")


if __name__ == "__main__":
    main()
