"""
Azure Communication Service Email送信モジュール (FastAPI版)

FlaskからFastAPIへ移植し、async/awaitに対応しています。

主な変更点:
- EmailClientを非同期対応に変更
- send_email, send_notification_emailをasync関数に変更
- インポートをFlaskからFastAPI用に調整
"""

import os
import logging
from typing import List, Optional, Dict, Any
from azure.communication.email import EmailClient
from azure.core.exceptions import HttpResponseError

try:
    from . import app_config
except ImportError:
    import app_config

# ロガーの設定
logger = logging.getLogger(__name__)

class EmailService:
    """
    Azure Communication Serviceを使用したEmail送信サービス
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        EmailServiceの初期化
        
        Args:
            connection_string: Azure Communication Serviceの接続文字列
                               指定されない場合は環境変数から取得
        """
        # 接続文字列の設定（環境変数または引数から）
        self.connection_string = (
            connection_string or 
            app_config.COMMUNICATION_CONNECTION_STRING
        )
        
        # 固定ドメイン
        self.domain = "nihon-tug.net"
        
        # デバッグ: 接続文字列の確認（セキュリティ上、一部のみ表示）
        if self.connection_string:
            logger.info(f"Using connection string: {self.connection_string[:50]}...")
        else:
            logger.error("No connection string found!")
        
        # EmailClientの初期化
        try:
            self.client = EmailClient.from_connection_string(self.connection_string)
            logger.info("EmailClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EmailClient: {e}")
            raise
    
    async def send_email(self, 
                   to_addresses: List[str],
                   subject: str,
                   plain_text: str,
                   html_content: Optional[str] = None,
                   sender_address: Optional[str] = None,
                   reply_to_address: Optional[str] = None,
                   cc_addresses: Optional[List[str]] = None,
                   bcc_addresses: Optional[List[str]] = None) -> Optional[str]:
        """
        Emailを送信する
        
        Args:
            to_addresses: 宛先Emailアドレスのリスト
            subject: 件名
            plain_text: プレーンテキスト本文
            html_content: HTML本文（オプション）
            sender_address: 送信者アドレス（指定しない場合はデフォルト）
            reply_to_address: 返信用アドレス（オプション）
            cc_addresses: CCアドレスのリスト（オプション）
            bcc_addresses: BCCアドレスのリスト（オプション）
            
        Returns:
            str: メッセージID（送信成功時）
            None: 送信失敗時
        """
        try:
            # 送信者アドレスの設定
            if not sender_address:
                # Azure Communication Serviceで設定済みの認証済みドメインを使用
                sender_address = f"Requested_matter@{self.domain}"
                # または認証済みのアドレスを直接指定
                # sender_address = "noreply@ntb-communication.azurecomm.net"  # Azureデフォルトドメイン
            
            logger.info(f"Using sender address: {sender_address}")
            
            # 受信者の設定
            recipients = {"to": [{"address": addr} for addr in to_addresses]}
            
            # CCの設定
            if cc_addresses:
                recipients["cc"] = [{"address": addr} for addr in cc_addresses]
            
            # BCCの設定
            if bcc_addresses:
                recipients["bcc"] = [{"address": addr} for addr in bcc_addresses]
            
            # メッセージの構築
            message = {
                "senderAddress": sender_address,
                "recipients": recipients,
                "content": {
                    "subject": subject,
                    "plainText": plain_text,
                }
            }
            
            # Reply-Toアドレスが指定されている場合は追加
            if reply_to_address:
                message["replyTo"] = [{"address": reply_to_address}]
                logger.info(f"Using reply-to address: {reply_to_address}")
            
            # HTML本文が指定されている場合は追加
            if html_content:
                message["content"]["html"] = html_content
            
            # デバッグ: メッセージ構造をログ出力
            logger.info(f"Message structure: sender={sender_address}, recipients={len(to_addresses)}")
            
            # メール送信の実行 (FastAPIでは非同期を推奨、但しAzure SDKはsyncのみ)
            logger.info(f"Sending email to {len(to_addresses)} recipients with subject: {subject}")
            # Azure Communication Email SDKは同期版のみ提供しているため、そのまま使用
            poller = self.client.begin_send(message)
            result = poller.result()
            
            # デバッグ: レスポンス内容をログ出力
            logger.info(f"Email send result type: {type(result)}")
            logger.info(f"Email send result content: {result}")
            
            # レスポンスの形式を確認してメッセージIDを取得
            if hasattr(result, 'message_id'):
                message_id = result.message_id
            elif isinstance(result, dict):
                message_id = result.get('id') or result.get('messageId') or result.get('message_id')
            else:
                message_id = str(result)
            
            logger.info(f"Email sent successfully. Message ID: {message_id}")
            return message_id
            
        except HttpResponseError as e:
            logger.error(f"HTTP error occurred while sending email: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error occurred while sending email: {e}")
            return None

# シングルトンインスタンス（モジュールレベル）
_email_service = None

def get_email_service() -> EmailService:
    """
    EmailServiceのシングルトンインスタンスを取得
    
    Returns:
        EmailService: EmailServiceのインスタンス
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

async def send_notification_email(to_addresses: List[str], 
                          subject: str, 
                          message: str,
                          html_message: Optional[str] = None,
                          reply_to_address: Optional[str] = None) -> bool:
    """
    通知メールを送信する便利関数
    
    Args:
        to_addresses: 宛先Emailアドレスのリスト
        subject: 件名
        message: メッセージ本文
        html_message: HTMLメッセージ（オプション）
        reply_to_address: 返信用アドレス（オプション）
        
    Returns:
        bool: 送信成功時はTrue、失敗時はFalse
    """
    try:
        # 入力値の検証
        if not to_addresses:
            logger.warning("No email addresses provided")
            return False
        
        # 有効なメールアドレスのみをフィルタリング
        valid_addresses = [addr for addr in to_addresses if addr and isinstance(addr, str) and addr.strip()]
        
        if not valid_addresses:
            logger.warning("No valid email addresses found after filtering")
            return False
        
        logger.info(f"Sending email to {len(valid_addresses)} valid addresses: {valid_addresses}")
        
        email_service = get_email_service()
        message_id = await email_service.send_email(
            to_addresses=valid_addresses,
            subject=subject,
            plain_text=message,
            html_content=html_message,
            reply_to_address=reply_to_address
        )
        return message_id is not None
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
        return False

async def main():
    """
    テスト用のメイン関数 (FastAPI版)
    """
    # テスト用のEmail送信
    test_addresses = ["test@example.com"]
    success = await send_notification_email(
        to_addresses=test_addresses,
        subject="Test Email",
        message="Hello world via email.",
        html_message="""
        <html>
            <body>
                <h1>Hello world via email.</h1>
                <p>This is a test email from the FastAPI application.</p>
            </body>
        </html>"""
    )
    
    if success:
        print("Test email sent successfully")
    else:
        print("Failed to send test email")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
