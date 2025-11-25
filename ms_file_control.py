"""
Microsoft SharePoint ファイル操作モジュール (FastAPI版)

このモジュールは、Microsoft Graph APIを使用してSharePointとのファイル操作を提供します。
FlaskからFastAPIへ移植し、async/awaitに対応しています。

主な変更点:
- ファイルアップロード関数を async/await 対応に変更
- FastAPIの UploadFile オブジェクトに対応
- file.read() を await file.read() に変更
- file.seek(0) を file.file.seek(0) に変更（FastAPIのUploadFileは同期seek）
"""

import requests
from io import BytesIO
import re, os
from datetime import datetime
from urllib.parse import quote
import urllib.parse
from pytz import timezone

try:
    from .utils import generate_unique_filename
except ImportError:
    from utils import generate_unique_filename
try:
    from . import app_config
except ImportError:
    import app_config


async def upload_file_to_sharepoint(file, auth, app_config):
    try:
        token_response = auth.get_token_for_user(app_config.SCOPE)
        if not token_response:
            return None, 401

        headers = {
            'Authorization': 'Bearer ' + token_response['access_token'],
            'Content-Type': 'application/octet-stream'
        }
        file_name = file.filename
        file_content = await file.read()
        # FastAPI UploadFileはseekが同期メソッド
        if hasattr(file, 'file'):
            file.file.seek(0)
        # MOL DRIVE
        endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{app_config.parent_folder_id}:/{file_name}:/content'

        response = requests.put(endpoint, headers=headers, data=file_content)

        if response.status_code in (200, 201):
            file_info = response.json()
            file_id = file_info['id']
            return file_id, None
        else:
            return None, response.status_code
    except Exception as e:
        # print(f"Error in upload_file_to_sharepoint: {e}")
        if 'response' in locals():
            return None, response.status_code
        else:
            return None, 500

# 添付ファイルをアップロード       
async def upload_attachment_to_sharepoint(file, auth, app_config):
    try:
        token_response = auth.get_token_for_user(app_config.SCOPE)
        if not token_response:
            return None, 401

        headers = {
            'Authorization': 'Bearer ' + token_response['access_token'],
            'Content-Type': 'application/octet-stream'
        }
        file_name = generate_unique_filename(file)
        file_content = await file.read()
        # FastAPI UploadFileはseekが同期メソッド
        if hasattr(file, 'seek'):
            file.file.seek(0)
        # MOL DRIVE
        endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{app_config.attached_maint_folder_id}:/{file_name}:/content'

        response = requests.put(endpoint, headers=headers, data=file_content)

        if response.status_code in (200, 201):
            file_info = response.json()
            return file_info['id'], app_config.attached_maint_folder_id, response.status_code
        else:
            return None, response.status_code
    except Exception as e:
        # print(f"Error in upload_file_to_sharepoint: {e}")
        if 'response' in locals():
            return None, response.status_code
        else:
            return None, 500

def upload_edited_files(file_content,file_name, auth, app_config):
    try:
        token_response = auth.get_token_for_user(app_config.SCOPE)
        if not token_response:
            return None, 401

        headers = {
            'Authorization': 'Bearer ' + token_response['access_token'],
            'Content-Type': 'application/octet-stream'
        }
        # MOL DRIVE
        endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{app_config.Edited_Files}:/{file_name}:/content'

        response = requests.put(endpoint, headers=headers, data=file_content)

        if response.status_code in (200, 201):
            file_info = response.json()
            file_id = file_info['id']
            return file_id, response.status_code
        else:
            return None, response.status_code
    except Exception as e:
        # print(f"Error in upload_edited_files: {e}")
        if 'response' in locals():
            return None, response.status_code
        else:
            return None, 500

async def upload_file_to_specific_folder(file, folder_id, auth, app_config):
    try:
        token_response = auth.get_token_for_user(app_config.SCOPE)
        if not token_response:
            return None

        headers = {
            'Authorization': 'Bearer ' + token_response['access_token'],
            'Content-Type': 'application/octet-stream'
        }
        file_name = file.filename
        file_content = await file.read()
        # FastAPI UploadFileはseekが同期メソッド
        if hasattr(file, 'file'):
            file.file.seek(0)
        # MOL DRIVE
        endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{folder_id}:/{file_name}:/content'
        
        response = requests.put(endpoint, headers=headers, data=file_content)
        
        if response.status_code in (200, 201):
            file_info = response.json()
            file_id = file_info['id']
            return file_id
        else:
            return None
    except Exception as e:
        # print(f"Error in upload_file_to_specific_folder: {e}")
        return None

