# isort: skip_file

from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_jwt_auth_manager
from database import UserModel
from dependencies.database_session import get_db
from security.interfaces import JWTAuthManagerInterface

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Security(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = jwt_manager.decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: int = payload.get("user_id")
    if not user_id:
        raise credentials_exception

    result = await db.execute(select(UserModel).filter(UserModel.id == user_id))
    user = result.scalars().first()
    if not user:
        raise credentials_exception

    return user
