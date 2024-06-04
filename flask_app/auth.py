import json
import time
import urllib.request
from datetime import datetime
from jose import jwk, jwt
from jose.utils import base64url_decode
from flask import current_app as app
from microservice_utils.settings import logger
from typing import Tuple, Optional
from sqlalchemy import and_, or_, true, false
from flask.wrappers import Request
from microservice_utils.auth import authorization_wrap


def get_condition(condition: bool):
    if condition:
        return true()
    return false()


def _get_cognito_public_key(
    token: str, tenant_id: Optional[str]
) -> Tuple[dict, str, Optional[str]]:
    region = app.config["AWS_REGION"]

    payload = jwt.get_unverified_claims(token)
    userpool_id = str(payload["iss"]).split("/")[-1]

    # https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_a0lPcksMV/.well-known/jwks.json
    keys_url = (
        "https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json".format(
            region, userpool_id
        )
    )

    with urllib.request.urlopen(keys_url) as f:
        response = f.read()
    keys = json.loads(response.decode("utf-8"))["keys"]

    # get the kid from the headers prior to verification
    headers = jwt.get_unverified_headers(token)
    kid = headers["kid"]
    # search for the kid in the downloaded public keys
    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]["kid"]:
            key_index = i
            break
    if key_index == -1:
        raise Exception("Public key not found in jwks.json")

    # construct the public key
    public_key = jwk.construct(keys[key_index])
    # get the last two sections of the token,
    # message and signature (encoded in base64)
    message, encoded_signature = str(token).rsplit(".", 1)
    # decode the signature
    decoded_signature = base64url_decode(encoded_signature.encode("utf-8"))
    # verify the signature
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        raise Exception("Signature verification failed")

    # Signature successfully verified

    # since we passed the verification, we can now safely
    # use the unverified claims
    claims = jwt.get_unverified_claims(token)
    # additionally we can verify the token expiration
    if time.time() > claims["exp"]:
        raise Exception("Token is expired")

    # and the Audience  (use claims['client_id'] if verifying an access token)
    if (
        claims.get("aud") != tenant_id.ev_user_pool_client_id
        and claims.get("client_id") != tenant_id.ev_user_pool_client_id
    ):
        raise Exception("Token was not issued for this audience")

    return keys[key_index], tenant_id.tenant_id, tenant_id.ev_user_pool_client_id


def decode_token(token):
    return jwt.get_unverified_claims(token)


def token_callback(request: Request, token: str) -> None:

    tenant_id = None
    data: Optional[dict[str, str]] = request.json
    if data is not None:
        tenant_id = data.get("tenant_id", None)

    claims = decode_token(token)

    public_key, tenant_id, client_id = _get_cognito_public_key(
        token, tenant_id
    )
    jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=client_id,
        options={"verify_at_hash": False},
    )

    try:
        if (
            request.json is not None
            and request.json.get("tenant_id", None) is None
        ):
            request.json["tenant_id"] = tenant_id
            request.json["user_sub"] = claims["sub"]

    except Exception as e:
        logger.error(str(e))

    return None


token_required = authorization_wrap(token_callback)