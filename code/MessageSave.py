#!/usr/bin/python3

"""
MessageSave.py holds the functions to save messages and attachments.
It reads every line in the data and determines the message header,
message body, MIME header and MIME body. If the message body or MIME body
is base64 encoded, MessageSave will decode the message. Afterwards,
the message body is broken into the message body and attachments,
and saved into a new directory (directory name is generated by MessageSave.)

You need to review this code first and complete all missing sections. Replace
all '''Fill in''' with your code.
"""

import datetime
import calendar
import re
import base64
from pathlib import Path
from io import StringIO
import os


def parse_headers(data):
    format = {
        'Content-Type': 'list',
        'Content-Disposition': 'list'
    }
    lines = []

    for line in data:
        line = line.strip()
        if line == '':
            break
        if ':' in line:
            lines.append(line)
        else:
            lines[-1] += line

    headers = {}
    for line in lines:
        spt = line.split(':')
        key = spt[0].strip()
        if format.get(key) == 'list':
            value = [x.strip() for x in spt[1].split(';')]
        else:
            value = spt[1].strip()
        headers[key] = value

    return headers

# Class to save the message and attachment
class MessageSave:
    CRLF = '\r\n'

    # constructor
    def __init__(self, From, To, wholeBody):
        # sender of the message
        self.From = From
        # receiver of the message
        self.To = To
        # the body of message
        self.raw_data = wholeBody

    @property
    def save(self):
        Body = "From: " + self.From + self.CRLF + "To: " + self.To + self.CRLF
        # Use StringIO to read string as a file
        data = StringIO(self.raw_data)

        encoding = ''
        mime = False
        multipart = False
        plain_text = False
        content_type = None

        # Boolean flags for header processing
        is_header = True

        # boundary identification string
        boundary = ''
        # Sting for encoded message body
        encoded_body = ''
        # directory for saving files
        directory = self.FindVacancy('../emails/', 'email')

        # String for attachment appendix
        attachments = []
        # String for filename to be saved
        file_name = ''
        # Create the directory
        Path(directory).mkdir(parents=True)

        # Read the message header for the parameters used in this Email
        headers = parse_headers(data)
        print('Headers', headers)
        Body += "From: " + headers['From'] + self.CRLF
        Body += "To: " + headers['To'] + self.CRLF
        Body += "Subject: " + headers['Subject'] + self.CRLF

        for parameter in headers['Content-Type']:
            # Check if this tag talks about boundary
            if re.fullmatch('boundary=.+', parameter):
                boundary = parameter[parameter.find("\"") + 1:parameter.rfind("\"")]
            # Check if this tag talks about multipart
            elif re.fullmatch('multipart/mixed', parameter):
                multipart = True
            # Check if this tag talks about text/plain
            elif re.fullmatch('text/plain', parameter):
                plain_text = True
            else:
                print("Unprocessed parameter in Content-Type:", parameter)
        encoding = headers.get('Content-Transfer-Encoding')
        mime = 'MIME-Version' in headers

        print('headers:', Body)

        # Separate the message header with actual message content
        Body += "-------------------------------------------------" + self.CRLF

        # If the above while loop do processing header, discard them
        if is_header:
            encoded_body = ''

        # This while loop crops the non-MIME parts in MIME email
        while True:
            data_line = data.readline().strip()
            if not boundary and data_line == '':
                break
            # Check if we meet the boundary in MIME message
            if mime and data_line[:2] == '--' and data_line[2:] == boundary:
                break
            # if the Email is non-MIME, Single Part or without header, save the body
            encoded_body += data_line + self.CRLF

        # Do it only if the Email is non-MIME, Single Part or without header
        if not multipart or not mime or not is_header:
            # If it is base64 encoded, decode it and place it at message.txt
            if encoding == 'base64' and len(encoded_body) > 0:
                print(encoded_body)
                Body += base64.b64decode(encoded_body).decode()
            else:
                Body += encoded_body
        # This block is only for Multipart Message
        else:
            # A flag to indicate MIME-style message.txt is filled or not
            bodyFilled = False
            # Reset the encodedBody
            encoded_body = ''

            # This while loop loops for each part
            while True:
                if is_header:
                    headers = parse_headers(data)
                    if len(headers) == 0:
                        break

                    print('Headers', headers)
                    for parameter in headers['Content-Type']:
                        # If this part is text/plain or not
                        if parameter == 'text/plain':
                            plain_text = True
                        elif parameter == 'application/octet-stream':
                            encoding = 'base64'
                        else:
                            print("Unprocessed parameter in Content-Type:", parameter)
                    mime = 'MIME-Version' in headers
                    encoding = headers.get('Content-Transfer-Encoding') or encoding
                    is_header = False
                    disposition = headers.get('Content-Disposition') or headers.get('Content-Type')
                    if disposition:
                        if type(disposition) == str:
                            disposition = [disposition]
                        for e in disposition:
                            if e.startswith('filename') or e.startswith('name'):
                                file_name = e[e.find("\"") + 1:e.rfind("\"")]

                    # If this part doesn't give the filename, use "Attachment" as default
                    file_name = file_name or "Attachment"

                data_line = data.readline().strip()
                if data_line == '':
                    continue
                if data_line == '.':
                    break
                # We hit the boundary, it is the time to save the attachment
                if data_line == ("--" + boundary) or data_line == ("--" + boundary + "--") or data_line == boundary:
                    # If this part is using un-supported encoding method
                    if encoding not in ['base64', '7bit']:
                        # Display a line in message.txt to indicate this attachment encounters problem
                        attachments.append(file_name + ' (discarded due to unknown encoding method)')

                    # If this part is the first MIME-style text message, serve it as message body
                    # (This part should be no attachment filename and Content-type is text/plain)
                    elif not bodyFilled and plain_text:
                        print("Writing text")
                        bodyFilled = True
                        if encoding == 'base64':
                            Body += base64.b64decode(encoded_body).decode()
                        else:
                            Body += encoded_body
                    # For other supported attachment, process it here
                    else:
                        print("Writing attachment", file_name)
                        attachments.append(file_name)
                        with Path(os.path.join(directory, file_name)).open('wb') as f:
                            if encoding == 'base64':
                                f.write(base64.b64decode(encoded_body))
                            else:
                                f.write(encoded_body.encode())

                    # Reset the necessary flags and variable for next MIME part.
                    plain_text = False
                    is_header = True
                    encoded_body = ''
                    file_name = ''
                # In normal case, just accumulate the string read
                else:
                    encoded_body += data_line + self.CRLF

        # Finally we save the message body to message.txt
        # Append the attachment information at the end of the message.txt
        if multipart and mime:
            Body += self.CRLF + "-------------------------------------------------" + self.CRLF + "File(s) of Attachment :" + self.CRLF + self.CRLF.join(
                attachments)
            print("multipart and mime=" + str(multipart) + " " + str(mime))
            print("attachment=" + self.CRLF.join(attachments))

        # Open the message.txt file and write it
        with Path(os.path.join(str(directory), 'message.txt')).open('wb') as f:
            print("Writing body", Body)
            f.write(Body.encode())

        return True

    # This method find out the next available directory/file name
    def FindVacancy(self, path, prefix):
        counter = 0
        extension = ''

        if prefix == '':
            entry = Path(os.path.join(path, self.Today() + '_' + str(counter)))
        else:
            entry = Path(os.path.join(path, prefix))

        if prefix.rfind('.') >= 0:
            extension = prefix[prefix.rfind('.'):]
            prefix = prefix[:prefix.rfind('.')]

        while entry.exists():
            counter = counter + 1
            if prefix == '':
                entry = Path(os.path.join(path, self.Today() + '_' + str(counter)))
            else:
                entry = Path(os.path.join(path, prefix + '_' + str(counter) + extension))
        return entry.resolve()

    # This method return the date in simple DDMMM format
    def Today(self):
        now = datetime.datetime.now()
        monthAbbr = calendar.month_abbr[now.month]
        return str(now.day) + monthAbbr
