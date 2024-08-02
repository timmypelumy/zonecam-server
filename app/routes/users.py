from fastapi import APIRouter, Query, Depends, Request, Form
from app.models.users import UserInput, User,  EmailVerifyOutput, AccessToken,  PasswordResetInput, PasswordResetStore, SessionInfo
from app.config.settings import get_settings
from app.database import cols
from app.utils.security import create_access_code, verify_access_code, scrypt_hash, scrypt_verify, create_access_token
from app.models.enums import OperationTypes
from app.tasks import creators
from app.utils.helpers import get_utc_timestamp
from fastapi.security import OAuth2PasswordRequestForm
from . import util
from datetime import datetime
from .deps import get_auth_user, retrieve_session

settings = get_settings()
router = APIRouter(tags=["Users"], prefix="/u")


@router.post("/session", response_model=SessionInfo)
async def fetch_session_info(token:  str = Form(alias="token", )):

    if not token or len(token) < 32:
        return SessionInfo(is_authenticated=False, error="Invalid token.")

    err, session = await retrieve_session(token)

    if err:

        return SessionInfo(is_authenticated=False, error=err)

    else:

        u = await cols.users.find_one({
            "uid":  session.user_id
        })

        if not u:

            return SessionInfo(is_authenticated=False, error="User not found")

        user = User(**u)

        return SessionInfo(user=user, session=session, is_authenticated=True)


@router.get("", response_model=User, )
async def get_authenticated_user(user:  User = Depends(get_auth_user)):

    return user


@ router.post("/sign-in", response_model=AccessToken)
async def log_in(req:  Request, body: OAuth2PasswordRequestForm = Depends(), device:  str | None = Query(None)):

    u = await util.fetch_user(body.username)

    if not u:
        util.raise_unauthorized("Invalid credentials.")

    email, name = util.fetch_email_and_name(u)

    user = User(**u)

    if not user.is_active:
        util.raise_forbidden_reqest(
            "Your account is not active, please contact support.")

    is_correct_password = False

    try:

        is_correct_password = scrypt_verify(
            body.password, user.password_hash, email)

    except Exception as e:

        util.debug_log(str(e))

        util.raise_server_error(
            "An error occured while processing your request.")

    else:

        if not is_correct_password:
            util.raise_unauthorized("Invalid credentials.")

        token = await create_access_token(user.uid)

        # creators.task_send_email(
        #     "sign_in_notification", email, {"first_name": name, "sign_in_time": str(datetime.now().strftime("%A, %B %d, %Y %I:%M %p")), "ip_address": req.client.host, "device":  device})

        return AccessToken(access_token=token)


@router.post("/password/reset", status_code=200)
async def password_reset(body:  PasswordResetInput):

    user = await util.fetch_user(body.email, body.user_type)

    # ignore the reset request of the user does not exist
    if user is None:
        util.debug_log("User not found.")
        return

    email, name = util.fetch_email_and_name(user)

    user = User(**user)

    if not user.email_verified:

        util.raise_forbidden_reqest(
            "Your email is not verified. Please verify your email.")

    if not user.is_active:
        util.raise_forbidden_reqest(
            "Your account is not active, please contact support.")

    err, hash = scrypt_hash(body.new_password, email)

    if err:
        util.raise_bad_reqest("Password reset failed.")

    reset_store = PasswordResetStore(
        user_id=user.uid, new_password_hash=hash,
    )

    # save store to db
    await cols.passwordresetstores.insert_one(reset_store.model_dump())

    token = reset_store.token

    # send email

    url = f"{settings.app_url}/password/confirm/{user.uid}:{token}:{body.user_type.value}"

    creators.task_send_email(
        "reset_password", email, {"reset_link": url, "first_name": name, })

    util.debug_log("URL: ", url)


@ router.post("/password/reset/complete", status_code=200)
async def complete_password_reset(uid:  str, token:  str):

    user = await util.fetch_user(uid,  is_uid=True)

    if user is None:
        util.raise_not_found("User not found")

    email, name = util.fetch_email_and_name(user)

    user = User(**user)

    if not user.email_verified:
        util.raise_forbidden_reqest("Your email is not verified.")

    if not user.is_active:
        util.raise_forbidden_reqest(
            "Your account is not active, please contact support.")

    reset_store = await cols.passwordresetstores.find_one({
        "user_id": user.uid, "token": token
    })

    if reset_store is None:
        util.raise_not_found("Reset token not found.")

    reset_store = PasswordResetStore(**reset_store)

    if reset_store.user_id != user.uid:
        util.raise_bad_reqest("This reset token is not for this user.")

    if not reset_store.valid:
        util.raise_bad_reqest("This reset token is no longer valid.")

    if get_utc_timestamp() > reset_store.created_at + (60 * 5):
        util.raise_bad_reqest("Reset token expired.")

    user.password_hash = reset_store.new_password_hash

    user.password_reset_at = get_utc_timestamp()

    await cols.users.update_one({"uid": user.uid}, {"$set": user.model_dump()})

    await cols.passwordresetstores.update_one({"uid": reset_store.uid}, {
        "$set": {"valid": False}
    })

    creators.task_send_email(
        "reset_password_complete", email, {})

    return


