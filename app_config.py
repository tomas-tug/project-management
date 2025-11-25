import os
from dotenv import load_dotenv

load_dotenv()

AUTHORITY = os.getenv("AUTHORITY")
# Application (client) ID of app registration
CLIENT_ID = os.getenv("CLIENT_ID")
# Application's generated client secret: never check this into source control!
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
site_id = os.getenv('SITE_ID')  # 取得したsite_idを設定
# list_id = os.getenv('LIST_ID')  # 取得したlist_idを設定
drive_id =  os.getenv('DRIVE_ID')
TENANT_ID = os.getenv('TENANT_ID')  # 取得したtenant_idを設定
parent_folder_id =  os.getenv('FLDRID_ForApp')
REDIRECT_PATH = "/getAToken"  # Used for forming an absolute URL to your redirect URI.
# The absolute URL must match the redirect URI you set
# in the app's registration in the Azure portal.
# You can find more Microsoft Graph API endpoints from Graph Explorer
# https://developer.microsoft.com/en-us/graph/graph-explorer
ENDPOINT = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children'
# You can find the proper permission names from this document
# https://docs.microsoft.com/en-us/graph/permissions-reference
SCOPE = ["User.Read"]
SECRET_KEY = os.getenv("SECRET_KEY")
# Tells the Flask-session extension to store sessions in the filesystem
SESSION_TYPE = "filesystem"
ALLOWED_TENANTS = [os.getenv("TENANT_ID")]

MAIL_SERVER = os.getenv("MAIL_SERVER")  # メールサーバーのアドレス
MAIL_PORT = os.getenv("MAIL_PORT")  # メールサーバーのポート
MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # メールサーバーのユーザー名
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")  # デフォルトの送信者アドレス
MAIL_SENDER1 = os.getenv("MAIL_SENDER1")  # メールの送信者アドレス
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # メールサーバーのパスワード
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL") == 'True'  # SSLを使用するかどうか
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS") == 'True'  # TLSを使用するかどうか
COMMUNICATION_CONNECTION_STRING = os.getenv("COMMUNICATION_CONNECTION_STRING")  # Azure Communication Serviceの接続文字列
# 新しい送信アドレスを追加
MAIL_ALTERNATE_SENDER = os.getenv("MAIL_ALTERNATE_SENDER")  # 追加の送信者アドレス
# In production, your setup may use multiple web servers behind a load balancer,
# and the subsequent requests may not be routed to the same web server.
# In that case, you may either use a centralized database-backed session store,
# or configure your load balancer to route subsequent requests to the same web server
# by using sticky sessions also known as affinity cookie.
SESSION_COOKIE_SECURE = True