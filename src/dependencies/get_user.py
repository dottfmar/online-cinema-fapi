from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_jwt_auth_manager
from database import UserModel
from dependencies.database_session import get_db
from security.interfaces import JWTAuthManagerInterface

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/")


# async def get_current_user(
#         token: str = Depends(get_token),  # Використовуємо get_token замість OAuth2PasswordBearer
#         db: AsyncSession = Depends(get_db),
#         jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
# ) -> UserModel:
#     try:
#         payload = jwt_manager.decode_access_token(token)
#         token_user_id = payload.get("user_id")
#         if not token_user_id:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
#     except BaseSecurityError as e:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
#
#     stmt = select(UserModel).where(UserModel.id == token_user_id)
#     result = await db.execute(stmt)
#     user = result.scalars().first()
#
#     if not user or not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found or not active.",
#         )
#     return user


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

    # Декодируем токен и извлекаем payload
    payload = jwt_manager.decode_access_token(token)
    if not payload:
        raise credentials_exception

    # Извлекаем email из payload
    email: str = payload.get("email")
    if not email:
        raise credentials_exception

    # Запрос к базе данных для нахождения пользователя
    result = await db.execute(select(UserModel).filter(UserModel.email == email))
    user = result.scalars().first()
    if not user:
        raise credentials_exception

    return user
