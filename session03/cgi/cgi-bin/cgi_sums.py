#!/usr/bin/env python
import cgi
import cgitb

cgitb.enable()

form = cgi.FieldStorage()
operands = form.getlist('operand')
msg = "your total is {total}"
try:
    total = sum(map(int, operands))
    msg = msg.format(total=total)
except (ValueError, TypeError):
    msg = "Unable to calculate a sum, please provide integer operands"

print("Content-Type: text/plain")
print("Content-Length: %s" % len(msg))
print()
print(msg)
