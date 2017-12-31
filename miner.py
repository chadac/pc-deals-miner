#!/usr/bin/env python3

import praw
import os
import re
import smtplib
from email.mime.text import MIMEText
import secrets
import filters

reddit = praw.Reddit(client_id=secrets.CLIENT_ID,
                     client_secret=secrets.CLIENT_SECRET,
                     user_agent='pcdeals-miner:1.0 (by /u/ChadtheWad)')
subreddit = reddit.subreddit('buildapcsales')


last_id = None
if os.path.exists('.last-post'):
    with open('.last-post', 'r') as f:
        last_id = f.read()


def is_valid_submission(submission):
    return not submission.selftext


def find(pattern, text):
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


class Item:
    def __init__(self, submission):
        title = submission.title.strip()
        self.comments_link = submission.permalink
        self.link = submission.url
        self.title = title
        self.content = title.replace(' ', '').lower()
        self.group = find("\[(.+)\]", title).lower()
        try:
            self.price = float(find("\$(\d+(\.\d+)?)", title))
        except TypeError:
            self.price = None

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


new_last_id = None
for submission in subreddit.new(limit=20):
    if not new_last_id:
        new_last_id = submission.id
    if str(submission.id) == last_id:
        break
    if is_valid_submission(submission):
        item = Item(submission)
        if filters.matches(item):
            print("Match for", item)
            send_email(item)


with open('.last-post', 'w') as f:
    f.write(new_last_id)
