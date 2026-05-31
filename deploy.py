#!/usr/bin/env python3
"""
Deploy-Script: Löscht alte Dateien auf dem Server und lädt neue hoch.
"""

import paramiko
import os
import getpass
import stat

HOST = "home29819267.1and1-data.host"
USER = "acc828869407"
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

# Dateien/Ordner die NICHT gelöscht werden
KEEP = {".ssh", ".bash_history", ".htaccess", "logs"}

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


def main():
    password = getpass.getpass(f"SFTP-Passwort für {USER}@{HOST}: ")

    transport = paramiko.Transport((HOST, 22))
    transport.connect(username=USER, password=password)
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
    for fname in UPLOAD_FILES:
        local = os.path.join(LOCAL_DIR, fname)
        if os.path.exists(local):
            sftp.put(local, fname)
            print(f"  Hochgeladen: {fname}")
        else:
            print(f"  FEHLER: {fname} nicht gefunden!")

    for dname in UPLOAD_DIRS:
        local = os.path.join(LOCAL_DIR, dname)
        if os.path.isdir(local):
            sftp_upload_dir(sftp, local, dname)
        else:
            print(f"  FEHLER: Ordner {dname} nicht gefunden!")

    sftp.close()
    transport.close()
    print("\n=== Fertig! Alle Dateien wurden erfolgreich übertragen. ===")


if __name__ == "__main__":
    main()
