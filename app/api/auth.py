from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
from jose import JWTError, jwt

from app.db.database import get_db
from app.db import crud, models
from app.schemas import user as user_schemas
from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

# Helper function to get current user from cookie
async def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
):
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None

        # Get the user from database
        user = crud.get_user_by_email(db, email)
        return user
    except JWTError:
        return None
    except Exception as e:
        print(f"Error getting user from cookie: {e}")
        return None


@router.post("/login", response_model=user_schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint for API access"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    crud.update_last_login(db, user.id)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/login-form")
async def login_form_redirect(request: Request):
    """Redirect from /api/auth/login-form to /login"""
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/login-form")
async def login_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Login endpoint for form submission"""
    # Authenticate user
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password", "next": next}
        )

    # Update last login time
    crud.update_last_login(db, user.id)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    # Create response
    if user.first_login:
        # If first login, redirect to change password page
        response = RedirectResponse(url="/change-password", status_code=status.HTTP_303_SEE_OTHER)
    else:
        # Otherwise, redirect to next page or home page
        redirect_url = next if next else "/"
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    # Set cookie with token (same for both cases)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"  # Helps with CSRF protection
    )

    return response


@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Get the current user from the cookie
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        # Extract the token
        token = token[7:]  # Remove "Bearer " prefix

        # Get the user from the token
        from jose import jwt
        from app.core.auth import SECRET_KEY, ALGORITHM

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

        # Get the user from the database
        current_user = crud.get_user_by_email(db, email)
        if not current_user:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

        # Check if new password and confirmation match
        if new_password != confirm_password:
            return templates.TemplateResponse(
                "change_password.html",
                {
                    "request": request,
                    "user": current_user,
                    "first_login": current_user.first_login,
                    "error": "New password and confirmation do not match"
                }
            )

        # Verify current password
        user = authenticate_user(db, current_user.email, current_password)
        if not user:
            # Return to the change password page with an error
            return templates.TemplateResponse(
                "change_password.html",
                {
                    "request": request,
                    "user": current_user,
                    "first_login": current_user.first_login,
                    "error": "Current password is incorrect"
                }
            )

        # Update password
        updated_user = crud.update_password(db, current_user.id, new_password)
        if not updated_user:
            # Return to the change password page with an error
            return templates.TemplateResponse(
                "change_password.html",
                {
                    "request": request,
                    "user": current_user,
                    "first_login": current_user.first_login,
                    "error": "Failed to update password"
                }
            )

        # Create a new access token for the user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": current_user.email, "role": current_user.role},
            expires_delta=access_token_expires
        )

        # Redirect to home page
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        # Set the new token in the cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"  # Helps with CSRF protection
        )

        return response

    except Exception as e:
        print(f"Error in change_password: {e}")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
@router.get("/logout")
async def logout():
    """Logout endpoint"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response


# Admin user management endpoints

@router.post("/users", response_model=user_schemas.UserResponse)
async def create_user(
    user: user_schemas.UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db)
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Admin privileges required."
            )

        # Check if email already exists
        db_user = crud.get_user_by_email(db, user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        print(f"Creating user with data: {user.dict()}")

        # Create user
        new_user = crud.create_user(db, user.dict())
        print(f"User created: {new_user.id} - {new_user.email}")
        return new_user
    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.get("/users", response_model=List[user_schemas.UserResponse])
async def get_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db)
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Admin privileges required."
            )

        print("Fetching all users")
        users = crud.get_all_users(db, skip=skip, limit=limit)
        print(f"Found {len(users)} users")
        return users
    except Exception as e:
        print(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=user_schemas.UserResponse)
async def get_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get a specific user (admin only)"""
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db)
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Admin privileges required."
            )

        print(f"Fetching user with ID: {user_id}")
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        print(f"Found user: {user.id} - {user.email}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user: {str(e)}"
        )


@router.put("/users/{user_id}", response_model=user_schemas.UserResponse)
async def update_user(
    user_id: int,
    user_data: user_schemas.UserUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update a user (admin only)"""
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db)
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Admin privileges required."
            )

        print(f"Updating user with ID: {user_id}, Data: {user_data.dict(exclude_unset=True)}")

        # Check if email already exists (if email is being updated)
        if user_data.email and user_data.email != current_user.email:
            existing_user = crud.get_user_by_email(db, user_data.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered to another user"
                )

        updated_user = crud.update_user(db, user_id, user_data.dict(exclude_unset=True))
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        print(f"User updated: {updated_user.id} - {updated_user.email}")
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    try:
        # Get current user from cookie
        current_user = await get_current_user_from_cookie(request, db)
        if not current_user or current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Admin privileges required."
            )

        print(f"Attempting to delete user with ID: {user_id}")

        # Prevent deleting yourself
        if current_user.id == int(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        # Check if user exists
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        result = crud.delete_user(db, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )

        print(f"User deleted successfully: {user_id}")
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )
