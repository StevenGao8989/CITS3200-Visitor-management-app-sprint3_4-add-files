from django.shortcuts import render, redirect

from django.contrib import messages # flash messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from django.urls import reverse_lazy

from .globals import *

from . import models, forms

from datetime import datetime

from visitorsite.emailservice import _send_notification


# FUNCTIONS USED MULTIPLE TIMES
# ============================================================

# Django converts the domain part of the email to lower case (base_user.py line 20, normalize_email)
# for bulk-registration attempts that do not bind to a User object, normalise the e-mail address
# as if it were part of the User object. This will make the site manager page more consistent
def normaliseEmail(x:str):
    # the first part should include @ because we cannot lower this (for safety)
    return x[:x.rfind('@') + 1] + x[x.rfind('@') + 1:].lower()

def registerNewVisitor(visitor:forms.VisitorProfileForm, userprofile:bool = True):
    # create user object first
    user = None
    if (userprofile):
        user = User.objects.create_user(
            username = visitor["username"],
            email=visitor["email"],
            password=visitor["password"] # password is hashed upon constructing the object
        )
        user.first_name = visitor["first_name"]
        user.last_name = visitor["last_name"]

        user.save()
    
    # create the emergency contact
    newEmergencyContact = models.EmergencyContact.objects.create(
        name = visitor["emergencyname"],
        phone = visitor["emergencyphone"],
        relationship = visitor["relationship"]
    )

    newEmergencyContact.save()

    # create the visitor
    newVisitor = models.Visitor.objects.create(
        user = user,
        first_name = visitor["first_name"],
        last_name = visitor["last_name"],
        email = normaliseEmail(visitor["email"]),
        phone_number=visitor["phone"],
        role=models.Role.objects.filter(name=visitor["role"]).first(),
        emergencycontact = newEmergencyContact
        )
    newVisitor.save()

    return newVisitor # return for team registration function

def registerNewVisit(site, visit:forms.VisitForm, visitors:list):
    """
    registerNewVisit takes in a cleaned visit form and a list
    of visitors. A list of visitors instead of one visitor is
    specified so that this function can be used for bulk registration.
    The function can be called once with all the team members for bulk
    registration which would make the code look more tidy in the bulk
    registration function.
    """

    visitorm = None

    if (site == "ridgefield"):
        visitorm = models.RidgefieldVisit
    elif (site == "gingin"):
        visitorm = models.GinginVisit

    if (visitorm == None): # back-end developer hired by the client might not have done their job
        raise ValueError("{} could not be converted into a Visit-derived model (did you forget to make it)?".format(site))
    
    for visitor in visitors:
        kwargs = {
            "visitor" : visitor,
            "arrival" : datetime.combine(visit["arrivaldate"], visit["arrivaltime"]),
            "departure" : datetime.combine(visit["departuredate"], visit["departuretime"]),
            "induction" : visit["induction"],
            "houserules" : visit["houserules"],
            "overnight" : visit["overnight"],
        }
        if (site == "ridgefield"): kwargs.update({"paddock": visit["paddock"]})
        
        # unpack arguments with **kwargs
        newVisit = visitorm.objects.create(**kwargs)
        newVisit.save()

        # finally, notify the site manager
        _send_notification(site, newVisit)
    
# ============================================================

# ROUTES
# ============================================================

# General
# ------------------------------------------------------------
def index(request):
    if (request.user.is_authenticated): return redirect(account)
    return render(request, "index.html", {"logged_in" : request.user.is_authenticated})
# ------------------------------------------------------------

# Logged out forms
# ------------------------------------------------------------
def register(request):
    if (request.method == "GET"):
        # if the user had authenticated, no need to log in again
        if (request.user.is_authenticated):
            return redirect(account)
        else: # is not authenticated
            visitorForm = forms.VisitorProfileForm()
        
    if (request.method == "POST"): # user submitted a form
        visitorForm = forms.VisitorProfileForm(request.POST)
        if visitorForm.is_valid(): # the form contains no errors
            if User.objects.filter(username = visitorForm.cleaned_data["username"]).exists():
                # username existed
                messages.error(request, "The username already exists!")
            else: # username does not exist
                registerNewVisitor(visitorForm.cleaned_data)
                messages.success(request, "Success! Please login with your credentials.")
                return redirect(login)
        else: # other form errors
            messages.error(request, "Form is not valid!")

    context = {
        "logged_in" : False, # always false if we need to log in
        "form" : visitorForm,
        "title" : "Register here",
        "desc" : "Register to use this electronic visitor registration system",
        "submit_button_value" : "Register",
    }

    return render(request, BASICFORMTEMPLATE, context)

