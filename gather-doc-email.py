#!/usr/bin/python

import datetime
import pycurl
import re

# Use pycurl as suggested in http://stackoverflow.com/a/1921551, since
# it actually does certificate checking, unlike httplib or urllib.
# See http://pycurl.sourceforge.net/doc/pycurl.html for pycurl docs.
def fetch_https_securely(url, destination, username=None, password=None):
    curl = pycurl.Curl()
    curl.setopt(pycurl.CAINFO, "/etc/ssl/certs/ca-certificates.crt")
    curl.setopt(pycurl.SSL_VERIFYPEER, 1)
    curl.setopt(pycurl.SSL_VERIFYHOST, 2)
    curl.setopt(pycurl.URL, url)
    io = open(destination, "w")
    curl.setopt(pycurl.WRITEFUNCTION, io.write)
    if username is not None or password is not None:
        curl.setopt(pycurl.USERPWD, username + ":" + password)
    curl.perform()

    respcode = curl.getinfo(pycurl.RESPONSE_CODE)
    io.close()
    if respcode != 200:
        raise StandardError("HTTP response code " + str(respcode) + " retrieving " + url)

def gather_archives(mailbox_url, search_terms, destination_mbox):
    # FIXME: WRITE ME
    print mailbox_url

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
    print search_terms
    destination_mbox = raw_input("Destination mailbox file: ")

    while current_date <= end_date:
        mailbox_url = "https://lists.w3.org/Archives/Public/{0}/mboxes/{1}.mbx".format(mailing_list, current_date.isoformat()[0:7])
        gather_archives(mailbox_url, search_terms, destination_mbox)

        # increment 31 days, and then set day-of-month back to 1
        current_date = current_date + datetime.timedelta(31)
        current_date = datetime.date(current_date.year, current_date.month, 1)
