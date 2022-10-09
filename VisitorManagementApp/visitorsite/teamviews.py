from django.shortcuts import render, redirect

from django.contrib import messages # flash messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.forms import formset_factory

from django.urls import reverse_lazy

from .globals import *

from . import models
from . import forms

from visitorsite.views import account, registerNewVisitor, registerNewVisit

# ------------------------------------------------------------
"""First users will be presented with a single numeric field
to enter the number of members of a team. Then the user will be
redirected to register_team."""
@login_required
def teamregister(request):

    if (request.user.is_staff): # Site managers go to the admin page
        return redirect(reverse_lazy("admin:index"))
    
    if (request.method == "GET"):
        n = forms.TeamVisitPrompt()
    elif (request.method == "POST"):
        n = forms.TeamVisitPrompt(request.POST)
        if (n.is_valid()):
            return redirect(teamtransitionpage, n = n.cleaned_data["team_size"])
        else: messages.error(request, "Form is not valid!")
    context = {
        "form" : n
    }
    return render(request, "prompt_team.html", context)

@login_required
def teamtransitionpage(request, n):
    context = {
            "logged_in" : True,
            "name" : "{} {}".format(request.user.first_name, request.user.last_name),
            "sites": SITES,
            "n" : n
            }
    
    return render(request, "transitionpage_team.html", context)    

@login_required
def teamnewvisit(request, n, site):
    visit = None
    if (site == "ridgefield"):
        visit = forms.RidgefieldVisitForm(request.POST if (request.method == "POST") else None)
    elif (site == "gingin"):
        visit = forms.GinginVisitForm(request.POST if (request.method == "POST") else None)
    elif (visit == None):
        messages.error(request, "Could not generate form (did you specify an invalid site?)")
        return redirect(account)

     # create as many instances of forms as specified
    TeamFormSet = formset_factory(forms.TeamVisitorForm, extra = n)

    team = TeamFormSet(request.POST if (request.method == "POST") else None)

    if (request.method == "POST"):
        if (not visit.is_valid()): 
            messages.error(request, "Visit form is not valid!")
        if (not team.is_valid()):
            messages.error(request, "Team personal details form is not valid!")
        if (visit.is_valid() and team.is_valid()):
            
            formOK = True
            for i in team:
                if (len(i.cleaned_data) == 0):
                    messages.error(request, "All members haven't been specified!")
                    formOK = False
                    break
                if (i.cleaned_data.get("team_username") == request.user.username):
                    messages.error(request, "You cannot specify yourself as a new team member!")
                    formOK = False
                    break
            if (formOK):
                goOK = True
                try: _teamnewvisit_internal(request, site, visit, team)
                except ValueError as ve:
                    messages.error(request, "Could not register users: {}".format(str(ve)))
                    goOK = False
                except Exception as e:
                    messages.error(request,"Developer bug: {}".format(str(e)))
                    goOK = False
                if (goOK):
                    messages.success(request, f"Successfully notified the site manager about {n} new visits!")
                    return redirect(account)

    context = {
        "logged_in" : True,
        "visit_form" : visit,
        "team_form" : team
    }
    return render(request, "registervisit_team.html", context)

def _teamnewvisit_internal(request, site:str, visit:forms, team:list):
    v = visit.cleaned_data
    visitors = []
    
    for i in team:
        # register the visitors
        # visitor personal details
        t = i.cleaned_data
        # clean function should have verified the users

        user = None
        if (t["team_username"]):
            user = User.objects.get(username = t["team_username"])
            if (not models.Visitor.objects.filter(user = user).first()):
                # The only time when this is raised is when a site manager is specified as the username
                # For security reasons, this is not reported to the user.
                raise ValueError("Could not find a visitor with the name {}!".format(t["team_username"]))
        # user will be not none if there is a user in the database
        # create a new visitor if user is none (since users will already have user profiles)
        if (user == None):
            visitorFormDict = {
                "first_name": t["team_first_name"],
                "last_name": t["team_last_name"],
                "email" : t["team_email"],
                "phone": t["team_phone"],
                "role" : t["team_role"],

                # no passwords

                "emergencyname" : t["team_emergencyname"],
                "emergencyphone" : t["team_emergencyphone"],
                "relationship" : t["team_relationship"]
            }
            visitors.append(registerNewVisitor(visitorFormDict, userprofile = False))
        else:
            member = models.Visitor.objects.get(user = user)
            visitors.append(member)

        # finally, add the team leader
        visitors.append(models.Visitor.objects.get(user = request.user))
        
        # then register the visits
        registerNewVisit(site, v, visitors)