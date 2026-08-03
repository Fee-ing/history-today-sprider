# main.py

import requests
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import os
import json
import base64
from dotenv import load_dotenv
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python < 3.9

URL = "https://baike.baidu.com/cms/home/eventsOnHistory/"

load_dotenv()

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

GH_PAT = os.environ.get("GH_PAT")
GH_REPO = os.environ.get("GH_REPO")  # 格式: owner/repo


def crawl_data():
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    month = now.strftime('%m')
    day = now.strftime('%d')
    api_url = f"{URL}{month}.json"

    print(api_url)

    headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
      response = requests.get(api_url, headers=headers)
      response.raise_for_status()
      data = response.json()
      
      # 获取今日事件并倒序（从远到近）
      events = data[month][f"{month}{day}"]
      return events[::-1]
    
    except Exception as e:
      print(f"数据获取失败：{e}")
      return None


def send_email(data_list):
  if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
    print(
      "错误：环境变量 EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER 未设置完整。"
    )
    return

  # 解析多个收件人
  EMAIL_RECEIVER_LIST = [
    email.strip() for email in EMAIL_RECEIVER.split(",") if email.strip()
  ]

  if not EMAIL_RECEIVER_LIST:
    print("错误：未设置有效的收件人地址。")
    return

  smtp_server = "smtp.qq.com"
  smtp_port = 465

  today = datetime.now().strftime("%m月%d日")

  for receiver in EMAIL_RECEIVER_LIST:
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("历史上的今天", EMAIL_SENDER))
    msg["To"] = receiver
    msg["Subject"] = Header(f"历史上{today}发生了{len(data_list)}个著名事件")

    events_html = ""
    if data_list:
      for idx, item in enumerate(data_list):
        year = item.get("year", "")
        title = item.get("title", "")
        link = item.get("link", "")
        desc = item.get("desc", "")
        
        events_html += f"""
        <div class="event-card">
          <div class="event-year">{year}</div>
          <div class="event-content">
            <h3 class="event-title">{title}</h3>
            {f'<p class="event-desc">{desc}</p>' if desc else ''}
            {f'<a href="{link}" class="event-link" target="_blank">查看详情 →</a>' if link else ''}
          </div>
          </div>
        """

    page_html = f"""
    <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>历史上的今天</title>
        <style type="text/css">
          * {{ margin: 0; padding: 0;box-sizing: border-box; }}
          a,
          a:link,
          a:visited,
          a:hover,
          a:active,
          a:focus {{
            outline: 0;
            background-color: transparent;
            text-decoration: none;
            -webkit-tap-highlight-color:rgba(0,0,0,0);
            -webkit-tap-highlight-color: transparent;
          }}
          ::-webkit-scrollbar {{ width: 6px; }}
          ::-webkit-scrollbar-track {{ background: #ffffff; border-radius: 3px; }}
          ::-webkit-scrollbar-thumb {{ background: #f1f5f9; border-radius: 3px; }}
          html, body {{ width: 100%; height: 100%; overflow: hidden; }}
          body {{ overflow-y: auto;scroll-behavior: smooth; }}
          .container {{
            max-width: 680px;
            margin: 0 auto;
            padding: 20px;
          }}
          
          /* 头部 */
          .header {{
            text-align: center;
            padding: 40px 20px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            margin-bottom: 24px;
            color: #ffffff;
          }}
          .header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
          }}
          .header .date {{
            font-size: 16px;
            opacity: 0.9;
            font-weight: 500;
          }}
          .header .count {{
            display: inline-block;
            margin-top: 12px;
            padding: 6px 16px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            font-size: 14px;
          }}
          
          /* 事件卡片 */
          .event-card {{
            background: #ffffff;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            display: flex;
            gap: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
          }}
          .event-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
          }}
          
          .event-year {{
            flex-shrink: 0;
            width: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 700;
            line-height: 1;
            display: flex;
            align-items: center;
            justify-content: center;
          }}
          
          .event-content {{
            flex: 1;
            min-width: 0;
          }}
          .event-title {{
            font-size: 16px;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 8px;
            line-height: 1.5;
          }}
          .event-desc {{
            font-size: 14px;
            color: #718096;
            margin-bottom: 10px;
            line-height: 1.6;
          }}
          .event-link {{
            display: inline-block;
            font-size: 13px;
            color: #667eea;
            font-weight: 500;
          }}
          .event-link:hover {{
            color: #764ba2;
          }}
          
          /* 底部 */
          .footer {{
            text-align: center;
            padding: 30px 20px;
            color: #a0aec0;
            font-size: 12px;
          }}
          .footer p {{
            margin-bottom: 6px;
          }}
          
          /* 移动端适配 */
          @media only screen and (max-width: 600px) {{
            .container {{
              padding: 12px;
            }}
            .header {{
              padding: 30px 16px 24px;
              border-radius: 12px;
            }}
            .header h1 {{
              font-size: 22px;
            }}
            .header .date {{
              font-size: 14px;
            }}
            .event-card {{
              flex-direction: column;
              padding: 16px;
              gap: 12px;
            }}
            .event-year {{
              width: 100%;
              height: 40px;
              font-size: 14px;
            }}
            .event-title {{
              font-size: 15px;
            }}
            .event-desc {{
              font-size: 13px;
            }}
          }}
          
          /* 空状态 */
          .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #a0aec0;
          }}
          .empty-state .icon {{
            font-size: 48px;
            margin-bottom: 16px;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>📜 历史上的今天</h1>
            <div class="date">{today}</div>
            <div class="count">共 {len(data_list) if data_list else 0} 条历史著名事件</div>
          </div>
          
          <div class="events">
            {events_html if events_html else '''
            <div class="empty-state">
              <div class="icon">📭</div>
              <p>暂无历史事件记录</p>
            </div>
            '''}
          </div>
          
          <div class="footer">
            <p>© 历史上的今天 · Powered by Fee</p>
            <p>数据来源：百度百科</p>
          </div>
        </div>
      </body>
      </html>
      """

    msg.attach(MIMEText(page_html, "html", "utf-8"))

    # 发送邮件
    try:
      server = smtplib.SMTP_SSL(smtp_server, smtp_port)
      server.login(EMAIL_SENDER, EMAIL_PASSWORD)
      server.sendmail(EMAIL_SENDER, [receiver], msg.as_string())
      print(f"✓ 邮件发送成功：{receiver}")
    except Exception as e:
      print(f"邮件发送失败: {e}")
    finally:
      server.quit()


