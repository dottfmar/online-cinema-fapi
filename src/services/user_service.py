from fastapi import HTTPException, status

from database import UserModel


async def check_admin_or_moderator(current_user: UserModel):
    if current_user.group_id not in (2, 3):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
