import hashlib
import re
import urllib.parse
from django.conf import settings
from django.core.signing import Signer, BadSignature
from .models import ShareEvent

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip

def hash_ip(ip: str) -> str:
    if not ip:
        return None
    salt = getattr(settings, 'ANALYTICS_IP_SALT', 'default_salt')
    # Use sha256 to securely hash
    return hashlib.sha256(f"{ip}:{salt}".encode('utf-8')).hexdigest()

def parse_user_agent(ua_string: str):
    """
    Very lightweight, dependency-free user-agent parser.
    Extracts coarse device_type, browser, and os.
    """
    if not ua_string:
        return None, None, None
    
    ua = ua_string.lower()
    
    # Device type
    if 'mobi' in ua or 'android' in ua or 'iphone' in ua:
        device_type = 'Mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'

    # Browser
    if 'edg' in ua:
        browser = 'Edge'
    elif 'chrome' in ua or 'crios' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua or 'fxios' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'opera' in ua or 'opr' in ua:
        browser = 'Opera'
    else:
        browser = 'Other'

    # OS
    if 'windows' in ua:
        os = 'Windows'
    elif 'mac os' in ua or 'macos' in ua:
        os = 'macOS'
    elif 'android' in ua:
        os = 'Android'
    elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
        os = 'iOS'
    elif 'linux' in ua:
        os = 'Linux'
    else:
        os = 'Other'

    return device_type, browser, os

def get_qr_signer():
    return Signer(key=getattr(settings, 'QR_ANALYTICS_SIGNING_SECRET', settings.SECRET_KEY))

def generate_qr_signature(qr_id: str, raw_token: str) -> str:
    signer = get_qr_signer()
    # Sign a canonical payload
    payload = f"{qr_id}.{raw_token}"
    return signer.sign(payload).split(':')[1] # just return the signature part

def verify_qr_signature(qr_id: str, raw_token: str, signature: str) -> bool:
    signer = get_qr_signer()
    payload = f"{qr_id}.{raw_token}"
    signed_value = f"{payload}:{signature}"
    try:
        signer.unsign(signed_value)
        return True
    except BadSignature:
        return False

def record_share_event(
    share_link,
    event_type: ShareEvent.EventType,
    request,
    qr_code=None,
    success: bool = True,
    metadata: dict = None
):
    """
    Records an analytics event robustly.
    Swallows exceptions to prevent breaking the core sharing flow.
    """
    try:
        ip = get_client_ip(request)
        hashed_ip = hash_ip(ip)

        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_type, browser, os_name = parse_user_agent(user_agent)

        referrer = request.META.get('HTTP_REFERER', '')
        # Sanitize referrer (just drop query params for privacy if needed, or store base)
        if referrer:
            parsed = urllib.parse.urlparse(referrer)
            referrer = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Geolocation isn't natively supported without a dependency (like GeoIP2), 
        # so we will leave it null as per requirement (do not introduce paid/external dependency unnecessarily).

        return ShareEvent.objects.create(
            share_link=share_link,
            file=share_link.file,
            qr_code=qr_code,
            event_type=event_type,
            ip_hash=hashed_ip,
            device_type=device_type,
            browser=browser,
            os=os_name,
            referrer=referrer[:1024] if referrer else None,
            success=success,
            metadata=metadata
        )
    except Exception as e:
        import logging
        logger = logging.getLogger('analytics')
        logger.error(f"Failed to record analytics event: {str(e)}")
        # Do not raise to avoid breaking the user flow
        return None
