# Deployment

| Umgebung | URL | Auslöser |
|---|---|---|
| Staging | https://container.ga-cms.de (Passwortschutz) | automatisch bei Push/Merge auf Branch `staging` |
| Prod | https://www.anwaelte-aalen.de | nur manuell: GitHub → Actions → **Deploy Production** → **Run workflow** (Branch `main`) |

Ablauf: Änderungen auf `staging` pushen → auf container.ga-cms.de prüfen → `staging` in `main` mergen → Prod-Workflow per Klick starten.

Lokaler Fallback: `python deploy.py staging` bzw. `python deploy.py prod` (fragt nach dem Passwort).

---

## Einmalige Einrichtung

### 1. Staging-Server (container.ga-cms.de)

```bash
# Deploy-User + Webverzeichnis
sudo adduser --disabled-password --gecos "" deploy
sudo mkdir -p /var/www/staging-korting
sudo chown deploy:www-data /var/www/staging-korting
sudo chmod 755 /var/www/staging-korting

# Public Key für GitHub Actions eintragen (Inhalt von deploy_staging.pub, siehe unten)
sudo -u deploy mkdir -p -m 700 /home/deploy/.ssh
sudo -u deploy nano /home/deploy/.ssh/authorized_keys
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# Passwortschutz
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd-staging korting
```

nginx-Server-Block für `container.ga-cms.de` anpassen (SSL-Zeilen bleiben wie sie sind):

```nginx
server {
    listen 443 ssl http2;
    server_name container.ga-cms.de;

    root /var/www/staging-korting;
    index index.html;

    auth_basic           "Staging";
    auth_basic_user_file /etc/nginx/.htpasswd-staging;

    add_header X-Robots-Tag "noindex, nofollow" always;

    location / { try_files $uri $uri/ =404; }

    # ssl_certificate ... (bestehend)
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
curl -I https://container.ga-cms.de          # erwartet: 401
```

### 2. SSH-Key für Staging erzeugen (lokal)

```bash
ssh-keygen -t ed25519 -f deploy_staging -N "" -C "github-actions-staging"
```

`deploy_staging.pub` → auf den Server (siehe oben), `deploy_staging` → GitHub-Secret. Danach beide Dateien lokal löschen, **nicht committen**.

### 3. GitHub (Settings → Environments)

**Environment `staging`**, Secrets:
- `STAGING_SSH_KEY` – Inhalt von `deploy_staging`
- `STAGING_KNOWN_HOSTS` – Ausgabe von `ssh-keyscan container.ga-cms.de`

**Environment `production`**:
- Deployment branches: nur `main`
- Secrets:
  - `PROD_SFTP_PASSWORD` – IONOS-SFTP-Passwort
  - `PROD_KNOWN_HOSTS` – Ausgabe von `ssh-keyscan home29819267.1and1-data.host`

### 4. Branch anlegen

```bash
git push origin main:staging
```
