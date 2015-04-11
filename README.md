This tool searches W3C mailing list archives for a given public mailing
list and produces a mailbox containing the email relevant to that
specification, by searching for the specification's shortname in email.

It decides what to do based on interactive input.  For example, the
following input and output:
```
W3C Public mailing list: www-style
Start year: 2013
Start month: 1
End year: 2015
End month: 4
search term (enter to finish): css3-transitions
search term (enter to finish): css-transitions
search term (enter to finish): 
Destination mailbox file: transitions-doc
```
will go through the www-style mailing list, and write messages referencing
css-transitions or css3-transitions (and messages in reply to those
messages) to the file transitions-doc, which is a mailbox that can be
read by many desktop email clients.

