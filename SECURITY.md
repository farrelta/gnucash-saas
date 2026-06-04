# GnuCash SaaS — Public Deployment Security Recommendations

To ensure your Azure VM deployment is secure against public threats, follow these recommendations.

## 1. Environment & Secrets Management
- **SECRET_KEY**: Never use a default or guessable `SECRET_KEY`. Generate a strong 256-bit random string (e.g., `openssl rand -hex 32`) and provide it in your `.env` file. The backend will now crash on startup if this is omitted.
- **Database Credentials**: Use strong, unique passwords for your Azure MySQL database. Store these in your `.env` file and never commit them to version control.

## 2. Network Security Groups (NSG)
Configure your Azure Virtual Machine NSG to:
- **Allow** inbound traffic on TCP port 80 (HTTP) and 443 (HTTPS) from the Internet.
- **Block** inbound traffic on TCP port 8000 (FastAPI internal), port 3306 (MySQL default, unless strictly needed from a specific IP), and port 14500 (Xpra internal).
- Never expose the Docker socket (`/var/run/docker.sock`) over TCP.

## 3. Database Security
- **Azure MySQL Firewall**: Restrict the Azure MySQL firewall rules so that *only* the specific Public IP address of your Azure VM can connect. Disable "Allow public access from any Azure service" if possible, as it broadens the attack surface.
- **SSL**: Enforce SSL connections between the FastAPI backend and Azure MySQL by appending `?ssl_ca=/path/to/cert.pem` to your `DATABASE_URL` (Azure provides root certificates for secure connections).

## 4. Traefik & Session Routing
- Traefik automatically generates unique HTTPS routes using a UUID `session_token`. Because Xpra itself does not currently authenticate websockets in this configuration, **the UUID is the only mechanism preventing unauthorised session access**. 
- **Zero-Trust Hardening**: For a true zero-trust setup in the future, implement Traefik ForwardAuth middleware. This will intercept traffic bound for `/session/{session_token}` and validate the JWT cookie before allowing the websocket connection to proxy to Xpra.

## 5. File System Security
- The application automatically mitigates path traversal attacks (e.g., `../../`) and restricts file uploads to `.gnucash, .qif, .ofx, .csv` up to 50MB. 
- Ensure the Azure VM host directory (`/opt/gnucash-data`) is owned by a restricted user and not `root`, preventing container breakouts from modifying host system binaries.

## 6. Backups
- Regularly back up your Azure MySQL database and the `/opt/gnucash-data` host directory to an external Azure Blob Storage container to prevent data loss.
