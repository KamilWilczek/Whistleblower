from dotenv import load_dotenv
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import os
from os.path import basename
import smtplib
import ssl
import time

# literals from const.py
from const import EMAIL
from const import SERVER
from const import PORT

load_dotenv(verbose=True)


while True:

    PASSWORD = os.getenv("SYGNALY_MAIL_PASSWORD")  # Password from .env

    # connect to the server and go to its inbox
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)
    # we choose the inbox but you can select others
    mail.select("inbox")
    recipient_emails_list = ['wojciech.kulinski@igoriatrade.com', 'jaroslaw.lejko@igoriatrade.com', 'andrzej.zielinski@igoriatrade.com']  # Enter receiver address

    # we'll search using the ALL criteria to retrieve
    # every message inside the inbox
    # it will return with its status and a list of ids
    status, data = mail.uid("search", None, "UNSEEN")

    # in this variable number of new messages will be stored
    # n_messages = len(mail.uid('search',None, 'ALL'))

    # the list returned is a list of bytes separated
    # by white spaces on this format: [b'1 2 3', b'4 5 6']
    # so, to separate it first we create an empty list
    mail_ids = []

    # then we go through the list splitting its blocks
    # of bytes and appending to the mail_ids list
    for block in data:
        # the split function called without parameter
        # transforms the text or bytes into a list using
        # as separator the white spaces:
        # b'1 2 3'.split() => [b'1', b'2', b'3']
        mail_ids += block.split()

    for recipient in recipient_emails_list:

        # now for every id we'll fetch the email
        # to extract its content
        for i in mail_ids:
            # the fetch function fetch the email given its id
            # and format that you want the message to be
            status, data = mail.uid("fetch", i, "(RFC822)")

            # the content data at the '(RFC822)' format comes on
            # a list with a tuple with header, content, and the closing
            # byte b')'
            for response_part in data:
                # so if its a tuple...
                if isinstance(response_part, tuple):
                    # we go for the content at its second element
                    # skipping the header at the first and the closing
                    # at the third
                    message = email.message_from_bytes(response_part[1])

                    # with the content we can extract the info about
                    # who sent the message and its subject
                    mail_from = message["from"]
                    mail_subject = message["subject"]

                    # then for the text we have a little more work to do
                    # because it can be in plain text or multipart
                    # if its not plain text we need to separate the message
                    # from its annexes to get the text
                    if message.is_multipart():
                        mail_content = ""

                        # on multipart we have the text message and
                        # another things like annex, and html version
                        # of the message, in that case we loop through
                        # the email payload
                        for part in message.get_payload():
                            # if the content type is text/plain
                            # we extract it
                            if part.get_content_type() == "text/plain":
                                mail_content += part.get_payload()
                    else:
                        # if the message isn't multipart, just extract it
                        mail_content = message.get_payload()

                    # getting attachments
                    att_list = list(message.walk())
                    # empty list for attachment content
                    att_content_list = []
                    filename_list = []

                    for part in att_list:
                        if part.get_filename() != None:
                            filename_list.append(part.get_filename())
                        print(filename_list)
                        if bool(filename_list):
                            att_content_list.append(part.get_payload(decode=True))

                    # sending mail
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(SERVER, PORT, context=context) as server:
                        message = f"{mail_content}"
                        message_content = MIMEText(message, "plain")
                        msg = MIMEMultipart()
                        msg["Subject"] = mail_subject
                        msg["From"] = EMAIL
                        msg["To"] = recipient
                        msg.attach(message_content)

                        for att_content in range(len(att_content_list)):
                            att = MIMEBase("application", "octet-stream")
                            att.set_payload(att_content_list[att_content])
                            encoders.encode_base64(att)
                            att.add_header(
                                "Content-Disposition",
                                "attachment; filename= %s"
                                % basename(filename_list[att_content]),
                            )
                            msg.attach(att)

                        server.login(EMAIL, PASSWORD)
                        server.send_message(msg)

                    # for SMTP to catch breath
                    time.sleep(5)
    print("I'm alive!")
    time.sleep(60)
