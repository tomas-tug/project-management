import os
from datetime import datetime
from pytz import timezone


def generate_unique_filename(file):
    """
    ファイルに一意のファイル名を生成する
    
    Args:
        file: アップロードされたファイルオブジェクト（filename属性を持つ）
        
    Returns:
        str: タイムスタンプ付きの一意のファイル名
    """
    # ファイル名を取得
    if hasattr(file, 'filename'):
        original_filename = file.filename
    elif hasattr(file, 'name'):
        original_filename = os.path.basename(file.name)
    else:
        original_filename = 'unknown_file'
    
    # 現在の日時を取得（日本時間）
    current_datetime = datetime.now(timezone("Asia/Tokyo")).strftime("%Y%m%d%H%M%S")
    
    # ファイル名と拡張子を分離
    name, ext = os.path.splitext(original_filename)
    
    # タイムスタンプ付きのファイル名を生成
    unique_filename = f"{current_datetime}_{name}{ext}"
    
    return unique_filename
