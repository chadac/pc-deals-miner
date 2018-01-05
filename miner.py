#!/usr/bin/env python3

import praw
import os
import re
import smtplib
from email.mime.text import MIMEText
import secrets
import filters
import requests
from bs4 import BeautifulSoup

reddit = praw.Reddit(client_id=secrets.CLIENT_ID,
                     client_secret=secrets.CLIENT_SECRET,
                     user_agent='pcdeals-miner:1.0 (by /u/ChadtheWad)')
subreddit = reddit.subreddit('buildapcsales')
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'}


def is_valid_submission(submission):
    return not submission.selftext


def webpage(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    return soup


def find(pattern, text):
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


class Item:
    def __init__(self, submission):
        title = submission.title.strip()
        self.comments_link = 'https://reddit.com' + submission.permalink
        self.link = submission.url
        self.title = title
        self.content = title
        self.group = find("\[(.+)\]", title).lower().replace(' ', '')
        try:
            self.price = float(find("\$(\d+(\.\d+)?)", title))
        except TypeError:
            self.price = None

        try:
            soup = webpage(self.link)
            for tag in soup.find_all("meta"):
                prop = tag.get("property", "description")
                if not prop or "description" in prop or "keywords" in prop:
                    self.content += " " + tag.get("content", "")
        except Exception as e:
            print("Exception occurred while loading web content:")
            import traceback
            traceback.print_exc()
            print("URL:", self.link)
        self.content = self.content.lower().replace(' ', '')

    @property
    def email_subject(self):
        return "/r/buildapcsales Price Alert: {}".format(self.title)

    @property
    def email_content(self):
        return """
<p>Hi Chad,</p>

<p>I found a new deal on <a href="https://reddit.com/r/buildapcsales">/r/buildapcsales</a> that might interest you:</p>

<h2><a href="{3}" target="_blank">{0}</a></h2>

<h3><a href="{4}" target="_blank">Discuss on Reddit</a></h3>
""".format(self.title, self.group, self.price, self.link, self.comments_link)

    def __repr__(self):
        return self.title


def send_email(item):
    smtp = smtplib.SMTP("smtp.mailgun.org", 587)
    smtp.login(secrets.SMTP_USER, secrets.SMTP_PASS)
    message = MIMEText(item.email_content, 'html')
    message['From'] = secrets.SMTP_FROM
    message['To'] = secrets.SMTP_SEND_TO
    message['Subject'] = item.email_subject

    msg_full = message.as_string()
    smtp.sendmail(secrets.SMTP_USER, secrets.SMTP_SEND_TO, msg_full)
    smtp.quit()



old_ids = []
if os.path.exists('.last-posts'):
    with open('.last-posts', 'r') as f:
        old_ids = f.read().split("::")

new_ids = []
for submission in subreddit.new(limit=20):
    new_ids += [str(submission.id)]
    if str(submission.id) in old_ids:
        continue
    if is_valid_submission(submission):
        item = Item(submission)
        if filters.matches(item):
            print("Match for", item)
            send_email(item)


with open('.last-posts', 'w') as f:
    f.write('::'.join(new_ids))