@ router.post("/email/verify/{rid}/{acuid}/complete", status_code=200)
async def email_verify_complete(rid:  str, acuid: str, code:  str, ):

    access_code_uid = acuid

    if not rid or not access_code_uid or not code:
        util.raise_bad_reqest("Invalid or broken verification link.")

    u = await util.fetch_user(rid)

    if not u:
        util.raise_bad_reqest("Account does not exist.")

    email, name = util.fetch_email_and_name(u)

    if not u:
        util.raise_bad_reqest("Account does not exist.")

    c = await cols.accesscodes.find_one({
        "uid":  access_code_uid
    })

    if not c:
        raise util.raise_bad_reqest("Invalid verification code.")

    if not (c["operation_type"] == OperationTypes.signup):
        util.raise_bad_reqest("Invalid data.")

    if not (c["resource_id"] == rid):
        util.raise_bad_reqest("Invalid data.")

    # confirm code

    try:
        totp, _ = await verify_access_code(access_code_uid)

        ref_code = totp.now()

        if not (ref_code == code):
            util.raise_bad_reqest("Invalid code.")

        await cols.accesscodes.update_one({"uid": c["uid"]}, {
            "$set": {
                "revoked":  True
            }
        })

        await cols.users.update_one({
            "uid": u["uid"],
        }, {
            "$set": {
                "is_active":  True,
                "email_verified":  True
            }
        })

        # send a welcome onboard email

        creators.task_send_email(
            "verify_email_complete", email, {
                "first_name": name
            })

        return

    except ValueError as e:
        util.raise_bad_reqest("Invalid code.")


@ router.post("/email/verify/{rid}/{acuid}", response_model=EmailVerifyOutput)
async def email_verify(rid:  str, acuid: str,):

    access_code_uid = acuid

    if not rid or not access_code_uid:
        util.raise_bad_reqest("Invalid or broken verification link.")

    u = await util.fetch_user(rid)

    if not u:
        util.raise_bad_reqest("Account does not exist.")

    if u["email_verified"]:
        util.raise_bad_reqest("Email is already verified.")

    email, _ = util.fetch_email_and_name(u)

    c = await cols.accesscodes.find_one({
        "uid":  access_code_uid
    })

    if not c:
        raise util.raise_bad_reqest("Verification is invalid.")

    if not (c["operation_type"] == OperationTypes.signup):
        raise util.raise_bad_reqest("Invalid data.")

    # send verification email again

    code, access_code_uid = await create_access_code(OperationTypes.signup, email)

    creators.task_send_email(
        "verify_email", email, {"code": code, })

    return EmailVerifyOutput(acuid=access_code_uid, rid=email)


@router.post("", status_code=201, response_model=EmailVerifyOutput)
async def register_new_user(body:  UserInput):

    existing_user = await cols.users.find_one({
        "email":  body.email
    })

    if existing_user:
        util.raise_bad_reqest(
            "The email address you entered has been registered already.")

    err, hash = scrypt_hash(body.password, body.email)

    if err:

        util.debug_log(err)

        util.raise_server_error(
            "An error occured while processing your request .")

    user = User(
        email=body.email,
        password_hash=hash,
        first_name=body.first_name,
        last_name=body.last_name,
        is_active=False,
        email_verified=False,
    )

    await cols.users.insert_one(user.model_dump())

    # send verification email

    code, access_code_uid = await create_access_code(OperationTypes.signup, body.email)

    creators.task_send_email(
        "verify_email", body.email, {"code": code, })

    return EmailVerifyOutput(acuid=access_code_uid, rid=body.email)


@router.get("/{uid}", response_model=User)
async def get_user(uid: str):

    util.raise_forbidden_reqest()

    user = await util.fetch_user(uid, is_uid=True)

    if not user:
        util.raise_not_found("User not found")

    return user
