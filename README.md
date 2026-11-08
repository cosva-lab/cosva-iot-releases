# Cosva IoT releases

Public installers and release artifacts for **Raspberry Pi 5 (8 GB)** running **Ubuntu Desktop 24.04 or 26.04 LTS ARM64**.

**[Download Cosva](https://github.com/cosva-lab/cosva-iot-releases/releases)**

Downloads do not require a GitHub account or token. Development source is maintained in the private `cosva-lab/cosva-iot` monorepo. This repository contains distribution documentation and release artifacts only.

## Install

1. Download `cosva-setup_VERSION_arm64.deb` and its `.sha256` receipt from a release.
2. On the Raspberry, outside milking hours, verify and install:

```sh
sha256sum -c cosva-setup_VERSION_arm64.deb.sha256
sudo apt install ./cosva-setup_VERSION_arm64.deb
```

3. Open **Cosva — Installation and recovery**, or `http://127.0.0.1:3501/setup`.
4. Create the local administrator and choose a new installation or adoption of an existing one.
5. Supply the farm configuration. A new installation also needs the farm API key and the MQTT password provisioned on the devices.
6. Follow setup progress. Once setup finishes, reboot manually to verify automatic startup.

The Debian installs the compiled helper and its services. The assistant installs Docker, Compose, Chromium and the application after APT finishes. The Raspberry host does not need Node.js, Go or Python. The application operates locally; initial installation and downloading a new release require internet access.

## Release channels and updates

- **Candidate / prerelease:** for testing and certification on a real Pi with real sensors. It is not considered production-ready.
- **Stable / latest:** requires matching physical certification evidence before promotion.
- Publishing a release never updates devices automatically. Each update requires an administrator's request from **Settings → Updates**.
- Active milking or an open parlor session rejects the update. The supervisor verifies signatures, schema compatibility and a restored scratch backup before replacement, then checks the services and browser rendering.
- Recovery uses previously verified local images without automatically restoring a database over newer production or outbox data.

The independent recovery panel remains at `http://127.0.0.1:3501/updates` when the application dashboard is unavailable.

## Release assets

| File | Purpose |
| --- | --- |
| `cosva-setup_VERSION_arm64.deb` | Ubuntu Desktop ARM64 installer |
| `cosva-setup_VERSION_arm64.deb.sha256` | Installer integrity receipt |
| `release.json` | Signed manifest containing exact images and versions |

The Raspberry verifies manifests with the trusted public key embedded in the installer and downloads images by immutable digest. Private signing keys, build credentials and farm data are not distributed.

Use **1.0.3 or newer**. Version **1.0.1** has a packaging issue on clean systems; **1.0.2** fixes that archive but its service images cannot load an absolute farm-configuration path. Version **1.0.3** fixes both issues. Preserve existing configuration and Docker volumes when repairing an installation.
