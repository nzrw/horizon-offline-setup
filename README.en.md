# Horizon Offline Setup

[Русская версия → README.md](README.md)

![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Windows x64 tested](https://img.shields.io/badge/Windows-x64%20tested-0078D6?logo=windows&logoColor=white)
![Horizon](https://img.shields.io/badge/Horizon-Rust%20client-6E40C9)
![No dependencies](https://img.shields.io/badge/dependencies-standard%20library-2ea44f)

> 🎮 One script, a clean Horizon setup, and offline play without launcher hacks.
> Minecraft files are never stored in this repository: they are downloaded from
> Mojang's public servers and checked against SHA-1.

<p align="center">
  <img src="docs/images/horizon-launcher.png" alt="Horizon launcher with the selected offline version" width="900">
</p>

<p align="center"><sub>Horizon launcher with a prepared 26.3 installation.</sub></p>

Cross-platform downloader for the files required by [Horizon](https://playhorizon.dev),
the Rust rewrite of Minecraft: Java Edition 26.3.

This is a port of [slycat555/horizon-offline-setup](https://gitea.com/slycat555/horizon-offline-setup).
The port was made at the request of the Horizon team. The repository contains no
Minecraft files: it downloads them from Mojang's public endpoints and verifies the
published SHA-1 hashes.

Windows x64 was tested with Horizon nightly from 2026-10-29. Linux and macOS are
supported by the path and library-selection code but were not tested in this port.
ARM is not supported because the script selects x86-64 libraries.

## Requirements

- Python 3.8 or newer.
- Your own Minecraft Java Edition 26.3 files or an internet connection to Mojang's
  public download endpoints.
- A Horizon launcher installation.

The script uses only Python's standard library. It does not ask for a Microsoft
account and does not bypass authentication or DRM; it only downloads public files.

## Step-by-step: Windows

1. Download or clone this repository.

2. Open PowerShell in the repository folder:

   ```powershell
   cd C:\path\to\horizon-offline-setup
   ```

3. Download the Minecraft 26.3 files into the launcher's default game folder:

   ```powershell
   python fetch_minecraft.py
   ```

   To use another folder:

   ```powershell
   python fetch_minecraft.py --minecraft-dir "D:\Horizon\.minecraft"
   ```

   The script downloads the 26.3 client and server jars, OS-specific libraries,
   the asset index, sounds, fonts and title-screen panorama files. Every downloaded
   jar, library and asset object is checked against SHA-1. Interrupted `.part`
   files are downloaded again from the beginning on the next run.

4. Point the launcher at the folder and prepare Horizon's resources:

   ```powershell
   horizon-launcher settings minecraft-dir "$env:APPDATA\.minecraft"
   horizon-launcher prepare --minecraft "$env:APPDATA\.minecraft"
   horizon-launcher
   ```

5. If the current launcher requires an account for an offline name, enable the
   developer option:

   - Open the launcher window.
   - Click the launcher version in the sidebar seven times.
   - Open **Settings → Developer options**.
   - Enable **Offline names without an account**.

   You can also add this setting to
   `$env:APPDATA\horizon-launcher\settings.json`:

   ```json
   "dev_offline": true
   ```

6. Start the game from the launcher window. The command-line `horizon-launcher
   play` path intentionally requires an owned Microsoft account on current
   nightlies; the GUI path is the one that applies `dev_offline`.

## Linux and macOS

Run the same script with Python 3:

```bash
python3 fetch_minecraft.py
```

The default game folders are `~/.minecraft` on Linux and
`~/Library/Application Support/minecraft` on macOS. You can override either with:

```bash
python3 fetch_minecraft.py --minecraft-dir /path/to/.minecraft
```

Then prepare the selected folder with the Horizon launcher and start the game from
its GUI window when using offline names without an account.

## What the script downloads

- `versions/26.3/26.3.json` and the 26.3 client jar;
- `26.3-server.jar`;
- libraries allowed by Mojang's rules for the current OS and x86-64 architecture;
- the asset index and the sounds, font and title-panorama objects Horizon needs.

The script never stores Minecraft files in this repository. Re-running it skips
valid files and replaces files whose SHA-1 does not match. It does not resume an
interrupted transfer from the last byte.

<details>
<summary>✨ What you get after setup</summary>

1. A Minecraft 26.3 folder with the client, server, libraries and required assets.
2. Prepared resources understood by Horizon.
3. Offline names and GUI launching without a Microsoft account when `dev_offline`
   is enabled.

</details>

## Troubleshooting

- **`26.3 not found or an unknown republish`**: Mojang published a new manifest
  hash. Update the `ACCEPTED_JSON_SHA1` list in `fetch_minecraft.py` only after
  checking the new version manifest and the Horizon research lock.
- **The launcher cannot prepare the game**: verify that `26.3.json`, the client
  jar and `26.3-server.jar` are in the folder passed to `--minecraft-dir`.
- **The game is silent**: run Horizon's resource preparation again and verify that
  the sounds were downloaded successfully.
- **Offline play is rejected**: enable `dev_offline` and start from the launcher
  window instead of the CLI `play` command.
- **PowerShell does not expand `%APPDATA%`**: use `$env:APPDATA` in PowerShell.
  `%APPDATA%` is the syntax for `cmd.exe`.

## Attribution

Original project and idea: [slycat555/horizon-offline-setup](https://gitea.com/slycat555/horizon-offline-setup).
The cross-platform port, Windows support, SHA-1 updates and offline-launcher
documentation were prepared for the Horizon team.

<p align="center">
  <img src="docs/images/orbital-wheel.png" alt="Orbital Laser wheel running in Horizon" width="900">
</p>

<p align="center"><sub>Example Horizon setup with Orbital Laser running after resource preparation.</sub></p>
