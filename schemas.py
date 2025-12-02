from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# User Schemas (読み取り専用モデル用)
class UserBase(BaseModel):
    email: str = Field(..., title="メールアドレス", max_length=64)
    name: str = Field(..., title="氏名", max_length=64)
    ms_email: Optional[str] = Field(None, title="Microsoftメールアドレス", max_length=128)
    ms_id: Optional[str] = Field(None, title="Microsoft ID", max_length=128)


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# Ship Schemas (読み取り専用モデル用)
class ShipBase(BaseModel):
    name: Optional[str] = Field(..., title="船名", max_length=128)
    ex_name: Optional[str] = Field(None, title="旧船名", max_length=128)
    former_name: Optional[str] = Field(None, title="元船名", max_length=128)
    yard: Optional[str] = Field(None, title="建造所", max_length=128)
    ship_no: Optional[str] = Field(None,title="船番", max_length=128)
    delivered: Optional[datetime] = Field(None, title="就航日")
    issued_Inscert: Optional[datetime] = Field(None, title="就航日")
    expiry_date: Optional[datetime] = Field(None, title="定期検査期限")
    gross_tonn: Optional[float] = Field(None, title="総トン数")
    operte_section_id: Optional[int] = None
    navigation_area_id: Optional[int] = None
    deck_Categories: Optional[str] = Field(None, max_length=32)
    recent_dock: Optional[datetime] = Field(None, title="入渠完了（直近）")
    mmsi: Optional[str] = Field(None, title="MMSI番号", max_length=32)
    shipid: Optional[str] = Field(None, title="MarineTraffic-船ID", max_length=32)


class Ship(ShipBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# Role Schemas (読み取り専用モデル用)
class RoleBase(BaseModel):
    name: str = Field(..., max_length=128)
    description: Optional[str] = Field(None, max_length=255)


class Role(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime

# UserHasRoles Schemas (読み取り専用モデル用)
class UserHasRolesBase(BaseModel):
    user_id: int
    role_id: int

class UserHasRoles(UserHasRolesBase):
    model_config = ConfigDict(from_attributes=True)
	
    id: int
    created_at: datetime
    updated_at: datetime
    

# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., title="プロジェクト名", max_length=255)
    discription: Optional[str] = Field(None, title="説明")
    ship_id: Optional[int] = Field(None, title="船ID")
    owner_id: int = Field(..., title="プロジェクトオーナーID")
    dock: Optional[bool] = Field(None, title="入渠プロジェクトor not")
    yard: Optional[str] = Field(None, title="造船所", max_length=128)
    dock_in_date: Optional[datetime] = Field(None, title="入渠開始日")
    dock_out_date: Optional[datetime] = Field(None, title="入渠終了日")
    yard_decision: Optional[bool] = Field(None, title="造船所決定")
    date_decision: Optional[bool] = Field(None, title="日付決定")
    completion: Optional[datetime] = Field(None, title="完了日")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    discription: Optional[str] = None
    ship_id: Optional[int] = None
    dock: Optional[bool] = None
    yard: Optional[str] = Field(None, max_length=128)
    dock_in_date: Optional[datetime] = None
    dock_out_date: Optional[datetime] = None
    yard_decision: Optional[bool] = None
    date_decision: Optional[bool] = None
    completion: Optional[datetime] = None


class ProjectInDB(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# ProjectAssignment Schemas
class ProjectAssignmentBase(BaseModel):
    user_id: int
    project_id: int


class ProjectAssignmentCreate(ProjectAssignmentBase):
    pass


class ProjectAssignmentInDB(ProjectAssignmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# Task Schemas
class TaskBase(BaseModel):
    project_id: int = Field(..., title="プロジェクトID")
    name: str = Field(..., title="タスク名", max_length=255)
    discription: Optional[str] = Field(None, title="説明")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    discription: Optional[str] = None


class TaskInDB(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    
    task_number: int
    created_at: datetime
    updated_at: datetime


# Todo Schemas
class TodoBase(BaseModel):
    project_id: int = Field(..., title="プロジェクトID")
    task_number: int = Field(..., title="タスク番号")
    description: str = Field(..., title="説明", max_length=512)
    start: Optional[datetime] = Field(None, title="開始日時")
    is_completed: Optional[datetime] = Field(None, title="完了日時")


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    description: Optional[str] = None
    start: Optional[datetime] = None
    is_completed: Optional[datetime] = None


class TodoInDB(TodoBase):
    model_config = ConfigDict(from_attributes=True)
    
    todo_number: int
    created_at: datetime
    updated_at: datetime


# TaskAssignment Schemas
class TaskAssignmentBase(BaseModel):
    user_id: int
    project_id: int
    task_number: int


class TaskAssignmentCreate(TaskAssignmentBase):
    pass


class TaskAssignmentInDB(TaskAssignmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# TodoAssignment Schemas
class TodoAssignmentBase(BaseModel):
    user_id: int
    project_id: int
    task_number: int
    todo_number: int


class TodoAssignmentCreate(TodoAssignmentBase):
    pass


class TodoAssignmentInDB(TodoAssignmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# TaskAttachment Schemas
class TaskAttachmentBase(BaseModel):
    project_id: int
    task_number: int
    user_id: int
    file_id: str = Field(..., max_length=255)
    directory_id: str = Field(..., max_length=255)
    originname: str = Field(..., max_length=128)
    title: str = Field(..., max_length=128)
    icon: str = Field(..., max_length=128)


class TaskAttachmentCreate(TaskAttachmentBase):
    pass


class TaskAttachmentInDB(TaskAttachmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# TodoAttachment Schemas
class TodoAttachmentBase(BaseModel):
    project_id: int
    task_number: int
    todo_number: int
    user_id: int
    file_id: str = Field(..., max_length=255)
    originname: str = Field(..., max_length=128)
    title: str = Field(..., max_length=128)


class TodoAttachmentCreate(TodoAttachmentBase):
    directory_id: Optional[str] = Field(None, max_length=255)
    icon: Optional[str] = Field(None, max_length=128)


class TodoAttachmentInDB(TodoAttachmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    directory_id: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# TaskComment Schemas
class TaskCommentBase(BaseModel):
    project_id: int = Field(..., title="プロジェクトID")
    task_number: int = Field(..., title="タスク番号")
    user_id: int = Field(..., title="コメント入力者ID")
    content: str = Field(..., title="コメント")


class TaskCommentCreate(TaskCommentBase):
    pass


class TaskCommentInDB(TaskCommentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# TodoComment Schemas
class TodoCommentBase(BaseModel):
    project_id: int
    task_number: int
    todo_number: int
    user_id: int
    content: str


class TodoCommentCreate(TodoCommentBase):
    pass


class TodoCommentInDB(TodoCommentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# ProjectPhoto Schemas
class ProjectPhotoBase(BaseModel):
    project_id: int = Field(..., title="プロジェクトID")
    user_id: int = Field(..., title="ユーザID")
    file_id: str = Field(..., title="ファイルID", max_length=255)
    task_number: Optional[int] = None
    todo_number: Optional[int] = None
    category: Optional[str] = Field(None, title="カテゴリ", max_length=128)
    description: Optional[str] = Field(None, title="説明", max_length=512)


class ProjectPhotoCreate(ProjectPhotoBase):
    pass


class ProjectPhotoInDB(ProjectPhotoBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
