# Installation

This project ships **two** deployment paths. Picking the wrong one is the failure this
document exists to prevent.

| Host | Path | Entry point |
|---|---|---|
| Docker | compose | `make start` |
| **Podman + systemd** | **quadlet** | **`make quadlet-install`** |

## Step 0 — Identify the host before anything else

```bash
command -v podman && echo "PODMAN — use the quadlet path"
command -v docker  && echo "docker — compose path is fine"
systemd-detect-virt          # wsl / hyperv / none — affects where the stack actually lives
hostnamectl                  # confirm WHICH machine you are on
```

**Do this even when you think you know.** On 2026-08-31 a session read `.container` files on
one host and reported them as the live deployment, while the running stack was on a different
machine entirely — a Hyper-V podman VM reachable over mirrored networking. Two hosts, one
`localhost`.

## Podman path

Units are versioned in `./quadlet/` and installed into `~/.config/containers/systemd/`.
**The repo is the source of truth; the systemd directory is a build artifact.**

```bash
make image               # build the image
make quadlet-install     # copy units, daemon-reload, validate
make quadlet-start       # start via systemd --user
make verify              # REQUIRED — see below
```

### The units carry no host paths

The deployment references an image by tag and keeps state in a named volume. It
does not bind-mount a source checkout, a config file, or a certificate directory
from the host, so the same unit is correct on every machine.

An earlier revision did build on the target from a bind-mounted checkout. On a
podman machine that checkout arrives over **9p**, and 9p produced three separate
failures: overlayfs cannot be layered over it so `podman build` refuses outright;
a 9p mount is owned by exactly one uid so a root-run unit cannot traverse it; and
it is not mounted yet when units first start at boot, so the service failed every
reboot. None of those are 9p bugs — they are the cost of reaching into the host
from a container deployment. Build the image, ship the image.

Config and secrets follow the same rule: `nginx.conf` is baked into
`Containerfile.nginx`, and TLS material is a podman secret, not a mounted host
directory.

nginx is the old compose `production` profile. A profile has no quadlet equivalent, so it is
a separate unit with **no `[Install]` section** — it exists but never auto-starts:

```bash
systemctl --user enable --now sangre-signal-nginx.service
```

### Never run `make run` on a podman host

`docker-compose up` under podman produces loose containers that systemd does not supervise.
Nothing restarts them, nothing orders them against `falcon.network`, and `systemctl` reports
nothing at all. They look deployed and are not managed.

## Step N — `make verify` is not optional

**A unit file existing is not a service running.** These are different facts and they were
conflated on 2026-08-31: `.container` files were present in
`~/.config/containers/systemd/` while `podman ps` returned empty, and the deployment was
described as live.

`make verify` fails unless the container is **up** *and* **answering**:

```
── is a container running? ──
FAIL: no running sangre-signal-web container
make: *** [verify] Error 1
```

Do not report a successful deployment without a passing `make verify`. `make quadlet-status`
deliberately prints unit state and `podman ps` side by side for the same reason.

## What conversion changed, and why

Compose constructs with no direct quadlet equivalent — each was translated, not dropped:

| compose | quadlet | why |
|---|---|---|
| `build: .` | `sangre-signal.build` unit | `.container` cannot build; web `Requires=` the build unit |
| `./data:/app/data` | absolute path + `:Z` | relative paths don't resolve under systemd; `:Z` sets the SELinux label compose omitted |
| `restart: unless-stopped` | `[Service] Restart=always` | compose restart policies aren't systemd policies |
| `depends_on: web` | `After=` + `Requires=` | ordering belongs to systemd |
| `profiles: [production]` | separate unit, no `[Install]` | opt-in is expressed by absence, not a flag |
| `healthcheck:` | `HealthCmd=` / `HealthInterval=` / … | podman health, surfaced to systemd |

Re-validate after editing any unit:

```bash
make quadlet-validate     # /usr/libexec/podman/quadlet -dryrun -user
```

## Local development

Unchanged — no containers involved:

```bash
make install    # pip install -r requirements.txt
make dev        # FLASK_ENV=development python run.py
```

## Regression coverage

This conversion is covered by an automated behavioural check that forbids
`docker compose up` / `podman-compose up` on a podman host, requires quadlet unit files (or a
`podlet` invocation) instead, and asserts the distinction this document is built around:
unit files existing is not the same fact as services running.
