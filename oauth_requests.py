import requests
import logging
import dotenv
import time
import os

import oauth_utils

# Read the environment variables and configure the environment
dotenv.load_dotenv()
app_config = {
    "CONSUMER_KEY": os.getenv("CONSUMER_KEY"),
    "SIGNATURE_KEY_FP": os.getenv("SIGNATURE_KEY_FP"),
    "ENCRYPTION_KEY_FP": os.getenv("ENCRYPTION_KEY_FP"),
    "DH_PRIME": os.getenv("DH_PRIME"),
    "DH_GENERATOR": int(os.getenv("DH_GENERATOR", default=2)),
    "REALM": os.getenv("REALM", default="limited_poa"),
}

# Helper functions


def send_oauth_request(
    request_method: str,
    request_url: str,
    oauth_token: str = None,
    live_session_token: str = None,
    extra_headers: dict[str, str] = None,
    request_params: dict[str, str] = None,
    signature_method: str = "HMAC-SHA256",
    prepend: str = None,
) -> requests.Response:
    headers = {
        "oauth_consumer_key": app_config["CONSUMER_KEY"],
        "oauth_nonce": oauth_utils.generate_oauth_nonce(),
        "oauth_signature_method": signature_method,
        "oauth_timestamp": oauth_utils.generate_request_timestamp(),
    }
    if oauth_token:
        headers.update({"oauth_token": oauth_token})
    if extra_headers:
        headers.update(extra_headers)
    base_string = oauth_utils.generate_base_string(
        request_method=request_method,
        request_url=request_url,
        request_headers=headers,
        request_params=request_params,
        prepend=prepend,
    )
    logging.info(
        msg={
            "message": "generated base string",
            "timestamp": time.time(),
            "details": {
                "base_string": base_string,
                "request_method": request_method,
                "request_url": request_url,
                "request_headers": headers,
                "request_params": request_params,
                "prepend": prepend,
            },
        }
    )
    if signature_method == "HMAC-SHA256":
        headers.update(
            {
                "oauth_signature": oauth_utils.generate_hmac_sha_256_signature(
                    base_string=base_string,
                    live_session_token=live_session_token,
                )
            }
        )
    else:
        headers.update(
            {
                "oauth_signature": oauth_utils.generate_rsa_sha_256_signature(
                    base_string=base_string,
                    private_signature_key=oauth_utils.read_private_key(
                        app_config["SIGNATURE_KEY_FP"]
                    ),
                )
            }
        )
    logging.info(
        msg={
            "message": "generated signature",
            "timestamp": time.time(),
            "details": {
                "signature": headers["oauth_signature"],
                "signature_method": signature_method,
            },
        }
    )
    response = requests.request(
        method=request_method,
        url=request_url,
        headers={
            "Authorization": oauth_utils.generate_authorization_header_string(
                request_data=headers,
                realm=app_config["REALM"],
            )
        },
        params=request_params,
        timeout=10,
    )
    logging.info(
        msg={
            "message": "sent oauth request",
            "timestamp": time.time(),
            "details": {
                "request_method": request_method,
                "request_url": response.request.url,
                "request_headers": response.request.headers,
                "request_body": response.request.body,
                "response_status_code": response.status_code,
                "response_error_message": response.text if not response.ok else None,
            },
        }
    )
    return response


# Authentication flow


