"""Thin client for the Tidbyt HTTP API (https://tidbyt.dev)."""

import base64
import json
import urllib.error
import urllib.request

API_BASE = "https://api.tidbyt.com/v0"


class TidbytError(RuntimeError):
    pass


def _request(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        raise TidbytError(f"Tidbyt API {method} {url} failed: {e.code} {detail}") from e
    except urllib.error.URLError as e:
        raise TidbytError(f"Could not reach Tidbyt API: {e.reason}") from e


def push(device_id, token, webp_bytes, installation_id=None, background=False):
    """Push an image to the device.

    Without an installation_id the image interrupts the rotation once.
    With one, it is also saved into the rotation (until deleted).
    background=True skips the immediate interruption.
    """
    body = {
        "image": base64.b64encode(webp_bytes).decode(),
        "background": background,
    }
    if installation_id:
        body["installationID"] = installation_id
    _request("POST", f"{API_BASE}/devices/{device_id}/push", token, body)


def delete_installation(device_id, token, installation_id):
    """Remove a pushed installation from the device's rotation."""
    _request(
        "DELETE",
        f"{API_BASE}/devices/{device_id}/installations/{installation_id}",
        token,
    )
