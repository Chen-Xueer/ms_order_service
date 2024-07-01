from flask import request
from functools import wraps
from jose import jwt, jwk
from jose.utils import base64url_decode
from typing import Tuple, Optional
import urllib.request
import json
import time
import os

CUSTOM_PERMISSION = "custom:permission"
region = os.getenv('AWS_REGION')
password = os.getenv('POSTGRES_PASSWORD')
user_pool_id = os.getenv('USER_POOL_ID')
app_client_id = os.getenv('APP_CLIENT_ID')


def permission_required(site: str = "", role: str = "", permission: str = ""):

    def permission_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get("Authorization", None)
            if token is None:
                return {"error": "Authorization header missing"}, 401

            try:
                public_key = _get_cognito_public_key(token)
                jwt.decode(token, public_key, algorithms=[
                    "RS256"], audience=app_client_id, options={"verify_at_hash": False},)

                if permission is not None and len(permission) > 0:
                    claims = decode_token(token)
                    permissions = claims.get(CUSTOM_PERMISSION)
                    if permissions is None or permission not in permissions:
                        return {"error": "No permission to access api"}, 401

            except Exception as e:
                return {"error": str(e)}, 401

            return f(*args, **kwargs)

        return decorated

    return permission_required


def decode_token(token):
    return jwt.get_unverified_claims(token)


def _get_cognito_public_key(
        token: str) -> Tuple[dict, Optional[str]]:

    keys_url = (
        "https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json".format(
            region, user_pool_id
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
        claims.get("aud") != app_client_id
    ):
        raise Exception("Token was not issued for this client")

    return keys[key_index]