def save_history_json(data_list, filepath="history.json"):
    """将爬取数据保存为本地 JSON 文件，返回格式化后的数据"""
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    timestamp = int(now.timestamp() * 1000)

    json_data = {
        "timestamp": timestamp,
        "data": data_list,
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"JSON 文件已保存：{filepath}")
    return json_data


def push_to_github_pages(json_data, filepath="history.json"):
    """将 history.json 推送到 GitHub 仓库的 master 分支"""
    if not all([GH_PAT, GH_REPO]):
        print("错误：环境变量 GH_PAT, GH_REPO 未设置完整。跳过推送。")
        return False

    headers = {
        "Authorization": f"token {GH_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 检查 master 分支是否存在
    branch_ref_url = f"https://api.github.com/repos/{GH_REPO}/git/refs/heads/master"
    branch_exists = False
    try:
        ref_response = requests.get(branch_ref_url, headers=headers)
        if ref_response.status_code == 200:
            branch_exists = True
            print("master 分支已存在")
        elif ref_response.status_code == 404:
            print("master 分支不存在，将自动创建")
        else:
            print(f"检查分支异常：{ref_response.status_code} {ref_response.text}")
    except Exception as e:
        print(f"检查分支异常：{e}")

    # 如果分支不存在，从默认分支创建 master
    if not branch_exists:
        try:
            # 获取仓库信息（默认分支名）
            repo_url = f"https://api.github.com/repos/{GH_REPO}"
            repo_response = requests.get(repo_url, headers=headers)
            if repo_response.status_code != 200:
                print(f"获取仓库信息失败：{repo_response.status_code} {repo_response.text}")
                return False
            default_branch = repo_response.json().get("default_branch", "main")

            # 获取默认分支最新 commit SHA
            ref_default_url = f"https://api.github.com/repos/{GH_REPO}/git/refs/heads/{default_branch}"
            ref_default_response = requests.get(ref_default_url, headers=headers)
            if ref_default_response.status_code != 200:
                print(f"获取默认分支失败：{ref_default_response.status_code}")
                return False
            base_sha = ref_default_response.json()["object"]["sha"]

            # 创建 master 分支
            create_branch_payload = {
                "ref": "refs/heads/master",
                "sha": base_sha
            }
            create_response = requests.post(
                f"https://api.github.com/repos/{GH_REPO}/git/refs",
                headers=headers,
                json=create_branch_payload
            )
            if create_response.status_code == 201:
                print("master 分支创建成功")
            else:
                print(f"创建分支失败：{create_response.status_code} {create_response.json()}")
                return False
        except Exception as e:
            print(f"创建分支异常：{e}")
            return False

    FILE_PATH = f"JSONs/{filepath}"  # 确保写入子目录
    api_url = f"https://api.github.com/repos/{GH_REPO}/contents/{urllib.parse.quote(FILE_PATH, safe='/')}"

    content = json.dumps(json_data, ensure_ascii=False, indent=2)
    content_bytes = content.encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')

    # 检查 master 分支上是否已存在该文件
    sha = None
    try:
        response = requests.get(f"{api_url}?ref=master", headers=headers)
        if response.status_code == 200:
            sha = response.json().get("sha")
            print(f"文件已存在，将更新（SHA: {sha[:7]}...）")
        elif response.status_code == 404:
            print("文件不存在，将创建新文件")
        else:
            print(f"检查文件状态异常：{response.status_code} {response.text}")
    except Exception as e:
        print(f"检查文件异常：{e}")

    # 创建或更新文件
    commit_message = f"Update history.json - {json_data.get('date', '')}"
    payload = {
        "message": commit_message,
        "content": content_base64,
        "branch": "master"
    }
    if sha:
        payload["sha"] = sha

    try:
        response = requests.put(api_url, headers=headers, json=payload)
        if response.status_code in (200, 201):
            print(f"✓ history.json 推送成功 → https://github.com/{GH_REPO}/blob/master/{filepath}")
            return True
        else:
            print(f"推送失败：{response.status_code} {response.json()}")
            return False
    except Exception as e:
        print(f"推送异常：{e}")
        return False


if __name__ == "__main__":
  print("开始爬取数据...")
  data = crawl_data()

  if data:
    print("数据爬取成功，正在处理...")

    # 1. 发送邮件
    send_email(data)

    # 2. 保存 JSON 并推送到 GitHub Pages
    json_data = save_history_json(data)
    push_to_github_pages(json_data)
  else:
    print("数据爬取失败，跳过后续操作。")
