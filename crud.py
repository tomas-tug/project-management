from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from models import (
    User, Role, UserHasRoles, Ship,
    Project, ProjectAssignment, Task, Todo,
    TaskAssignment, TodoAssignment,
    TaskAttachment, TodoAttachment,
    TaskComment, TodoComment, ProjectPhoto
)
from schemas import (
    ProjectCreate, ProjectUpdate,
    ProjectAssignmentCreate,
    TaskCreate, TaskUpdate,
    TodoCreate, TodoUpdate,
    TaskAssignmentCreate, TodoAssignmentCreate,
    TaskAttachmentCreate, TodoAttachmentCreate,
    TaskCommentCreate, TodoCommentCreate,
    ProjectPhotoCreate
)

# ===== User CRUD (読み取り専用 - ntb_data テーブル) =====
def get_user(db: Session, user_id: int) -> Optional[User]:
    """ユーザーをIDで取得 (ntb_data.users)"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """ユーザーをメールアドレスで取得 (ntb_data.users)"""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """ユーザー一覧を取得 (ntb_data.users)"""
    return db.query(User).offset(skip).limit(limit).all()


# ===== Ship CRUD (読み取り専用 - ntb_data テーブル) =====
def get_ship(db: Session, ship_id: int) -> Optional[Ship]:
    """船舶をIDで取得 (ntb_data.ships)"""
    return db.query(Ship).filter(Ship.id == ship_id).first()


def get_ships(db: Session, skip: int = 0, limit: int = 100) -> List[Ship]:
    """船舶一覧を取得 (ntb_data.ships)"""
    return db.query(Ship).offset(skip).limit(limit).all()


# ===== Role CRUD (読み取り専用 - ntb_data テーブル) =====
def get_role(db: Session, role_id: int) -> Optional[Role]:
    """ロールをIDで取得 (ntb_data.roles)"""
    return db.query(Role).filter(Role.id == role_id).first()


def get_user_roles(db: Session, user_id: int) -> List[Role]:
    """ユーザーのロール一覧を取得 (ntb_data.roles, ntb_data.user_has_roles)"""
    return db.query(Role).join(UserHasRoles).filter(
        UserHasRoles.user_id == user_id
    ).all()


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    """ロール一覧を取得 (ntb_data.roles)"""
    return db.query(Role).offset(skip).limit(limit).all()

# ===== Project CRUD =====
def create_project(db: Session, project: ProjectCreate) -> Project:
    """プロジェクトを作成"""
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """プロジェクトをIDで取得"""
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    """プロジェクト一覧を取得"""
    return db.query(Project).offset(skip).limit(limit).all()


def get_projects_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
    """オーナーIDでプロジェクト一覧を取得"""
    return db.query(Project).filter(Project.owner_id == owner_id).offset(skip).limit(limit).all()


def update_project(db: Session, project_id: int, project_update: ProjectUpdate) -> Optional[Project]:
    """プロジェクトを更新"""
    db_project = get_project(db, project_id)
    if db_project is None:
        return None
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int) -> bool:
    """プロジェクトを削除"""
    db_project = get_project(db, project_id)
    if db_project is None:
        return False
    
    db.delete(db_project)
    db.commit()
    return True


# ===== ProjectAssignment CRUD =====
def create_project_assignment(db: Session, assignment: ProjectAssignmentCreate) -> ProjectAssignment:
    """プロジェクト担当者を追加"""
    db_assignment = ProjectAssignment(**assignment.model_dump())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


def get_project_assignments(db: Session, project_id: int) -> List[ProjectAssignment]:
    """プロジェクトの担当者一覧を取得"""
    return db.query(ProjectAssignment).filter(ProjectAssignment.project_id == project_id).all()


def delete_project_assignment(db: Session, assignment_id: int) -> bool:
    """プロジェクト担当者を削除"""
    db_assignment = db.query(ProjectAssignment).filter(ProjectAssignment.id == assignment_id).first()
    if db_assignment is None:
        return False
    
    db.delete(db_assignment)
    db.commit()
    return True


# ===== Task CRUD =====
def create_task(db: Session, task: TaskCreate) -> Task:
    """タスクを作成"""
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task(db: Session, project_id: int, task_number: int) -> Optional[Task]:
    """タスクを取得"""
    return db.query(Task).filter(
        and_(Task.project_id == project_id, Task.task_number == task_number)
    ).first()


def get_tasks_by_project(db: Session, project_id: int) -> List[Task]:
    """プロジェクトのタスク一覧を取得"""
    return db.query(Task).filter(Task.project_id == project_id).all()


def update_task(db: Session, project_id: int, task_number: int, task_update: TaskUpdate) -> Optional[Task]:
    """タスクを更新"""
    db_task = get_task(db, project_id, task_number)
    if db_task is None:
        return None
    
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, project_id: int, task_number: int) -> bool:
    """タスクを削除"""
    db_task = get_task(db, project_id, task_number)
    if db_task is None:
        return False
    
    db.delete(db_task)
    db.commit()
    return True


# ===== Todo CRUD =====
def create_todo(db: Session, todo: TodoCreate) -> Todo:
    """Todoを作成"""
    db_todo = Todo(**todo.model_dump())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


def get_todo(db: Session, project_id: int, task_number: int, todo_number: int) -> Optional[Todo]:
    """Todoを取得"""
    return db.query(Todo).filter(
        and_(
            Todo.project_id == project_id,
            Todo.task_number == task_number,
            Todo.todo_number == todo_number
        )
    ).first()


def get_todos_by_task(db: Session, project_id: int, task_number: int) -> List[Todo]:
    """タスクのTodo一覧を取得"""
    return db.query(Todo).filter(
        and_(Todo.project_id == project_id, Todo.task_number == task_number)
    ).all()


def update_todo(db: Session, project_id: int, task_number: int, todo_number: int, todo_update: TodoUpdate) -> Optional[Todo]:
    """Todoを更新"""
    db_todo = get_todo(db, project_id, task_number, todo_number)
    if db_todo is None:
        return None
    
    update_data = todo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_todo, field, value)
    
    db.commit()
    db.refresh(db_todo)
    return db_todo


def delete_todo(db: Session, project_id: int, task_number: int, todo_number: int) -> bool:
    """Todoを削除"""
    db_todo = get_todo(db, project_id, task_number, todo_number)
    if db_todo is None:
        return False
    
    db.delete(db_todo)
    db.commit()
    return True


def complete_todo(db: Session, project_id: int, task_number: int, todo_number: int) -> Optional[Todo]:
    """Todoを完了にする"""
    db_todo = get_todo(db, project_id, task_number, todo_number)
    if db_todo is None:
        return None
    
    db_todo.is_completed = datetime.now()
    db.commit()
    db.refresh(db_todo)
    return db_todo


# ===== TaskAssignment CRUD =====
def create_task_assignment(db: Session, assignment: TaskAssignmentCreate) -> TaskAssignment:
    """タスク担当者を追加"""
    db_assignment = TaskAssignment(**assignment.model_dump())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


def get_task_assignments(db: Session, project_id: int, task_number: int) -> List[TaskAssignment]:
    """タスクの担当者一覧を取得"""
    return db.query(TaskAssignment).filter(
        and_(TaskAssignment.project_id == project_id, TaskAssignment.task_number == task_number)
    ).all()


def delete_task_assignment(db: Session, assignment_id: int) -> bool:
    """タスク担当者を削除"""
    db_assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
    if db_assignment is None:
        return False
    
    db.delete(db_assignment)
    db.commit()
    return True


# ===== TodoAssignment CRUD =====
def create_todo_assignment(db: Session, assignment: TodoAssignmentCreate) -> TodoAssignment:
    """Todo担当者を追加"""
    db_assignment = TodoAssignment(**assignment.model_dump())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


def get_todo_assignments(db: Session, project_id: int, task_number: int, todo_number: int) -> List[TodoAssignment]:
    """Todoの担当者一覧を取得"""
    return db.query(TodoAssignment).filter(
        and_(
            TodoAssignment.project_id == project_id,
            TodoAssignment.task_number == task_number,
            TodoAssignment.todo_number == todo_number
        )
    ).all()


def delete_todo_assignment(db: Session, assignment_id: int) -> bool:
    """Todo担当者を削除"""
    db_assignment = db.query(TodoAssignment).filter(TodoAssignment.id == assignment_id).first()
    if db_assignment is None:
        return False
    
    db.delete(db_assignment)
    db.commit()
    return True


# ===== TaskAttachment CRUD =====
def create_task_attachment(db: Session, attachment: TaskAttachmentCreate) -> TaskAttachment:
    """タスク添付ファイルを追加"""
    db_attachment = TaskAttachment(**attachment.model_dump())
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment


def get_task_attachments(db: Session, project_id: int, task_number: int) -> List[TaskAttachment]:
    """タスクの添付ファイル一覧を取得"""
    return db.query(TaskAttachment).filter(
        and_(TaskAttachment.project_id == project_id, TaskAttachment.task_number == task_number)
    ).all()


def delete_task_attachment(db: Session, attachment_id: int) -> bool:
    """タスク添付ファイルを削除"""
    db_attachment = db.query(TaskAttachment).filter(TaskAttachment.id == attachment_id).first()
    if db_attachment is None:
        return False
    
    db.delete(db_attachment)
    db.commit()
    return True


# ===== TodoAttachment CRUD =====
def create_todo_attachment(db: Session, attachment: TodoAttachmentCreate) -> TodoAttachment:
    """Todo添付ファイルを追加"""
    db_attachment = TodoAttachment(**attachment.model_dump())
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment


def get_todo_attachments(db: Session, project_id: int, task_number: int, todo_number: int) -> List[TodoAttachment]:
    """Todoの添付ファイル一覧を取得"""
    return db.query(TodoAttachment).filter(
        and_(
            TodoAttachment.project_id == project_id,
            TodoAttachment.task_number == task_number,
            TodoAttachment.todo_number == todo_number
        )
    ).all()


def delete_todo_attachment(db: Session, attachment_id: int) -> bool:
    """Todo添付ファイルを削除"""
    db_attachment = db.query(TodoAttachment).filter(TodoAttachment.id == attachment_id).first()
    if db_attachment is None:
        return False
    
    db.delete(db_attachment)
    db.commit()
    return True


# ===== TaskComment CRUD =====
def create_task_comment(db: Session, comment: TaskCommentCreate) -> TaskComment:
    """タスクコメントを追加"""
    db_comment = TaskComment(**comment.model_dump())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_task_comments(db: Session, project_id: int, task_number: int) -> List[TaskComment]:
    """タスクのコメント一覧を取得"""
    return db.query(TaskComment).filter(
        and_(TaskComment.project_id == project_id, TaskComment.task_number == task_number)
    ).all()


def delete_task_comment(db: Session, comment_id: int) -> bool:
    """タスクコメントを削除"""
    db_comment = db.query(TaskComment).filter(TaskComment.id == comment_id).first()
    if db_comment is None:
        return False
    
    db.delete(db_comment)
    db.commit()
    return True


# ===== TodoComment CRUD =====
def create_todo_comment(db: Session, comment: TodoCommentCreate) -> TodoComment:
    """Todoコメントを追加"""
    db_comment = TodoComment(**comment.model_dump())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_todo_comments(db: Session, project_id: int, task_number: int, todo_number: int) -> List[TodoComment]:
    """Todoのコメント一覧を取得"""
    return db.query(TodoComment).filter(
        and_(
            TodoComment.project_id == project_id,
            TodoComment.task_number == task_number,
            TodoComment.todo_number == todo_number
        )
    ).all()


def delete_todo_comment(db: Session, comment_id: int) -> bool:
    """Todoコメントを削除"""
    db_comment = db.query(TodoComment).filter(TodoComment.id == comment_id).first()
    if db_comment is None:
        return False
    
    db.delete(db_comment)
    db.commit()
    return True


# ===== ProjectPhoto CRUD =====
def create_project_photo(db: Session, photo: ProjectPhotoCreate) -> ProjectPhoto:
    """プロジェクト写真を追加"""
    db_photo = ProjectPhoto(**photo.model_dump())
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo


def get_project_photos(db: Session, project_id: int, task_number: Optional[int] = None, 
                       todo_number: Optional[int] = None) -> List[ProjectPhoto]:
    """プロジェクトの写真一覧を取得"""
    query = db.query(ProjectPhoto).filter(ProjectPhoto.project_id == project_id)
    
    if task_number is not None:
        query = query.filter(ProjectPhoto.task_number == task_number)
    
    if todo_number is not None:
        query = query.filter(ProjectPhoto.todo_number == todo_number)
    
    return query.all()


def delete_project_photo(db: Session, photo_id: int) -> bool:
    """プロジェクト写真を削除"""
    db_photo = db.query(ProjectPhoto).filter(ProjectPhoto.id == photo_id).first()
    if db_photo is None:
        return False
    
    db.delete(db_photo)
    db.commit()
    return True
