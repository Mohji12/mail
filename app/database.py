import pymysql
from pymysql.cursors import DictCursor
import os
from datetime import datetime

# MySQL connection details
DB_HOST = os.getenv("DB_HOST", "16.16.70.205")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Newpassword123#")
DB_NAME = os.getenv("DB_NAME", "harish")

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=DictCursor,
        connect_timeout=10
    )

def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute('''
                CREATE TABLE IF NOT EXISTS email_campaigns (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    subject VARCHAR(255) NOT NULL,
                    total_attempted INT NOT NULL,
                    successful INT NOT NULL,
                    failed INT NOT NULL
                )
            ''')
        conn.commit()
    finally:
        conn.close()

def log_campaign(subject: str, total_attempted: int, successful: int, failed: int):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute('''
                INSERT INTO email_campaigns (timestamp, subject, total_attempted, successful, failed)
                VALUES (%s, %s, %s, %s, %s)
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), subject, total_attempted, successful, failed))
        conn.commit()
    finally:
        conn.close()

def get_analytics_summary():
    conn = get_connection()
    try:
        with conn.cursor() as c:
            # Overall totals
            c.execute('''
                SELECT 
                    COUNT(id) as total_campaigns,
                    SUM(total_attempted) as total_emails_attempted,
                    SUM(successful) as total_emails_sent,
                    SUM(failed) as total_emails_failed
                FROM email_campaigns
            ''')
            row = c.fetchone()

            total_campaigns = row['total_campaigns'] or 0
            total_emails_attempted = int(row['total_emails_attempted'] or 0)
            total_emails_sent = int(row['total_emails_sent'] or 0)
            total_emails_failed = int(row['total_emails_failed'] or 0)

            success_rate = 0.0
            if total_emails_attempted > 0:
                success_rate = round((total_emails_sent / total_emails_attempted) * 100, 2)

            # Today's report (server local date)
            c.execute('''
                SELECT
                    COUNT(id) as campaigns_today,
                    COALESCE(SUM(total_attempted), 0) as attempted_today,
                    COALESCE(SUM(successful), 0) as sent_today,
                    COALESCE(SUM(failed), 0) as failed_today
                FROM email_campaigns
                WHERE DATE(timestamp) = CURDATE()
            ''')
            today_row = c.fetchone()
            attempted_today = int(today_row['attempted_today'] or 0)
            sent_today = int(today_row['sent_today'] or 0)
            failed_today = int(today_row['failed_today'] or 0)
            success_rate_today = (
                round((sent_today / attempted_today) * 100, 2) if attempted_today > 0 else 0.0
            )

            # Campaigns sent today
            c.execute('''
                SELECT id, timestamp, subject, total_attempted, successful, failed
                FROM email_campaigns
                WHERE DATE(timestamp) = CURDATE()
                ORDER BY timestamp DESC
            ''')
            today_campaigns = c.fetchall()

            # Last 7 days daily breakdown
            c.execute('''
                SELECT
                    DATE(timestamp) as report_date,
                    COUNT(id) as campaigns,
                    COALESCE(SUM(total_attempted), 0) as attempted,
                    COALESCE(SUM(successful), 0) as sent,
                    COALESCE(SUM(failed), 0) as failed
                FROM email_campaigns
                WHERE timestamp >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
                GROUP BY DATE(timestamp)
                ORDER BY report_date DESC
            ''')
            daily_rows = c.fetchall()

            # Recent campaigns (last 20)
            c.execute('''
                SELECT id, timestamp, subject, total_attempted, successful, failed
                FROM email_campaigns
                ORDER BY timestamp DESC
                LIMIT 20
            ''')
            recent_campaigns = c.fetchall()

            def _fmt_camps(rows):
                out = []
                for camp in rows:
                    item = dict(camp)
                    if isinstance(item.get('timestamp'), datetime):
                        item['timestamp'] = item['timestamp'].isoformat()
                    attempted = int(item.get('total_attempted') or 0)
                    sent = int(item.get('successful') or 0)
                    item['success_rate'] = (
                        round((sent / attempted) * 100, 2) if attempted > 0 else 0.0
                    )
                    out.append(item)
                return out

            daily_breakdown = []
            for d in daily_rows:
                attempted = int(d['attempted'] or 0)
                sent = int(d['sent'] or 0)
                report_date = d['report_date']
                if hasattr(report_date, 'isoformat'):
                    report_date = report_date.isoformat()
                else:
                    report_date = str(report_date)
                daily_breakdown.append({
                    "date": report_date,
                    "campaigns": int(d['campaigns'] or 0),
                    "attempted": attempted,
                    "sent": sent,
                    "failed": int(d['failed'] or 0),
                    "success_rate": round((sent / attempted) * 100, 2) if attempted > 0 else 0.0,
                })

            return {
                "report_generated_at": datetime.now().isoformat(),
                "total_campaigns": total_campaigns,
                "total_emails_attempted": total_emails_attempted,
                "total_emails_sent": total_emails_sent,
                "total_emails_failed": total_emails_failed,
                "success_rate": success_rate,
                "today": {
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "campaigns": int(today_row['campaigns_today'] or 0),
                    "attempted": attempted_today,
                    "sent": sent_today,
                    "failed": failed_today,
                    "success_rate": success_rate_today,
                    "campaigns_list": _fmt_camps(today_campaigns),
                },
                "daily_breakdown": daily_breakdown,
                "recent_campaigns": _fmt_camps(recent_campaigns),
                "metric_guide": {
                    "campaigns": "Number of bulk send jobs run (one upload/send action = one campaign).",
                    "attempted": "Total recipient emails tried in those campaigns.",
                    "sent": "Emails accepted by ZeptoMail without an immediate send error.",
                    "failed": "Emails that failed during send (API/network/auth errors).",
                    "success_rate": "sent ÷ attempted × 100.",
                },
            }
    finally:
        conn.close()