def list_files(auth, folder_id=None, app_config=None):
    token_response = auth.get_token_for_user(app_config.SCOPE)
    if not token_response:
        # print("401")
        return None, None, None, None, 401, None

    headers = {
        'Authorization': 'Bearer ' + token_response['access_token'],
        'Accept': 'application/json'
    }
    # NTB DRIVE
    if folder_id:
        endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{folder_id}/children'
    else:
        endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{app_config.parent_folder_id}/children'
        # endpoint = app_config.ENDPOINT

    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        items = response.json()['value']
        files = [item for item in items if 'file' in item]
        file_ids = [item['id'] for item in files]

        folders = [item for item in items if 'folder' in item]
        folder_ids = [item['id'] for item in folders]
        return files, folders, file_ids, folder_ids, response.status_code, response
    else:
        return None, None, None, None, response.status_code, response

def download_file(file_id, auth, app_config):
    token_response = auth.get_token_for_user(app_config.SCOPE)
    if not token_response:
        return None, 401
    headers = {
        'Authorization': 'Bearer ' + token_response['access_token'],
        'Accept': 'application/octet-stream'
    }
    # MOL DRIVE
    endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{file_id}/content'


    response = requests.get(endpoint, headers=headers, stream=True)
    if response.status_code == 200:
        return BytesIO(response.content),  response.status_code
    else:
        return None, response.status_code
    
def get_shared_link(file_id, auth, app_config):
    token_response = auth.get_token_for_user(app_config.SCOPE)
    if not token_response:
        # print("トークン取得に失敗しました")
        return None, 401
    headers = {
        'Authorization': 'Bearer ' + token_response['access_token'],
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{file_id}/createLink'
    body = {
        "type": "view",
        "scope": "anonymous"
    }

    response = requests.post(endpoint, headers=headers, json=body)
    # print(f"SharePoint API response: {response.status_code}")
    # print(f"Response content: {response.content}")
    if response.status_code in [200, 201, 202]:  # 成功の可能性があるコードを追加
        shared_link_info = response.json()
        shared_link = shared_link_info.get('link', {}).get('webUrl')
        if shared_link:
            return shared_link, 200
        else:
            return None, 404
    else:
        return None, response.status_code

    
def get_preview_url(file_id, auth, app_config):
    """Office ファイルのプレビュー URL を取得する"""
    # トークンを取得
    token_response = auth.get_token_for_user(app_config.SCOPE)
    if not token_response:
        # print("トークン取得に失敗しました")
        return None, 401
    
    access_token = token_response['access_token']
    
    # ファイル情報を取得（ダウンロードURLを含む）
    endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{file_id}'
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json'
    }
    
    response = requests.get(endpoint, headers=headers)
    # print(f"SharePoint API response: {response.status_code}")
    
    if response.status_code == 200:
        file_info = response.json()
        # 一時的なダウンロードURLを取得
        download_url = file_info.get('@microsoft.graph.downloadUrl')
        if download_url:
            # Office Viewerに直接ダウンロードURLを渡す
            encoded_url = quote(download_url, safe='')
            preview_url = f'https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}&wdStartOn=1&ui=ja-JP'
            return preview_url, 200
        else:
            # print("ダウンロードURLが見つかりません")
            return None, 404
    else:
        # print(f"Response content: {response.text}")
        return None, response.status_code
        
def create_folder(folder_name, auth, app_config):
    token_response = auth.get_token_for_user(app_config.SCOPE)
    if not token_response:
        return None, 401

    headers = {
        'Authorization': 'Bearer ' + token_response['access_token'],
        'Content-Type': 'application/json'
    }

    # MOL DRIVE
    endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/root/children'
    
    if folder_name:
        # フォルダが存在するか確認
        response = requests.get(endpoint, headers=headers)
        if response.status_code in (200, 201):
            children = response.json().get('value', [])
            for child in children:
                if child.get('name') == folder_name and 'folder' in child:
                    return child['id'], None
        else:
            return None, response.status_code

    # フォルダ名がない場合、新規作成
    folder_data = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "rename"
    }

    response = requests.post(endpoint, headers=headers, json=folder_data)
    
    if response.status_code in (200, 201):
        folder_id = response.json().get('id')
        return folder_id, response.status_code
    else:
        return None, response.status_code

