from fastapi import HTTPException, Request, status


def get_token(request: Request) -> str:
    """
    Extracts the Bearer token from the Authorization header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token"
        )
    return auth_header.split("Bearer ")[1]
