import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


class EmailService:
    """邮件服务"""
    
    @staticmethod
    async def send_test_completion_email(
        to_email: str,
        test_name: str,
        test_id: int,
        status: str,
        total_score: float = None
    ):
        """发送测试完成邮件"""
        
        if not settings.smtp_user or not settings.smtp_password:
            print("SMTP not configured, skipping email")
            return
        
        subject = f"AI模型测试完成 - {test_name}"
        
        body = f"""
        <html>
        <body>
            <h2>AI模型测试平台 - 测试完成通知</h2>
            <p>您的测试任务已完成，详情如下：</p>
            <ul>
                <li><strong>测试名称：</strong>{test_name}</li>
                <li><strong>测试ID：</strong>{test_id}</li>
                <li><strong>测试状态：</strong>{status}</li>
                {f'<li><strong>总分：</strong>{total_score}</li>' if total_score else ''}
            </ul>
            <p>请登录平台查看详细测试报告。</p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = settings.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=settings.smtp_tls
            )
            print(f"Email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