def user_info(auth, app_config=None):
    token_response = auth.get_token_for_user(app_config.SCOPE)
    if not token_response:
        return None, 401

    headers = {
        'Authorization': 'Bearer ' + token_response['access_token'],
        'Accept': 'application/json'
    }

    endpoint = "https://graph.microsoft.com/v1.0/me"
    
    response = requests.get(endpoint, headers=headers)
    user_info = response.json()

    return user_info    

# ファイル名からIDを抽出する関数
def id_from_filename(filename):
    # 正規表現を使って、ID_数字_ の形式にマッチングする部分を探す
    match = re.search(r'ID_(\d+)_', filename)

    if match:
        # マッチングした部分を整数に変換して返す
        id_num = int(match.group(1))
        return id_num
    else:
        # マッチングしなかった場合はエラーを発生させる
        raise ValueError(f"Invalid filename format: {filename}")

def delete_file(file_id, auth, app_config):
    try:
        # 入力値のバリデーション
        if not file_id:
            # print("delete_file: file_id is None or empty")
            return False, 400
        
        if not auth:
            # print("delete_file: auth object is None")
            return False, 400
        
        if not app_config:
            # print("delete_file: app_config is None")
            return False, 400
        
        # print(f"delete_file: Starting deletion for file_id={file_id}")
        
        # トークン取得
        try:
            token_response = auth.get_token_for_user(app_config.SCOPE)
        except Exception as token_error:
            # print(f"delete_file: Error getting token: {token_error}")
            return False, 401
        
        if not token_response:
            # print("delete_file: Failed to get token")
            return False, 401
        
        if 'access_token' not in token_response:
            print("delete_file: No access_token in token_response")
            return False, 401
        
        headers = {
            'Authorization': 'Bearer ' + token_response['access_token']
        }
        
        # エンドポイント構築
        try:
            endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{file_id}'
            # print(f"delete_file: Sending DELETE request to {endpoint}")
        except Exception as endpoint_error:
            print(f"delete_file: Error constructing endpoint: {endpoint_error}")
            return False, 500
        
        # API呼び出し
        try:
            response = requests.delete(endpoint, headers=headers, timeout=30)
            # print(f"delete_file: Response status_code={response.status_code}")
        except requests.exceptions.Timeout:
            print("delete_file: Request timed out")
            return False, 408
        except requests.exceptions.RequestException as req_error:
            print(f"delete_file: Request error: {req_error}")
            return False, 500
        
        if response.status_code == 204:  # No Content, meaning the delete was successful
            # print("delete_file: Deletion successful")
            return True, response.status_code
        elif response.status_code == 404:  # File not found, treat as success
            print("delete_file: File not found (404), treating as successful deletion")
            return True, response.status_code
        else:
            try:
                response_text = response.text[:500]  # 最初の500文字のみ
            except:
                response_text = "Unable to read response text"
            # print(f"delete_file: Deletion failed with status {response.status_code}, response: {response_text}")
            return False, response.status_code
            
    except Exception as e:
        print(f"Unexpected error in delete_file: {type(e).__name__}: {e}")
        return False, 500

def delete_folder(folder_id, auth, app_config):
    try:
        token_response = auth.get_token_for_user(app_config.SCOPE)
        if not token_response:
            return False, 401
        
        headers = {
            'Authorization': 'Bearer ' + token_response['access_token']
        }
        # MOL DRIVE
        endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{folder_id}'        
        
        response = requests.delete(endpoint, headers=headers)
        
        if response.status_code == 204:  # No Content, meaning the delete was successful
            return True, response.status_code
        else:
            return False, response.status_code
    except Exception as e:
        # print(f"Error in delete_folder: {e}")
        return False, 500
        
