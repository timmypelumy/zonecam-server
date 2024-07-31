from fastapi import Depends, HTTPException, BackgroundTasks
from app.models.users import User,  AuthSession
from app.database import cols
from app.config.settings import get_settings
from app.utils.security import decode_jwt_token
from fastapi.security import OAuth2PasswordBearer
from app.utils.helpers import get_utc_timestamp
from datetime import datetime, timedelta, timezone


settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/u/sign-in")


async def retrieve_session(token:  str) -> AuthSession:

    try:
        data = decode_jwt_token(token)

        user = await cols.users.find_one({
            "uid":  data["sub"]["user_id"]
        })

        session = await cols.sessions.find_one({
            "uid":  data["sub"]["session_id"]
        })

        if not user or not session:
            return "Invalid session", None

        user = User(**user)
        session = AuthSession(**session)

        if user.uid != session.user_id:

            return "Invalid session", None

        if session.revoked:

            return "Session revoked", None

        return None, session

    except Exception as e:
        return str(e), None


async def get_auth_user(bg_tasks: BackgroundTasks, token: str = Depends(oauth2_scheme)) -> User:

    err, session = await retrieve_session(token)

    if err:
        raise HTTPException(401, err)

    user = await cols.users.find_one({
        "uid":  session.user_id
    })

    session_created = datetime.fromtimestamp(session.created_at, timezone.utc)
    utc_now = datetime.now(tz=timezone.utc)

    if utc_now >= session_created + timedelta(hours=session.duration_in_hours):
        raise HTTPException(401, "Session expired")

    session.last_used = get_utc_timestamp()
    session.usage_count += 1

    async def make_update(uid, last_used, usage_count):

        await cols.sessions.update_one(
            {"uid": uid}, {"$set": {"last_used": last_used, "usage_count": usage_count}})

    bg_tasks.add_task(make_update, session.uid,
                      session.last_used, session.usage_count)

    user = User(**user)

    return user
