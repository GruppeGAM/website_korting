# Deployment

| Umgebung | URL | Auslöser | Weg |
|---|---|---|---|
| Staging | https://container.ga-cms.de/ (Login nötig) | automatisch bei Push/Merge auf Branch `staging` | rsync über SSH |
| Prod | https://www.anwaelte-aalen.de/ | nur manuell: GitHub → Actions → **Deploy Production** → **Run workflow** (Branch `main`) | SFTP (`deploy.py`) |

Ablauf: Änderungen auf `staging` pushen → auf container.ga-cms.de prüfen → `staging` in `main` mergen → Prod-Workflow per Klick starten.

## Build

`./build.sh` stellt die auszuliefernden Dateien in `_site/` zusammen (HTML, `styles.css`, `images/`).
Nur dieser Ordner wird hochgeladen – kein `.git`, `.github`, keine Skripte oder Doku.
Neue Seiten oder Ordner müssen in `build.sh` ergänzt werden.

## Staging

- Ziel: `korting-deploy@container.ga-cms.de:/var/www/container.ga-cms.de/`
- Workflow: [.github/workflows/deploy-staging.yml](.github/workflows/deploy-staging.yml)
- Der Server wird vom Server-Admin betreut. Passwortschutz (Basic Auth) und
  `X-Robots-Tag: noindex, nofollow` kommen vom Server, nicht aus diesem Repo.
- Der SSH-Key ist serverseitig eingeschränkt: nur rsync, kein Terminal, kein sudo.
- Server hat rsync 3.1.3 – keine Optionen verwenden, die es erst ab 3.2 gibt (z. B. `--mkpath`).
- Nach dem Deploy prüft ein Smoke-Test: ohne Login `401`; mit Login (falls Secrets gesetzt)
  `200` für `/`, `impressum.html`, `datenschutz.html`, `styles.css` und dass `index.html` dem Build entspricht.

Manuell (Notfall), aus dem Repo-Ordner:

```bash
./build.sh && rsync -rltvz --delete --chmod=D755,F644 --exclude='.well-known/' _site/ korting-deploy@container.ga-cms.de:/var/www/container.ga-cms.de/
```

## Production

- Workflow: [.github/workflows/deploy-prod.yml](.github/workflows/deploy-prod.yml), läuft nur von `main`.
- `deploy.py` baut die Seite, bricht ab, wenn `container.ga-cms.de` im Build vorkommt oder
  `index.html` nicht `index, follow` bzw. `og:url` = `https://www.anwaelte-aalen.de/` hat,
  löscht dann die alten Dateien auf dem IONOS-Webspace (außer `.htaccess`, `logs`, Dotfiles) und lädt `_site/` hoch.
- Manuell (Notfall): `python deploy.py` (fragt nach dem SFTP-Passwort).

## GitHub-Einrichtung (Settings → Environments)

**Environment `staging`** – Secrets:

| Secret | Inhalt | Pflicht |
|---|---|---|
| `STAGING_SSH_KEY` | privater Key `deploy_staging` (Kommentar `github-actions-staging`) | ja |
| `STAGING_KNOWN_HOSTS` | `ssh-keyscan container.ga-cms.de` | ja |
| `STAGING_BASIC_AUTH_USER` | `korting` | optional (Smoke-Test mit Login) |
| `STAGING_BASIC_AUTH_PASS` | Passwort des Staging-Logins | optional |

`STAGING_KNOWN_HOSTS` muss diese Fingerabdrücke ergeben (`ssh-keygen -lf staging_known_hosts`):

```
ED25519 SHA256:eRVj0M5qNfXXJPMRRrawKVafCiDD1olIsTMpLJiFtks
ECDSA   SHA256:/scjhY14eEHWk7f7r2mLqjAf3m2RKw0R/cdMjwvHOUo
RSA     SHA256:dkB1/t+DosGwdedBPepojh4FyDD/zvrHWA3DiWJDsh4
```

**Environment `production`** – Deployment branches: nur `main`. Secrets:

| Secret | Inhalt |
|---|---|
| `PROD_SFTP_PASSWORD` | IONOS-SFTP-Passwort |
| `PROD_KNOWN_HOSTS` | `ssh-keyscan home29819267.1and1-data.host` |
