# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report security issues privately to:

- **Email:** [sepehr@sageteam.org](mailto:sepehr@sageteam.org)

Include:

- A description of the issue and potential impact
- Steps to reproduce (proof of concept if possible)
- Affected versions

We aim to acknowledge reports within **5 business days** and will coordinate a fix and
disclosure timeline with you.

## Secure Usage

- Prefer **TLS** (`use_ssl=True`, port 993) or **STARTTLS** for cleartext connections.
- Store credentials in environment variables or a secrets manager, not in source code.
- Use **OAuth2** (`connect_oauth2`) when your provider supports it instead of passwords.
- Keep Python and this library updated.
