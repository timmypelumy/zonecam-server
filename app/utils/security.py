from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidKey
from app.config.settings import get_settings
from cryptography.fernet import MultiFernet, Fernet
from app.database import cols as db
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from app.models.users import AuthSession, AccessCode
from .helpers import get_uuid4
from datetime import datetime, timedelta, timezone
from app.models.enums import OperationTypes
import jwt
import base64
import binascii
import pyotp


settings = get_settings()


# Function to encode a string to Base64
def encode_to_base64(input_string):
    encoded_bytes = base64.b64encode(input_string.encode())
    return encoded_bytes.decode()

# Function to decode a Base64 string to the original string


def decode_from_base64(encoded_string: str):
    decoded_bytes = base64.b64decode(encoded_string.encode())
    try:
        decoded_str = decoded_bytes.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        decoded_str = "Error: Invalid UTF-8 data"
    return decoded_str


def decode_jwt_token(token: str):

    try:

        decoded = jwt.decode(token, settings.jwt_secret, algorithms='HS256',
                             issuer=settings.app_name, options={"require": ["exp", "iss", "sub", "iat"]})

        return decoded

    except jwt.exceptions.ExpiredSignatureError as e:
        raise ValueError("unauthenticated request : expired token")

    except jwt.exceptions.InvalidAudienceError as e:
        raise ValueError("unauthenticated request : invalid audience")

    except jwt.exceptions.InvalidIssuerError as e:
        raise ValueError("unauthenticated request : invalid issuer")

    except jwt.exceptions.DecodeError as e:
        raise ValueError("unauthenticated request : decode error")

    except Exception as e:
        raise ValueError(f"unauthenticated request : {str(e)}")


async def create_access_token(user_id: str):

    session_id = get_uuid4()

    payload = {
        "sub": {

            "user_id": user_id,
            "session_id": session_id,
        },
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=settings.jwt_exp),
        "iss":  settings.app_name,
        "iat": datetime.now(tz=timezone.utc)
    }

    _token = jwt.encode(payload, settings.jwt_secret, algorithm='HS256')

    authsession = AuthSession(uid=session_id, user_id=user_id,
                              duration_in_hours=settings.jwt_exp)

    await db.sessions.insert_one(authsession.model_dump())

    return _token


def scrypt_hash(password: str, salt: str, n: int = 2 ** 14, r: int = 8, p: int = 1,):

    try:

        kdf = Scrypt(
            salt=(salt + settings.password_salt).encode(),
            length=32,
            n=n, r=r, p=p
        )

        return None, base64.encodebytes(kdf.derive(password.encode())).decode()

    except Exception as e:
        return str(e), None


def scrypt_verify(guessed_password: str,  expected_hash: str, salt: str, n: int = 2 ** 14, r: int = 8, p: int = 1,):

    try:

        kdf = Scrypt(
            salt=(salt + settings.password_salt).encode(),
            length=32,
            n=n, r=r, p=p
        )

        kdf.verify(guessed_password.encode(),
                   base64.decodebytes(expected_hash.encode()))

        return True

    except InvalidKey:
        return False

    except Exception as e:
        raise ValueError(str(e))


def sha256(message: str) -> str:

    digest = hashes.Hash(hashes.SHA256())
    digest.update(message.encode())
    _bytes = digest.finalize()
    return base64.b64encode(_bytes).decode()


def encrypt_string(message: str) -> str:

    keys = [settings.key1, settings.key2, ]
    f = MultiFernet(Fernet(sha256(x)) for x in keys)
    cipher_text = f.encrypt(message.encode())
    hex_encoded = binascii.hexlify(cipher_text).decode()

    return hex_encoded


def decrypt_string(hex_encoded: str) -> str:

    cipher_text = binascii.unhexlify(hex_encoded.encode())

    keys = [settings.key1, settings.key2, ]
    f = MultiFernet(Fernet(sha256(x)) for x in keys)
    message = f.decrypt(cipher_text).decode()

    return message


async def create_access_code(operation_type: OperationTypes, resource_id:  str):

    # clear existing matches

    await db.accesscodes.delete_many({
        "operation_type": operation_type, "resource_id": resource_id
    })

    key = pyotp.random_base32()

    totp = pyotp.TOTP(key, interval=settings.code_duration,
                      digits=settings.code_length, )
    encrypted_key = base64.encodebytes(encrypt_string(key).encode()).decode()

    access_code = AccessCode(
        key=encrypted_key, operation_type=operation_type, resource_id=resource_id)

    access_code_dict = access_code.model_dump()

    await db.accesscodes.insert_one(access_code_dict)

    return totp.now(), access_code.uid


async def verify_access_code(access_code_uid:  str):

    access_code_dict = await db.accesscodes.find_one({"uid": access_code_uid})

    if not access_code_dict:
        raise ValueError("Invalid code")

    if access_code_dict["revoked"]:
        raise ValueError("Revoked, please request a new code")

    decrypted_key = decrypt_string(base64.decodebytes(
        access_code_dict["key"].encode()).decode())

    totp = pyotp.TOTP(decrypted_key, interval=settings.code_duration,
                      digits=settings.code_length)

    return totp, access_code_dict
