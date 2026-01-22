from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    require_admin,
    verify_password,
)
from backend.core.logger import LOG
from backend.database import get_db
from backend.database.models import User
from backend.models.auth import (
    AuthResponse,
    ChangePasswordRequest,
    CreateUserRequest,
    LoginRequest,
    UserInfo,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Routes
@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with username and password."""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if (
        not user
        or not user.password_hash
        or not verify_password(request.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})

    return AuthResponse(
        access_token=access_token,
        user=UserInfo(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            avatar_url=user.avatar_url,
            role=user.role,
            created_at=user.created_at,
            require_password_change=user.require_password_change or False,
        ),
    )


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user info."""
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        created_at=current_user.created_at,
        require_password_change=current_user.require_password_change or False,
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Change password."""
    if not current_user.require_password_change and request.old_password:
        if not current_user.password_hash or not verify_password(
            request.old_password, current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid old password"
            )

    current_user.password_hash = get_password_hash(request.new_password)
    current_user.require_password_change = False
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/users", response_model=UserInfo)
async def create_user(
    request: CreateUserRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a user."""
    # ensure we don't create a user that already exists
    if request.email:
        result = await db.execute(
            select(User).where(
                or_(User.username == request.username, User.email == request.email)
            )
        )
    else:
        request.email = None  # normalize empty email to None to prevent '' duplicates
        result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    # generate user
    new_user = User(
        username=request.username,
        password_hash=get_password_hash(request.password),
        email=request.email,
        display_name=request.username,
        role=request.role,
        require_password_change=request.require_password_change,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    LOG.info(f"Admin {admin.username} created user {new_user.username}")

    return UserInfo(
        id=new_user.id,
        username=new_user.username,
        display_name=new_user.display_name,
        email=new_user.email,
        avatar_url=new_user.avatar_url,
        role=new_user.role,
        created_at=new_user.created_at,
        require_password_change=new_user.require_password_change or False,
        # jellyfin_linked=False,
    )


@router.get("/users", response_model=list[UserInfo])
async def list_users(
    _admin: Annotated[User, Depends(require_admin)], db: AsyncSession = Depends(get_db)
):
    """Admin lists all users."""
    result = await db.execute(select(User))
    return [
        UserInfo(
            id=u.id,
            username=u.username,
            display_name=u.display_name,
            email=u.email,
            avatar_url=u.avatar_url,
            role=u.role,
            created_at=u.created_at,
            require_password_change=u.require_password_change or False,
        )
        for u in result.scalars()
    ]


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    """Admin deletes a user."""
    # prevent deleting own account
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # delete
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await db.delete(user)
    await db.commit()

    LOG.info(f"Admin {admin.username} deleted user {user.username}")

    return {"message": "User deleted successfully"}


# @router.post("/users/{user_id}/reset-password")
# async def reset_password(
#     user_id: int,
#     admin: Annotated[User, Depends(require_admin)],
#     db: AsyncSession = Depends(get_db),
# ):
#     """Admin resets user password."""
#     result = await db.execute(select(User).where(User.id == user_id))
#     user = result.scalar_one_or_none()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     import secrets

#     temp_password = secrets.token_urlsafe(12)

#     user.password_hash = get_password_hash(temp_password)
#     user.require_password_change = True
#     await db.commit()

#     LOG.info(f"Admin {admin.username} reset password for {user.username}")

#     return {
#         "message": "Password reset successfully",
#         "temporary_password": temp_password,
#     }


# @router.post("/link-jellyfin")
# async def link_jellyfin(
#     request: LinkJellyfinRequest,
#     current_user: Annotated[User, Depends(get_current_user)],
#     db: AsyncSession = Depends(get_db),
# ):
#     """Link Jellyfin account (optional)."""
#     result = await db.execute(
#         select(ServiceConfig).where(
#             ServiceConfig.service_type == Service.JELLYFIN,
#             ServiceConfig.enabled == True,
#         )
#     )
#     config = result.scalar_one_or_none()

#     if not config:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Jellyfin not configured",
#         )

#     try:
#         async with niquests.AsyncSession() as session:
#             response = await session.post(
#                 f"{config.base_url}/Users/AuthenticateByName",
#                 json={"Username": request.username, "Pw": request.password},
#                 headers={
#                     "Content-Type": "application/json",
#                     "X-Emby-Authorization": 'MediaBrowser Client="vacuumerr", Device="Web", DeviceId="vacuumerr", Version="1.0.0"',
#                 },
#             )
#             response.raise_for_status()
#             data = response.json()

#             current_user.jellyfin_id = data["User"]["Id"]
#             current_user.jellyfin_token = data["AccessToken"]
#             await db.commit()

#             return {"message": "Jellyfin linked successfully"}
#     except Exception as e:
#         LOG.error(f"Jellyfin linking failed: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid Jellyfin credentials",
#         )