async def attache_file_to_spo(file, auth, app_config, folder=None):
    try:
         # Check if file is a string (file path)
        if isinstance(file, str):
            with open(file, 'rb') as f:
                file_content = f.read()
                # ファイルパスから直接処理
                token_response = auth.get_token_for_user(app_config.SCOPE)
                if not token_response:
                    return None, None, 401

                headers = {
                    'Authorization': 'Bearer ' + token_response['access_token'],
                    'Content-Type': 'application/octet-stream'
                }
                file_name = os.path.basename(file)
                current_datetime = datetime.now(timezone("Asia/Tokyo")).strftime("%Y%m%d%H%M%S")
                new_file_name = f"{current_datetime}_{file_name}"
        else:
            # UploadFileオブジェクトの場合
            token_response = auth.get_token_for_user(app_config.SCOPE)
            if not token_response:
                return None, None, 401

            headers = {
                'Authorization': 'Bearer ' + token_response['access_token'],
                'Content-Type': 'application/octet-stream'
            }
            file_name = os.path.basename(file.filename if hasattr(file, 'filename') else file.name)
            current_datetime = datetime.now(timezone("Asia/Tokyo")).strftime("%Y%m%d%H%M%S")
            new_file_name = f"{current_datetime}_{file_name}"
            
            file_content = await file.read()
            # FastAPI UploadFileはseekが同期メソッド
            if hasattr(file, 'file'):
                file.file.seek(0)
        # トークンを取得済みなので、ここから共通処理
        if folder == None:
            spo_folder_id = app_config.ship_data_folder_id
        elif folder == 'request':
            spo_folder_id = app_config.request_data_folder_id
        
        # ファイルサイズをチェック (4MB = 4,194,304 bytes)
        file_size = len(file_content)
        
        # 4MB以上のファイルはアップロードセッションを使用
        if file_size > 4 * 1024 * 1024:
            return upload_large_file_to_spo(file_content, new_file_name, spo_folder_id, token_response['access_token'], app_config)
        
        # 4MB以下のファイルは通常のPUTを使用
        # MOL DRIVE
        endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{spo_folder_id}:/{new_file_name}:/content'

        response = requests.put(endpoint, headers=headers, data=file_content)
        # print(response.status_code)
        # print(response.json())

        if response.status_code in (200, 201):
            file_info = response.json()
            file_id = file_info['id']
            folder_id = spo_folder_id
            return file_id,folder_id, response.status_code
        else:
            return None, None, response.status_code
    except Exception as e:
        # print(f"Error in attache_file_to_spo: {e}")
        if 'response' in locals():
            return None, None, response.status_code
        else:
            return None, None, 500

def upload_large_file_to_spo(file_content, file_name, folder_id, access_token, app_config):
    """
    4MB以上のファイルをアップロードするための関数（チャンクアップロード）
    """
    try:
        # アップロードセッションを作成
        create_session_url = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{folder_id}:/{file_name}:/createUploadSession'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        session_response = requests.post(create_session_url, headers=headers)
        
        if session_response.status_code not in (200, 201):
            return None, None, session_response.status_code
        
        upload_url = session_response.json()['uploadUrl']
        
        # ファイルをチャンクに分割してアップロード (10MB チャンク)
        chunk_size = 10 * 1024 * 1024  # 10MB
        file_size = len(file_content)
        chunks = (file_size + chunk_size - 1) // chunk_size
        
        for i in range(chunks):
            start = i * chunk_size
            end = min(start + chunk_size, file_size)
            chunk = file_content[start:end]
            
            chunk_headers = {
                'Content-Length': str(len(chunk)),
                'Content-Range': f'bytes {start}-{end-1}/{file_size}'
            }
            
            chunk_response = requests.put(upload_url, headers=chunk_headers, data=chunk)
            
            # 最後のチャンク以外は202が返る
            if i < chunks - 1 and chunk_response.status_code != 202:
                return None, None, chunk_response.status_code
        
        # 最後のチャンクのレスポンスからファイル情報を取得
        if chunk_response.status_code in (200, 201):
            file_info = chunk_response.json()
            file_id = file_info['id']
            return file_id, folder_id, chunk_response.status_code
        else:
            return None, None, chunk_response.status_code
            
    except Exception as e:
        # print(f"Error in upload_large_file_to_spo: {e}")
        return None, None, 500
        
def get_preview_link(file_id, auth, app_config):
    token_response = auth.get_token_for_user(app_config.SCOPE)
    if not token_response:
        return None, 401
    headers = {
        'Authorization': 'Bearer ' + token_response['access_token'],
        'Content-Type': 'application/json'
    }
    endpoint = f'https://graph.microsoft.com/v1.0/sites/{app_config.site_id}/drives/{app_config.drive_id}/items/{file_id}/preview'
    # print(endpoint)
    response = requests.post(endpoint, headers=headers)
    # print(response.status_code)
    # print(response.json())

    if response.status_code == 200:
        preview_url = response.json().get('getUrl')
        # URLエンコードを適用
        encoded_url = urllib.parse.quote(preview_url, safe=':/?&=')
        # print(encoded_url)
        return encoded_url, 200
    return None, response.status_code

        
