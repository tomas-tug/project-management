from datetime import datetime
from pytz import timezone
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, Text, Boolean, PrimaryKeyConstraint, ForeignKeyConstraint, event, text, Numeric, Enum, Table
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import relationship
import enum

# SQLAlchemy Base
Base = declarative_base()


# Enum定義
class DockCategories(enum.Enum):
    Interm = "中間検査"
    Regular = "定期検査"
    Joint = "合入渠"
    others = "その他"
    Inaugural = "就航"
    NotSet = ""


# TimestampMixin for created_at and updated_at
class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime,
            default=lambda: datetime.now(timezone("Asia/Tokyo")),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=lambda: datetime.now(timezone("Asia/Tokyo")),
            onupdate=lambda: datetime.now(timezone("Asia/Tokyo")),
            nullable=False,
        )


# ===== 読み取り専用モデル (ntb_data) =====
# User Model (読み取り専用 - ntb_data)
class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = {'schema': 'ntb_data'}
    
    id = Column(Integer, primary_key=True)
    email = Column(String(64), unique=True, index=True)
    name = Column(String(64))
    ms_email = Column(String(128))
    ms_id = Column(String(128))
    
    # Relationships
    roles = relationship("Role", secondary="ntb_data.user_has_roles", back_populates="users")
    project_assignments = relationship("ProjectAssignment", back_populates="user")
    task_assignments = relationship("TaskAssignment", back_populates="user")
    todo_assignments = relationship("TodoAssignment", back_populates="user")
    task_attachments = relationship("TaskAttachment", back_populates="user")
    todo_attachments = relationship("TodoAttachment", back_populates="user")
    task_comments = relationship("TaskComment", back_populates="user")
    todo_comments = relationship("TodoComment", back_populates="user")
    project_photos = relationship("ProjectPhoto", back_populates="user")


