#!/usr/bin/python

import cStringIO
import datetime
import pycurl
import re
import io
import os
import os.path

# ~/.passwords.py must define two functions:
#   get_w3c_username()
#   get_w3c_password()
# each of which return a string
import imp
passwords = imp.load_source("passwords",
                            os.path.join(os.getenv("HOME"), ".passwords.py"))

# Use pycurl as suggested in http://stackoverflow.com/a/1921551, since
# it actually does certificate checking, unlike httplib or urllib.
# See http://pycurl.sourceforge.net/doc/pycurl.html for pycurl docs.
def fetch_https_securely(url, destio, username=None, password=None):
    """Write the resource at url into destio, verifying certificates
    correctly in the process."""
    curl = pycurl.Curl()
    curl.setopt(pycurl.CAINFO, "/etc/ssl/certs/ca-certificates.crt")
    curl.setopt(pycurl.SSL_VERIFYPEER, 1)
    curl.setopt(pycurl.SSL_VERIFYHOST, 2)
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.WRITEFUNCTION, destio.write)
    if username is not None or password is not None:
        curl.setopt(pycurl.USERPWD, username + ":" + password)
    curl.perform()

    respcode = curl.getinfo(pycurl.RESPONSE_CODE)
    if respcode != 200:
        raise StandardError("HTTP response code " + str(respcode) + " retrieving " + url)

def generate_messages(mailbox_string):
    """Given a mailbox as a string, generate the messages in
    that mailbox (each as a string)."""
    if mailbox_string == "":
        return
    if not mailbox_string[0:5] == "From ":
        raise StandardError("unexpected mailbox")
    message_start = 0
    while True:
        message_end = mailbox_string.find("\nFrom ", message_start + 5)
        if message_end == -1:
            break
        message_end = message_end + 1
        yield mailbox_string[message_start:message_end]
        message_start = message_end
    yield mailbox_string[message_start:]

def generate_headers(message_string):
    """Given an email message as a string, generate the sequence
    of [header_name, header_value] pairs for the email message."""
    header_name = None
    header_value = None
    for line in cStringIO.StringIO(message_string):
        if line[0:5] == "From ":
            if header_name is not None:
                raise StandardError("unexpected message format")
            continue
        # Continued header fields are always space or tab; see RFC 5322
        # sections 2.2 and 2.2.3.
        if line[0] == " " or line[0] == "\t":
            # Is there a correct way to normalize away the extra spaces?
            header_value += line
            continue
        # Yield what we found the last iteration.
        if header_name is not None:
            yield [header_name, header_value.rstrip("\n\r")]
        # RFC5322, section 2.1 says a blank line (terminated by CRLF)
        # separates the headers from the body.
        if line.rstrip("\n\r") == "":
            return
        colon_idx = line.find(":")
        if colon_idx == -1:
            raise StandardError("unexpected message header")
        header_name = line[0 : colon_idx]
        header_value = line[colon_idx + 1 : ].lstrip(" \t")
    # Yield the last header of a message with no body.
    yield [header_name, header_value.rstrip("\n\r")]

ws_re = re.compile("[ \t\n\r]+")
def gather_archives(mailbox_url, search_terms, destio):
    """Download the mailbox at mailbox_url, and write every message
    containing one of the terms in search_terms, or a message
    (transitively) in reply to one of those messages, to destio,
    the output mailbox stream."""

    io = cStringIO.StringIO()
    fetch_https_securely(mailbox_url, io,
                         username=passwords.get_w3c_username(),
                         password=passwords.get_w3c_password())
    month_message_str = io.getvalue()
    io.close()

    message_ids_included = set()
    for message in generate_messages(month_message_str):
        include = False
        message_id = None
        for [header_name, header_value] in generate_headers(message):
            header_name = header_name.lower()
            if header_name == "message-id":
                message_id = header_value
            elif header_name == "in-reply-to:":
                if not include:
                    if header_value in message_ids_included:
                        # This is a reply to a message in our set.
                        include = True
            elif header_name == "references":
                if not include:
                    for reference in ws_re.split("header_value"):
                        if reference in message_ids_included:
                            # This is a reply to a message in our set.
                            include = True
                            break
        if not include:
            for term in search_terms:
                if message.find(term) != -1:
                    include = True
                    break
        if include:
            message_ids_included.add(message_id)
            destio.write(message)

def validate_year(s):
    result = int(s)
    if result < 1980:
        raise StandardError("year predates W3C archives")
    return result

def validate_month(s):
    result = int(s)
    if result < 1 or result > 12:
        raise StandardError("invalid month")
    return result

if __name__ == '__main__':
    mailing_list = raw_input("W3C Public mailing list: ")
    if not re.match("^[a-z0-9-]*$", mailing_list):
        raise StandardError("unexpected characters in mailing list")
    start_year = validate_year(raw_input("Start year: "))
    start_month = validate_month(raw_input("Start month: "))
    end_year = validate_year(raw_input("End year: "))
    end_month = validate_month(raw_input("End month: "))
    current_date = datetime.date(start_year, start_month, 1)
    end_date = datetime.date(end_year, end_month, 1)
    if end_date > datetime.date.today() + datetime.timedelta(1):
        raise StandardError("end date is in the future")
    if current_date > end_date:
        raise StandardError("start date is after end date")
    search_terms = []
    while True:
        term = raw_input("search term (enter to finish): ")
        if not term:
            break
        search_terms.append(term)
    destination_mbox = raw_input("Destination mailbox file: ")

    if os.path.exists(destination_mbox):
        raise StandardError("destination file {0} exists".format(destination_mbox))
    destio = open(destination_mbox, "w")

    while current_date <= end_date:
        mailbox_url = "https://lists.w3.org/Archives/Public/{0}/mboxes/{1}.mbx".format(mailing_list, current_date.isoformat()[0:7])
        gather_archives(mailbox_url, search_terms, destio)

        # increment 31 days, and then set day-of-month back to 1
        current_date = current_date + datetime.timedelta(31)
        current_date = datetime.date(current_date.year, current_date.month, 1)

    destio.close()
