from fastapi import HTTPException

from database import UserGroupEnum, UserModel


def check_admin_or_moderator(user: UserModel):
    if user.group.name not in {UserGroupEnum.ADMIN, UserGroupEnum.MODERATOR}:
        raise HTTPException(
            status_code=403,
            detail="Only admins and moderators can create or update movies",
        )