def login(request):
    # if logged in, no need to log in again
    if (request.user.is_authenticated): return redirect(account)

    if (request.method == "GET"):
        visitorLogin = forms.VisitorLoginForm()

    if (request.method == "POST"): # user submitted the form
        visitorLogin = forms.VisitorLoginForm(request.POST)
        if visitorLogin.is_valid(): # no errors
            # attempt to authenticate with Django
            user = auth.authenticate(
                username = visitorLogin.cleaned_data["username"],
                password = visitorLogin.cleaned_data["password"]
                )
            if user is not None: # successful authentication
                auth.login(request, user)
                return redirect(account)
            else: # either username or pasword is wrong (Django does not specify)
                messages.error(request, "Username or password is wrong!")
        else: # CSRF attack or otherwise
            messages.error(request, "Form is not valid!")
    
    context = {
        "logged_in" : False, # always false if we need to log in
        "form" : visitorLogin,
        "title" : "Login here",
        "desc" : "Login to the electronic registration system here",
        "submit_button_value" : "Login"
    }

    return render(request, BASICFORMTEMPLATE, context)

# Logged in forms
# ------------------------------------------------------------
@login_required
def logout(request):
    auth.logout(request)
    messages.success(request, "You've been logged out!")
    return redirect(index)

@login_required
def account(request):
    if (request.user.is_staff): # Site managers go to the admin page
        return redirect(reverse_lazy("admin:index"))
    else: # Visitors go to the account page
        return render(request, "account.html", {
            "logged_in" : True,
            "name" : f"{request.user.first_name} {request.user.last_name}"
        })

@login_required
def deleteaccount(request):
    # deleting the user will automatically delete the visitor
    # and log out   
    if (request.method == "POST"):
        models.Visitor.objects.get(user = request.user).delete()
        request.user.delete()
        messages.success(request, "Your account has been deleted!")
        return redirect(index)
    context = {"logged_in": True, "name": f"{request.user.first_name} {request.user.last_name}"}
    return render(request, "deleteconfirmation.html", context)


@login_required
def changedetails(request):
    if (request.user.is_staff): 
        # SITE MANAGER REDIRECT TO ADMIN PAGE
        return redirect(reverse_lazy("admin:index"))
        
    if (request.method == "GET"):
        passwordForm = forms.VisitorProfileFieldsChangeForm()
    elif (request.method == "POST"):
        passwordForm = forms.VisitorProfileFieldsChangeForm(request.POST)
        if (passwordForm.is_valid()):
            for (field, value) in passwordForm.cleaned_data.items():
                # ignore empty fields
                if (value == "" or value == None): continue
                # remaining fields are attached to the Visitor object
                visitor = models.Visitor.objects.get(user = request.user)
                if (field == "first_name"): 
                    request.user.first_name = value
                    visitor.first_name = value
                elif (field == "last_name"): 
                    request.user.last_name = value
                    visitor.last_name = value
                elif (field == "email"): 
                    request.user.email = value
                    visitor.email = value
                elif (field == "role"):
                    visitor.role = value
                elif (field == "phone"):
                    visitor.phone_number = value
                
                visitor.save()
                request.user.save() # save each iteration
            messages.success(request, "Successfully changed specified fields!")
            return redirect(account)

        else:
            messages.error(request, "Form is not valid!")
    context = {
            "logged_in": True,
            "form" : passwordForm,
            "title" : "Change your details here",
            "desc" : "Leave fields you do not want to change blank",
            "submit_button_value": "Change details"
        }
    return render(request, BASICFORMTEMPLATE, context)
    

