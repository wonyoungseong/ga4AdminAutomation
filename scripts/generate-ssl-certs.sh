#!/bin/bash
"""
GA4 Admin Portal - SSL Certificate Generation Script
Generates self-signed certificates for development and provides Let's Encrypt setup for production
"""

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSL_DIR="${SSL_DIR:-./ssl}"
DOMAIN="${DOMAIN:-localhost}"
COUNTRY="${COUNTRY:-US}"
STATE="${STATE:-CA}"
CITY="${CITY:-San Francisco}"
ORG="${ORG:-GA4 Admin Portal}"
OU="${OU:-Infrastructure}"
EMAIL="${EMAIL:-admin@example.com}"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL is required but not installed"
    fi
    
    log "✓ All dependencies satisfied"
}

# Create SSL directory
create_ssl_directory() {
    log "Creating SSL directory: $SSL_DIR"
    mkdir -p "$SSL_DIR"
    chmod 755 "$SSL_DIR"
}

# Generate self-signed certificate
generate_self_signed() {
    log "Generating self-signed SSL certificate for $DOMAIN..."
    
    # Create private key
    openssl genrsa -out "$SSL_DIR/key.pem" 4096
    
    # Create certificate signing request config
    cat > "$SSL_DIR/csr.conf" <<EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=$COUNTRY
ST=$STATE
L=$CITY
O=$ORG
OU=$OU
CN=$DOMAIN

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = localhost
DNS.4 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    # Generate certificate signing request
    openssl req -new -key "$SSL_DIR/key.pem" -out "$SSL_DIR/csr.pem" -config "$SSL_DIR/csr.conf"
    
    # Generate self-signed certificate
    openssl x509 -req -in "$SSL_DIR/csr.pem" -signkey "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" \
        -days 365 -extensions v3_req -extfile "$SSL_DIR/csr.conf"
    
    # Create certificate chain (for self-signed, same as cert)
    cp "$SSL_DIR/cert.pem" "$SSL_DIR/fullchain.pem"
    
    # Set proper permissions
    chmod 600 "$SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem" "$SSL_DIR/fullchain.pem"
    
    # Generate DH parameters for enhanced security
    log "Generating Diffie-Hellman parameters (this may take a while)..."
    openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048
    chmod 644 "$SSL_DIR/dhparam.pem"
    
    log "✓ Self-signed certificate generated successfully"
    log "Certificate: $SSL_DIR/cert.pem"
    log "Private Key: $SSL_DIR/key.pem"
    log "Full Chain: $SSL_DIR/fullchain.pem"
    log "DH Params: $SSL_DIR/dhparam.pem"
}

# Generate Let's Encrypt certificate (production)
generate_letsencrypt() {
    local domain="$1"
    local email="$2"
    
    log "Setting up Let's Encrypt certificate for $domain..."
    
    if ! command -v certbot &> /dev/null; then
        warn "Certbot not found. Installing certbot..."
        
        # Install certbot based on OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y certbot python3-certbot-nginx
            elif command -v yum &> /dev/null; then
                sudo yum install -y certbot python3-certbot-nginx
            else
                error "Unable to install certbot automatically. Please install manually."
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install certbot
            else
                error "Please install Homebrew first or install certbot manually"
            fi
        else
            error "Unsupported OS for automatic certbot installation"
        fi
    fi
    
    # Stop nginx temporarily for standalone validation
    log "Stopping nginx for certificate generation..."
    docker-compose stop nginx || true
    
    # Generate certificate
    log "Generating Let's Encrypt certificate..."
    certbot certonly --standalone \
        --non-interactive \
        --agree-tos \
        --email "$email" \
        -d "$domain" \
        --cert-path "$SSL_DIR/cert.pem" \
        --key-path "$SSL_DIR/key.pem" \
        --fullchain-path "$SSL_DIR/fullchain.pem" \
        --chain-path "$SSL_DIR/chain.pem"
    
    # Set proper permissions
    chmod 600 "$SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem" "$SSL_DIR/fullchain.pem" "$SSL_DIR/chain.pem"
    
    # Generate DH parameters
    if [[ ! -f "$SSL_DIR/dhparam.pem" ]]; then
        log "Generating Diffie-Hellman parameters..."
        openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048
        chmod 644 "$SSL_DIR/dhparam.pem"
    fi
    
    # Restart nginx
    log "Restarting nginx..."
    docker-compose start nginx
    
    log "✓ Let's Encrypt certificate generated successfully"
    
    # Set up auto-renewal
    setup_auto_renewal "$domain" "$email"
}

# Setup auto-renewal for Let's Encrypt
setup_auto_renewal() {
    local domain="$1"
    local email="$2"
    
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > "$SSL_DIR/renew-cert.sh" <<EOF
#!/bin/bash
# Auto-renewal script for Let's Encrypt certificates

set -euo pipefail

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] \$1"
}

