"""Seperate module for e-mail notifications"""
from VisitorManagementApp import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from visitorsite import models

from django.contrib.auth.models import User

EMAILSTRING = "emailnotification.html"

def _send_notification(site:str, visit:models.RidgefieldVisit):
    # Site name should be capitalized since all groups in this application start with a capital letter
    managerstosend = [i.email for i in User.objects.filter(groups__name=site.capitalize())]
    context = {
        "site" : site.capitalize(),
        "visitorname" : "{} {}".format(visit.visitor.first_name, visit.visitor.last_name),
        "role" : visit.visitor.role.name,
        "arrival" : str(visit.arrival),
        "departure" : str(visit.departure),
        # if visit.paddock is referenced and the site is not ridgefield, the server will have an error
        "ridgefield_paddock" : None if (site != "ridgefield") else visit.paddock,
        "emname" : visit.visitor.emname,
        "emphone" : visit.visitor.emphone,
        "emrelation" : visit.visitor.emrelation
    }
    email_formatted = render_to_string(EMAILSTRING, context)
    kwargs = {
        "subject": "New visitor at {site}".format(site = site.capitalize()),
        
        "html_message" : email_formatted,
        "message" : strip_tags(email_formatted),

        "recipient_list" : managerstosend,
        "fail_silently": False,
        "from_email":settings.EMAIL_HOST_USER
    }
    send_mail(**kwargs)