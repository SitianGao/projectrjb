"""真实账号认证与多课程切换 API。"""

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.response import ApiError, ok
from database import get_db
from services.auth_service import auth_service


router = APIRouter()
bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(LoginRequest):
    phone: str = ""


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class CourseCreateRequest(BaseModel):
    title: str
    goal: str = ""


class CourseUpdateRequest(BaseModel):
    title: Optional[str] = None
    goal: Optional[str] = None


def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise ApiError("UNAUTHORIZED", "请先登录", status_code=401)
    return auth_service.authenticate(db, credentials.credentials)


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return ok(auth_service.register(db, request.username, request.password, request.phone), "注册成功")


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    return ok(auth_service.login(db, request.username, request.password), "登录成功")


@router.get("/me")
async def me(user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(auth_service.serialize_user(db, user))


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    auth_service.logout(db, credentials.credentials)
    return ok({"logged_out": True}, "已退出登录")


@router.put("/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    return ok(auth_service.update_profile(db, user, request.model_dump(exclude_none=True)))


@router.put("/password")
async def change_password(
    request: PasswordChangeRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    auth_service.change_password(db, user, request.old_password, request.new_password)
    return ok({"changed": True}, "密码已修改")


@router.get("/courses")
async def list_courses(user=Depends(require_user), db: Session = Depends(get_db)):
    return ok(auth_service.serialize_user(db, user))


@router.post("/courses")
async def create_course(
    request: CourseCreateRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    return ok(auth_service.create_course(db, user, request.title, request.goal), "课程已创建并切换")


@router.post("/courses/{course_id}/activate")
async def activate_course(
    course_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    return ok(auth_service.activate_course(db, user, course_id), "课程已切换")


@router.get("/courses/{course_id}/dashboard")
async def get_course_dashboard(
    course_id: str,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    return ok(auth_service.get_course_dashboard(db, user, course_id))


@router.put("/courses/{course_id}")
async def update_course(
    course_id: str,
    request: CourseUpdateRequest,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    if request.title is None and request.goal is None:
        raise ApiError("VALIDATION_ERROR", "课程名称和目标不能同时为空")
    return ok(
        auth_service.update_course(
            db,
            user,
            course_id,
            title=request.title,
            goal=request.goal,
        ),
        "课程信息已更新",
    )
