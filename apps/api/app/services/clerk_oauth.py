"""Clerk session-JWT verification against the Clerk JWKS endpoint.

No Clerk SDK is used: verification is done with the existing ``pyjwt``
dependency. ``jwt.PyJWKClient`` fetches and caches the JWKS internally,
so no manual cache handling is required here.

Expected Clerk JWKS URL pattern (documented in ``docs/prod.md``)::

    https://<clerk-frontend-api-domain>/.well-known/jwks.json

The expected token issuer is derived from that URL by stripping the
``/.well-known/jwks.json`` suffix, e.g.::

    JWKS URL: https://spiffy-panda-12.clerk.accounts.dev/.well-known/jwks.json
    Issuer:   https://spiffy-panda-12.clerk.accounts.dev
"""

from functools import lru_cache

import jwt
from fastapi import HTTPException, status

from app.config import settings

JWKS_SUFFIX = "/.well-known/jwks.json"

# Claim keys probed (in order) for the verified email address. Clerk's
# default session token does not carry an email claim, so deployments must
# configure a custom JWT template that includes one (see docs/prod.md).
# Several common template key names are accepted.
EMAIL_CLAIM_KEYS = ("email", "primary_email", "email_address")

# Claim keys probed (in order) for the email-verified flag. The flag MUST be
# present and true: a missing flag or an explicit false means the email is
# unverified and the token is rejected (401 OAUTH_EMAIL_UNVERIFIED). This
# blocks account takeover via a Clerk account holding a victim's unverified
# email address. Template snippet in docs/prod.md includes this flag.
EMAIL_VERIFIED_CLAIM_KEYS = ("email_verified", "emailVerified", "verified_email")


def expected_issuer(jwks_url: str | None = None) -> str:
    """Derive the expected ``iss`` claim from the Clerk JWKS URL."""
    base = (jwks_url if jwks_url is not None else settings.clerk_jwks_url).strip()
    if base.endswith(JWKS_SUFFIX):
        return base[: -len(JWKS_SUFFIX)]
    return base.rstrip("/")


@lru_cache(maxsize=8)
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url)


def verify_clerk_session_token(token: str) -> dict:
    """Verify a Clerk session JWT and return its verified identity claims.

    Returns ``{"clerk_id": ..., "email": ..., "display_name": ...}`` where
    ``clerk_id`` is the Clerk user id (``sub`` claim) and ``email`` is the
    verified email address from the token claims.

    Raises ``HTTPException`` 401 when the token is invalid, expired, carries
    no usable email claim, or carries no (or a false) email-verified flag.
    """
    jwks_url = settings.clerk_jwks_url.strip()
    try:
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token).key
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "OAUTH_INVALID_TOKEN",
                "message": "Could not verify Clerk session token.",
            },
        ) from err

    decode_kwargs: dict = {
        "algorithms": ["RS256"],
        "issuer": expected_issuer(jwks_url),
        "options": {"require": ["exp", "iss", "sub"]},
    }
    if settings.clerk_audience.strip():
        decode_kwargs["audience"] = settings.clerk_audience.strip()

    try:
        claims = jwt.decode(token, signing_key, **decode_kwargs)
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "OAUTH_TOKEN_EXPIRED", "message": "Clerk session has expired."},
        ) from err
    except jwt.PyJWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "OAUTH_INVALID_TOKEN",
                "message": "Could not verify Clerk session token.",
            },
        ) from err

    clerk_id = claims.get("sub")
    email = None
    for key in EMAIL_CLAIM_KEYS:
        value = claims.get(key)
        if isinstance(value, str) and value.strip():
            email = value.strip().lower()
            break

    if not clerk_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "OAUTH_EMAIL_MISSING",
                "message": "Clerk token is valid but carries no email claim. "
                "Configure a Clerk JWT template that includes the user's email.",
            },
        )

    # Require a verified-email flag: reject when absent or present-and-false.
    # Without this, an attacker could create a Clerk account with a victim's
    # email address and take over the linked Merit row.
    email_verified: bool | None = None
    for key in EMAIL_VERIFIED_CLAIM_KEYS:
        if key in claims:
            value = claims[key]
            if isinstance(value, bool):
                email_verified = value
            elif isinstance(value, (int, float)):
                email_verified = bool(value)
            elif isinstance(value, str):
                email_verified = value.strip().lower() in (
                    "true",
                    "1",
                    "yes",
                    "verified",
                )
            elif value is None:
                email_verified = False
            else:
                email_verified = bool(value)
            break

    if email_verified is not True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "OAUTH_EMAIL_UNVERIFIED",
                "message": "Clerk token email is not verified. "
                "Configure a Clerk JWT template that includes the email-verified flag.",
            },
        )

    display_name = (
        claims.get("name")
        or claims.get("username")
        or claims.get("given_name")
        or email.split("@")[0]
    )
    return {"clerk_id": clerk_id, "email": email, "display_name": str(display_name).strip()}
