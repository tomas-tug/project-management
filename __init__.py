"""
FastAPI Application Package

このパッケージは、FastAPIベースのプロジェクト管理アプリケーションです。

Modules:
    - models: SQLAlchemyデータベースモデル
    - schemas: Pydanticスキーマ（バリデーション・シリアライゼーション）
    - crud: データベースCRUD操作
    - database: データベース接続設定
    - main: FastAPIアプリケーションのエントリーポイント
    - ms_file_control: Microsoft SharePointファイル操作
    - send_email_message: Azure Communication Service メール送信
    - utils: ユーティリティ関数
    - app_config: アプリケーション設定
"""

__version__ = "0.1.0"
__all__ = [
    "models",
    "schemas", 
    "crud",
    "database",
    "main",
    "ms_file_control",
    "send_email_message",
    "utils",
    "app_config",
]