# Ship Model (読み取り専用 - ntb_data)
class Ship(Base, TimestampMixin):
    __tablename__ = "ships"
    __table_args__ = {'schema': 'ntb_data'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    ex_name = Column(String(128))
    former_name = Column(String(128))
    yard = Column(String(128))
    ship_no = Column(String(128))
    delivered = Column(DateTime)
    issued_Inscert = Column(DateTime)  # 定期検査完了
    expiry_date = Column(DateTime)  # 検査期限
    gross_tonn = Column(Numeric(8, 2))
    mmsi = Column(String(32))
    shipid = Column(String(32))
    operat_section_id = Column(Integer)  # ForeignKey削除（operat_sectionsテーブルが未定義）
    navigation_area_id = Column(Integer)  # ForeignKey削除（navigation_areasテーブルが未定義）
    deck_Categories = Column(Enum(DockCategories), default=DockCategories.NotSet)
    recent_dock = Column(DateTime)
    
    # Relationships
    projects = relationship("Project", back_populates="ship")


# Role Model (読み取り専用 - ntb_data)
class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = {'schema': 'ntb_data'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    description = Column(String(255))
    
    # Relationships
    users = relationship("User", secondary="ntb_data.user_has_roles", back_populates="roles")


# UserHasRoles Model (読み取り専用 - ntb_data)
class UserHasRoles(Base, TimestampMixin):
    __tablename__ = "user_has_roles"
    __table_args__ = {'schema': 'ntb_data'}
    
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("ntb_data.roles.id"))
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"))


# ===== 既存モデル =====
# Project Model
class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    discription = Column(Text, nullable=True)
    ship_id = Column(Integer, ForeignKey("ntb_data.ships.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    dock = Column(Boolean)
    yard = Column(String(128))
    dock_in_date = Column(DateTime)
    dock_out_date = Column(DateTime)
    yard_decision = Column(Boolean)
    date_decision = Column(Boolean)
    completion = Column(DateTime)

    # Relationships
    ship = relationship("Ship", back_populates="projects")
    owner = relationship("User", foreign_keys=[owner_id])
    photos = relationship("ProjectPhoto", back_populates="project")
    assignments = relationship("ProjectAssignment", back_populates="project")
    tasks = relationship("Task", back_populates="project")


# ProjectAssignment Model
class ProjectAssignment(Base, TimestampMixin):
    __tablename__ = "project_assignments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="project_assignments")
    project = relationship("Project", back_populates="assignments")

    def __init__(self, user_id, project_id):
        self.user_id = user_id
        self.project_id = project_id


# Task Model
class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    discription = Column(Text, nullable=True)

    # 複合主キー
    __table_args__ = (
        PrimaryKeyConstraint("project_id", "task_number"),
    )

    # Relationships
    project = relationship("Project", back_populates="tasks")
    todos = relationship("Todo", back_populates="task")
    assignments = relationship("TaskAssignment", back_populates="task")
    attachments = relationship("TaskAttachment", back_populates="task")
    comments = relationship("TaskComment", back_populates="task")

    # task_number を自動生成するためのイベント
    @staticmethod
    def generate_task_number(mapper, connection, target):
        max_task_number = connection.execute(
            text("SELECT COALESCE(MAX(task_number), 0) FROM tasks WHERE project_id = :project_id"),
            {"project_id": target.project_id}
        ).scalar()
        target.task_number = max_task_number + 1


# `before_insert` イベントで task_number を自動生成
event.listen(Task, "before_insert", Task.generate_task_number)


# Todo Model
class Todo(Base, TimestampMixin):
    __tablename__ = "todos"

    project_id = Column(Integer, nullable=False)
    task_number = Column(Integer, nullable=False)
    todo_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    start = Column(DateTime)
    is_completed = Column(DateTime)

    # 複合主キー
    __table_args__ = (
        PrimaryKeyConstraint("project_id", "task_number", "todo_number"),
        ForeignKeyConstraint(
            ["project_id", "task_number"],
            ["tasks.project_id", "tasks.task_number"],
        ),
    )

    # Relationships
    task = relationship("Task", back_populates="todos")
    assignments = relationship("TodoAssignment", back_populates="todo")
    attachments = relationship("TodoAttachment", back_populates="todo")
    comments = relationship("TodoComment", back_populates="todo")

    # todo_number を自動生成するためのイベント
    @staticmethod
    def generate_todo_number(mapper, connection, target):
        max_todo_number = connection.execute(
            text("SELECT COALESCE(MAX(todo_number), 0) FROM todos WHERE project_id = :project_id AND task_number = :task_number"),
            {"project_id": target.project_id, "task_number": target.task_number}
        ).scalar()
        target.todo_number = max_todo_number + 1


# `before_insert` イベントで todo_number を自動生成
event.listen(Todo, "before_insert", Todo.generate_todo_number)


# TaskAssignment Model
class TaskAssignment(Base, TimestampMixin):
    __tablename__ = "task_assignments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    project_id = Column(Integer, nullable=False)
    task_number = Column(Integer, nullable=False)

    # 外部キー制約
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "task_number"],
            ["tasks.project_id", "tasks.task_number"],
        ),
    )

    # Relationships
    user = relationship("User", back_populates="task_assignments")
    task = relationship("Task", back_populates="assignments")

    def __init__(self, user_id, project_id, task_number):
        self.user_id = user_id
        self.project_id = project_id
        self.task_number = task_number


# TodoAssignment Model
class TodoAssignment(Base, TimestampMixin):
    __tablename__ = "todo_assignments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    project_id = Column(Integer, nullable=False)
    task_number = Column(Integer, nullable=False)
    todo_number = Column(Integer, nullable=False)

    # 外部キー制約
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "task_number", "todo_number"],
            ["todos.project_id", "todos.task_number", "todos.todo_number"],
        ),
    )

    # Relationships
    user = relationship("User", back_populates="todo_assignments")
    todo = relationship("Todo", back_populates="assignments")

    def __init__(self, user_id, project_id, task_number, todo_number):
        self.user_id = user_id
        self.project_id = project_id
        self.task_number = task_number
        self.todo_number = todo_number


# TaskAttachment Model
class TaskAttachment(Base, TimestampMixin):
    __tablename__ = "task_attachments"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False)
    task_number = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    file_id = Column(String(255), nullable=False)
    directory_id = Column(String(255))
    originname = Column(String(128), nullable=False)
    title = Column(String(128), nullable=False)
    icon = Column(String(128))

    # 外部キー制約
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "task_number"],
            ["tasks.project_id", "tasks.task_number"],
        ),
    )

    # Relationships
    user = relationship("User", back_populates="task_attachments")
    task = relationship("Task", back_populates="attachments")

    def __init__(self, project_id, task_number, user_id, file_id, directory_id, originname, title, icon):
        self.project_id = project_id
        self.task_number = task_number
        self.user_id = user_id
        self.file_id = file_id
        self.directory_id = directory_id
        self.originname = originname
        self.title = title
        self.icon = icon