log "Starting certificate renewal check..."

# Stop nginx
docker-compose stop nginx || true

# Renew certificate
certbot renew --standalone --quiet

# Restart nginx
docker-compose start nginx

log "Certificate renewal check completed"
EOF

    chmod +x "$SSL_DIR/renew-cert.sh"
    
    # Add to crontab (runs every 12 hours)
    local cron_job="0 */12 * * * $PWD/$SSL_DIR/renew-cert.sh >> $PWD/logs/ssl-renewal.log 2>&1"
    
    # Check if cron job already exists
    if ! crontab -l 2>/dev/null | grep -q "renew-cert.sh"; then
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        log "✓ Auto-renewal cron job added"
    else
        log "✓ Auto-renewal cron job already exists"
    fi
}

# Validate generated certificates
validate_certificates() {
    log "Validating generated certificates..."
    
    if [[ ! -f "$SSL_DIR/cert.pem" ]] || [[ ! -f "$SSL_DIR/key.pem" ]]; then
        error "Certificate files not found"
    fi
    
    # Check certificate validity
    if ! openssl x509 -in "$SSL_DIR/cert.pem" -text -noout > /dev/null 2>&1; then
        error "Invalid certificate file"
    fi
    
    # Check private key
    if ! openssl rsa -in "$SSL_DIR/key.pem" -check -noout > /dev/null 2>&1; then
        error "Invalid private key file"
    fi
    
    # Check if certificate and key match
    cert_modulus=$(openssl x509 -in "$SSL_DIR/cert.pem" -modulus -noout)
    key_modulus=$(openssl rsa -in "$SSL_DIR/key.pem" -modulus -noout)
    
    if [[ "$cert_modulus" != "$key_modulus" ]]; then
        error "Certificate and private key do not match"
    fi
    
    # Get certificate info
    log "Certificate information:"
    openssl x509 -in "$SSL_DIR/cert.pem" -text -noout | grep -E "(Subject:|Not Before:|Not After:|DNS:)"
    
    log "✓ Certificate validation passed"
}

# Create nginx SSL configuration snippet
create_nginx_ssl_config() {
    log "Creating nginx SSL configuration..."
    
    cat > "$SSL_DIR/ssl-params.conf" <<EOF
# SSL Configuration for GA4 Admin Portal
# Modern configuration with security best practices

# SSL protocols and ciphers
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# Session settings
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;

# DH parameters
ssl_dhparam /etc/nginx/ssl/dhparam.pem;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# Security headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';" always;
EOF

    log "✓ Nginx SSL configuration created: $SSL_DIR/ssl-params.conf"
}

# Main function
main() {
    echo -e "${BLUE}"
    echo "============================================="
    echo "  GA4 Admin Portal SSL Certificate Setup"
    echo "============================================="
    echo -e "${NC}"
    
    # Parse command line arguments
    local cert_type="self-signed"
    local production_domain=""
    local production_email=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --production)
                cert_type="letsencrypt"
                shift
                ;;
            --domain)
                production_domain="$2"
                shift 2
                ;;
            --email)
                production_email="$2"
                shift 2
                ;;
            --ssl-dir)
                SSL_DIR="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --production              Generate Let's Encrypt certificate for production"
                echo "  --domain DOMAIN          Domain name for production certificate"
                echo "  --email EMAIL            Email for Let's Encrypt registration"
                echo "  --ssl-dir DIR            SSL directory (default: ./ssl)"
                echo "  --help                   Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                                    # Generate self-signed certificate"
                echo "  $0 --production --domain example.com --email admin@example.com"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Validate production arguments
    if [[ "$cert_type" == "letsencrypt" ]]; then
        if [[ -z "$production_domain" ]] || [[ -z "$production_email" ]]; then
            error "Production mode requires --domain and --email arguments"
        fi
    fi
    
    # Run setup
    check_dependencies
    create_ssl_directory
    
    if [[ "$cert_type" == "letsencrypt" ]]; then
        generate_letsencrypt "$production_domain" "$production_email"
    else
        generate_self_signed
    fi
    
    validate_certificates
    create_nginx_ssl_config
    
    echo -e "${GREEN}"
    echo "============================================="
    echo "  SSL Certificate Setup Complete!"
    echo "============================================="
    echo "SSL directory: $SSL_DIR"
    echo "Certificate type: $cert_type"
    if [[ "$cert_type" == "letsencrypt" ]]; then
        echo "Domain: $production_domain"
        echo "Auto-renewal: Enabled"
    fi
    echo -e "${NC}"
    
    if [[ "$cert_type" == "self-signed" ]]; then
        warn "Self-signed certificate generated for development use only"
        warn "For production, run with --production --domain your-domain.com --email your-email@example.com"
    fi
}

# Run main function with all arguments
main "$@"