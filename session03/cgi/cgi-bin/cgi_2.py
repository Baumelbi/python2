#!/usr/bin/env python
import cgi
import cgitb

cgitb.enable()
import os
import datetime

default = "No Value Present"
now = datetime.datetime.now()
print("Content-Type: text/html")
print()

body = """<html>
<head>
<title>Lab 1 - CGI experiments</title>
</head>
<body>
<p>Hey there, this page has been generated by {software}, running {script}</p>
<p>Today is {month} {date}, {year}.</p>
<p>This page was requested by IP Address {client_ip}</p>
</body>
</html>""".format(
    software=os.environ.get('SERVER_SOFTWARE', default),
    script=os.environ.get('SCRIPT_NAME', default),
    month=now.strftime('%B'),
    date=now.day,
    year=now.year,
    client_ip=os.environ.get('REMOTE_ADDR', default)
)
print(body)
