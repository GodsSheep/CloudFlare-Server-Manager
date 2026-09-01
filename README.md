NebulaForge Server Manager
==========================

Universal Local → Server → Tunnel → Web Control Center

Built with PySide6, psutil, and SQLite.

## Features

- Live project management with auto-recovery
- Universal runtime engine (Static, Python, Node, PHP, Docker, Custom)
- Tunnel orchestration (Cloudflare, ngrok, LocalTunnel)
- Background job system for safe imports and operations
- File manager with import/export
- Request monitoring and log center
- Diagnostics engine
- Multi-server capable architecture

## Quick Start

```bash
pip install -r requirements.txt
python main.pyw
```

## Project Structure

```
NebulaForge/
├── main.pyw
├── requirements.txt
├── README.md
├── app/
│   ├── gui/          - PySide6 desktop interface
│   ├── core/         - Jobs, events, state machine
│   ├── runtime/      - Universal runtime engine
│   ├── tunnels/      - Tunnel provider abstraction
│   ├── server/       - Process and port supervisors
│   ├── files/        - File and project manager
│   ├── monitoring/   - Request monitor
│   ├── diagnostics/  - Diagnostics center
│   ├── database/     - SQLite models
│   └── utils/        - Helpers and logging
├── data/             - Projects, logs, backups, database
├── assets/           - Icons and images
├── bin/              - Bundled executables (cloudflared)
└── scripts/          - Install and run scripts
```

## License

MIT
