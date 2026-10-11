from urllib.parse import urlparse

class SecurityError(Exception):
    pass

def validate_repository_url(url: str) -> str:
    """
    Validate repository URL to prevent SSRF, path traversal, 
    and execution of unsafe schemes.
    Raises SecurityError if validation fails.
    """
    if not url:
        raise SecurityError("Repository URL cannot be empty.")
        
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise SecurityError(f"Malformed URL: {str(e)}")

    if parsed.scheme not in ["https", "demo"]:
        raise SecurityError("Only HTTPS and demo protocols are supported.")
        
    if parsed.username or parsed.password:
        raise SecurityError("Embedded credentials in URL are not allowed.")
        
    hostname = parsed.hostname
    if parsed.scheme != "demo" and not hostname:
        raise SecurityError("URL must contain a valid hostname.")
        
    import ipaddress
    try:
        # If it's a direct IP, block private ranges
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise SecurityError("Private, loopback, and link-local IP addresses are blocked.")
    except ValueError:
        # Not an IP address, check for common localhost names
        pass
        
    blocked_hosts = {"localhost", "metadata.google.internal"}
    if hostname and hostname.lower() in blocked_hosts:
        raise SecurityError("Blocked internal hostname.")
        
    return url