@login_required       
def password(request):
    if (request.user.is_staff): 
        # Admin has own password change form
        return redirect(reverse_lazy("admin:password_change"))

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Included so user isn't logged out 
            messages.success(request, 'Your password was successfully updated!')
            return redirect(account)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
        # BASICFORMTEMPLATE url (top of this document) will need to be changed 
        # after we figure out our routing ie profile/change_password,  
        # account/change_password etc

    context = {
        "form" : form,
        "logged_in" : True,
        "title" : "Change your password",
        "submit_button_value" : "Change password",
        "desc" : "Please enter a strong password as described below"
    }

    return render(request, BASICFORMTEMPLATE, context)

@login_required
def changeemergency(request):
    if (request.user.is_staff):
        # SITE MANAGER REDIRECT TO ADMIN PAGE
        return redirect(reverse_lazy("admin:index"))

    if (request.method == "GET"):
        ec = forms.VisitorEmergencyContactForm()
    elif (request.method == "POST"): # user submitted the form
        ec = forms.VisitorEmergencyContactForm(request.POST)
        if ec.is_valid():
            # attempt to remove the current contact if present
            visitor = models.Visitor.objects.get(user = request.user)
            if (visitor.emergencycontact != None):
                visitor.emergencycontact.delete()
                
            # create a new contact
            newEc = models.EmergencyContact.objects.create(
                name = ec.cleaned_data["name"],
                phone = ec.cleaned_data["phone"],
                relationship = ec.cleaned_data["relationship"]
            )
            newEc.save()

            # one-to-one relation with the new contact on the visitor
            visitor.emergencycontact = newEc
            visitor.save()

            messages.success(request, "Changed emergency contact!")
            return redirect(account)
        else:
            messages.error(request, "Form is not valid!")

    context = {
        "logged_in" : True,
        "title" : "Change Emergency Contact",
            "desc" : "Changing the contact will overwrite the previous contact",
        "submit_button_value" : "Change emergency contact",
        "form" : ec
    }
    return render(request, BASICFORMTEMPLATE, context)

@login_required
def transitionpage(request):
    if (request.user.is_staff): # Site managers go to the admin page
        return redirect(reverse_lazy("admin:index"))
    else: # Visitors go to the account page
        return render(request, "transitionpage.html", {
            "logged_in" : True,
            "name" : "{} {}".format(request.user.first_name, request.user.last_name),
            "sites": SITES
        })    

@login_required
def newvisit(request, site):
    """
    In this function, the specific site form is loaded depending on the GET
    argument provided. If the GET argument is invalid, an error message is generated
    and the function redirects back to the transition page.

    The context is adjusted so that a single HTML template (registervisit.html) can serve
    both sites even with different form requirements, which would reduce code maintenance and keep things simple.
    """
    if (request.user.is_staff): 
        # SITE MANAGER REDIRECT TO ADMIN PAGE
        return redirect(reverse_lazy("admin:index"))

    visit = None
    if (site == "ridgefield"):
        visit = forms.RidgefieldVisitForm(request.POST if (request.method == "POST") else None)
    elif (site == "gingin"):
        visit = forms.GinginVisitForm(request.POST if (request.method == "POST") else None)
    elif (visit == None):
        messages.error(request, "Could not generate form (did you specify an invalid site?)")
        return redirect(transitionpage)

    if (request.method == "POST"): # user submitted the form
        if visit.is_valid():
            # VISIT MODELS NOT DONE YET
            registerNewVisit(site, visit.cleaned_data, [models.Visitor.objects.get(user = request.user)])
            messages.success(request, "Added new visit! Site manager will be notified.")
            return redirect(account)
        else:
            messages.error(request, "Form is not valid!")

    context = {
            "logged_in" : True,
            "form" : visit,
            "site" : SITES[site]
        }
    return render(request, "registervisit.html", context)

def site_emergency_contacts(request):
    if (request.user.is_staff):
        # SITE MANAGER REDIRECT TO ADMIN PAGE
        return redirect(reverse_lazy("admin:index"))
    site_contacts = models.SiteEmergencyContact.objects.all()
    context = {'contacts': site_contacts, "logged_in" : request.user.is_authenticated}
    return render(request, "site_emergency_contact.html", context)
# ------------------------------------------------------------
# ============================================================