# TodoAttachment Model
class TodoAttachment(Base, TimestampMixin):
    __tablename__ = "todo_attachments"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False)
    task_number = Column(Integer, nullable=False)
    todo_number = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    file_id = Column(String(255), nullable=False)
    directory_id = Column(String(255))  # カラムを追加
    originname = Column(String(128), nullable=False)
    title = Column(String(128), nullable=False)
    icon = Column(String(128))  # カラムを追加

    # 外部キー制約
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "task_number", "todo_number"],
            ["todos.project_id", "todos.task_number", "todos.todo_number"],
        ),
    )

    # Relationships
    user = relationship("User", back_populates="todo_attachments")
    todo = relationship("Todo", back_populates="attachments")

    def __init__(self, project_id, task_number, todo_number, user_id, file_id, directory_id, originname, title, icon):
        self.project_id = project_id
        self.task_number = task_number
        self.todo_number = todo_number
        self.user_id = user_id
        self.file_id = file_id
        self.directory_id = directory_id
        self.originname = originname
        self.title = title
        self.icon = icon


# TaskComment Model
class TaskComment(Base, TimestampMixin):
    __tablename__ = "task_comments"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False)
    task_number = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    content = Column(Text, nullable=False)

    # 外部キー制約
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "task_number"],
            ["tasks.project_id", "tasks.task_number"],
        ),
    )

    # Relationships
    user = relationship("User", back_populates="task_comments")
    task = relationship("Task", back_populates="comments")

    def __init__(self, project_id, task_number, user_id, content):
        self.project_id = project_id
        self.task_number = task_number
        self.user_id = user_id
        self.content = content


# TodoComment Model
class TodoComment(Base, TimestampMixin):
    __tablename__ = "todo_comments"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False)
    task_number = Column(Integer, nullable=False)
    todo_number = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    content = Column(Text, nullable=False)

    # 外部キー制約
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "task_number", "todo_number"],
            ["todos.project_id", "todos.task_number", "todos.todo_number"],
        ),
    )

    # Relationships
    user = relationship("User", back_populates="todo_comments")
    todo = relationship("Todo", back_populates="comments")

    def __init__(self, project_id, task_number, todo_number, user_id, content):
        self.project_id = project_id
        self.task_number = task_number
        self.todo_number = todo_number
        self.user_id = user_id
        self.content = content


# ProjectPhoto Model
class ProjectPhoto(Base, TimestampMixin):
    __tablename__ = "project_photos"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_number = Column(Integer, nullable=True)
    todo_number = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("ntb_data.users.id"), nullable=False)
    file_id = Column(String(255), nullable=False)
    category = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)

    # タスクとの条件付き外部キー制約
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "task_number"],
            ["tasks.project_id", "tasks.task_number"],
            name="fk_project_photo_task",
            use_alter=True,
            ondelete="SET NULL"
        ),
    )

    # Relationships
    user = relationship("User", back_populates="project_photos")
    project = relationship("Project", back_populates="photos")

    @hybrid_property
    def todo(self):
        if self.task_number is not None and self.todo_number is not None:
            from sqlalchemy.orm import object_session
            session = object_session(self)
            return session.query(Todo).filter(
                Todo.project_id == self.project_id,
                Todo.task_number == self.task_number,
                Todo.todo_number == self.todo_number
            ).first()
        return None

    @hybrid_property
    def task(self):
        if self.task_number is not None:
            from sqlalchemy.orm import object_session
            session = object_session(self)
            return session.query(Task).filter(
                Task.project_id == self.project_id,
                Task.task_number == self.task_number
            ).first()
        return None

    def __init__(self, project_id, user_id, file_id, task_number=None, todo_number=None, 
                 category=None, description=None):
        self.project_id = project_id
        self.user_id = user_id
        self.file_id = file_id
        self.task_number = task_number
        self.todo_number = todo_number
        self.category = category
        self.description = description