def live_session_token(
    access_token: str,
    access_token_secret: str,
) -> tuple[str, int]:
    REQUEST_URL = "https://api.ibkr.com/v1/api/oauth/live_session_token"
    REQUEST_METHOD = "POST"
    ENCRYPTION_METHOD = "RSA-SHA256"
    dh_random = oauth_utils.generate_dh_random_bytes()
    dh_challenge = oauth_utils.generate_dh_challenge(
        dh_prime=app_config["DH_PRIME"],
        dh_generator=app_config["DH_GENERATOR"],
        dh_random=dh_random,
    )
    prepend = oauth_utils.calculate_live_session_token_prepend(
        access_token_secret,
        oauth_utils.read_private_key(
            app_config["ENCRYPTION_KEY_FP"],
        ),
    )
    response = send_oauth_request(
        request_method=REQUEST_METHOD,
        request_url=REQUEST_URL,
        oauth_token=access_token,
        signature_method=ENCRYPTION_METHOD,
        extra_headers={
            "diffie_hellman_challenge": dh_challenge,
        },
        prepend=prepend,
    )
    if not response.ok:
        raise Exception(f"Live session token request failed: {response.text}")
    response_data = response.json()
    lst_expires = response_data["live_session_token_expiration"]
    dh_response = response_data["diffie_hellman_response"]
    lst_signature = response_data["live_session_token_signature"]
    live_session_token = oauth_utils.calculate_live_session_token(
        dh_prime=app_config["DH_PRIME"],
        dh_random_value=dh_random,
        dh_response=dh_response,
        prepend=prepend,
    )
    if not oauth_utils.validate_live_session_token(
        live_session_token=live_session_token,
        live_session_token_signature=lst_signature,
        consumer_key=app_config["CONSUMER_KEY"],
    ):
        raise Exception("Live session token validation failed.")
    return live_session_token, lst_expires


# Session management


def init_brokerage_session(
    access_token: str, live_session_token: str
) -> requests.Response:
    params = {
        "compete": "true",
        "publish": "true",
    }
    return send_oauth_request(
        request_method="POST",
        request_url="https://api.ibkr.com/v1/api/iserver/auth/ssodh/init",
        oauth_token=access_token,
        live_session_token=live_session_token,
        request_params=params,
    )


def tickle(access_token: str, live_session_token: str) -> requests.Response:
    return send_oauth_request(
        request_method="POST",
        request_url="https://api.ibkr.com/v1/api/tickle",
        oauth_token=access_token,
        live_session_token=live_session_token,
    )


def auth_status(access_token: str, live_session_token: str) -> requests.Response:
    return send_oauth_request(
        request_method="GET",
        request_url="https://api.ibkr.com/v1/api/iserver/auth/status",
        oauth_token=access_token,
        live_session_token=live_session_token,
    )


def logout(access_token: str, live_session_token: str) -> requests.Response:
    return send_oauth_request(
        request_method="POST",
        request_url="https://api.ibkr.com/v1/api/logout",
        oauth_token=access_token,
        live_session_token=live_session_token,
    )


# Account information & management


def brokerage_accounts(access_token: str, live_session_token: str) -> requests.Response:
    return send_oauth_request(
        request_method="GET",
        request_url="https://api.ibkr.com/v1/api/iserver/accounts",
        oauth_token=access_token,
        live_session_token=live_session_token,
    )


# Portfolio information


def account_ledger(
    access_token: str, live_session_token: str, account_id: str
) -> requests.Response:
    return send_oauth_request(
        request_method="GET",
        request_url=f"https://api.ibkr.com/v1/api/account/{account_id}/ledger",
        oauth_token=access_token,
        live_session_token=live_session_token,
    )


def portfolio_accounts(access_token: str, live_session_token: str) -> requests.Response:
    return send_oauth_request(
        request_method="GET",
        request_url=f"https://api.ibkr.com/v1/api/portfolio/accounts",
        oauth_token=access_token,
        live_session_token=live_session_token,
    )


# Market data requests


def market_data_snapshot(
    access_token: str,
    live_session_token: str,
    conids: list[int],
    fields: list[int],
    since: int = 0,
) -> requests.Response:
    params = {
        "since": since,
        "conids": ",".join([str(conid) for conid in conids]),
        "fields": ",".join([str(field) for field in fields]),
    }
    return send_oauth_request(
        request_method="GET",
        request_url="https://api.ibkr.com/v1/api/iserver/marketdata/snapshot",
        oauth_token=access_token,
        live_session_token=live_session_token,
        request_params=params,
    )
