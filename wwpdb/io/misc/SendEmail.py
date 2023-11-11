"""
Some functions to allow sending of email messages using the configuration
"""

import smtplib
from email.mime.text import MIMEText
import sys

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommunication
from wwpdb.utils.config.ConfigInfo import getSiteId


class SendEmail:
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__siteId = siteId if siteId is not None else getSiteId(defaultSiteId=siteId)

    def send_email(self, body, subject, to_email, from_email, relayhost="localhost"):
        """
        function to send email
        :param body: the body of the message
        :param subject: the subject of the message
        :param to_email: the to email address
        :param from_email: the from email address
        :param relayhost: The relayhost (defaults to localhost)
        :return: True if no errors, False if errors
        """
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email

            # Send the message via our own SMTP server, but don't include the envelope header.
            s = smtplib.SMTP(relayhost)
            send_errors = s.sendmail(from_email, [to_email], msg.as_string())  # return is dictionary of errors
            s.quit()

            if not send_errors:
                return True
        except Exception as e:
            self.__lfh.write("Failure to send message %s\n" % e)

        return False

    def send_system_error(self, body, subject):
        """Handles the sending of a system email message based on site-config
        Returns True on succss
        """

        ciac = ConfigInfoAppCommunication(self.__siteId, self.__verbose, self.__lfh)
        reply = ciac.get_noreply_address()
        relay = ciac.get_mailserver_name()
        dest = ciac.get_system_notification_address()

        status = self.send_email(body, subject, dest, reply, relay)
        if not status and self.__verbose:
            self.__lfh.write("Error: Failure to send system error\n")

        return status
