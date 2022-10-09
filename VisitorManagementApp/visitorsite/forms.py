from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from .models import Role
from django.utils.html import mark_safe
# opted not to use modelForm because:
# 1) arrival and departure fields are TextFields, not Date/TimePicker
#    fields
# 2) the client wants form fields to change over time

# VISITOR FORMS
# =======================================================================
class VisitorProfileForm(forms.Form):
    # Name may have accents: Ári Nordström
    # These are for the Django out-of-the-box User object
    username = forms.CharField(label="Username")
    first_name = forms.CharField(label="First name")
    last_name = forms.CharField(label="Last name")
    email = forms.EmailField(label="E-mail address")

    # These are for the extension to the User object
    # can be separated by dashes or by whitespace (\s)
    # US: +1-407-123-4567
    phone = forms.CharField(label="Phone Number", validators=[RegexValidator(r"[0-9\-\+\s]")])
    role = forms.ModelChoiceField(queryset = Role.objects.all(), label="Role")
    # Below are details for a visitor's emergency contacts
    emergencyname = forms.CharField(label="Emergency Contact Name", validators=[RegexValidator(r"[^0-9]")])
    emergencyphone = forms.CharField(label="Emergency Contact Phone Number", validators=[RegexValidator(r"[0-9\-\+\s]")])
    relationship = forms.CharField(label="Emergency Contact Relationship (Friend, Family member, etc)")
    
    password = forms.CharField(label="Enter password", widget=forms.PasswordInput())
    password_chk = forms.CharField(label="Enter password again", widget=forms.PasswordInput(), validators=[])
    def clean_password_chk(self):
        if (self.cleaned_data.get("password") != self.cleaned_data.get("password_chk")):
            self.add_error("password_chk", ValidationError("Passwords do not match!"))
        password_validation.validate_password(self.cleaned_data.get("password"))
        return self.cleaned_data["password_chk"]

class VisitorLoginForm(forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Enter password", widget=forms.PasswordInput())


class VisitorProfileFieldsChangeForm(forms.Form):
    first_name = forms.CharField(label="First name", required=False)
    last_name = forms.CharField(label="Last name", required=False)
    email = forms.EmailField(label="E-mail address", required=False)

    phone = forms.CharField(label="Phone Number", validators=[RegexValidator(r"[0-9\-\+\s]")], required=False)
    role = forms.ModelChoiceField(queryset = Role.objects.all(), label="Role", required=False)

class VisitorEmergencyContactForm(forms.Form):
    # Front-end does not show emergency contact details (new form after initial user registration)
    # we can retrieve the user id from here
    name = forms.CharField(label="Name", validators=[RegexValidator(r"[^0-9]")])
    phone = forms.CharField(label="Phone Number", validators=[RegexValidator(r"[0-9\-\+\s]")])
    relationship = forms.CharField(label="Relationship (Friend, Family member, etc)")
# =======================================================================

# VISIT FORM
# Parent class: VisitForm
# Inheriting from VisitForm:
# - RidgefieldForm (paddock field)
# - GinginVisitForm (no other fields, but this helps for easy addition of new form questions in the future)
# =======================================================================
class VisitForm(forms.Form):
    # Mozilla Firefox does not support date and time
    # We will have to combine both fields before entering into the database
    arrivaldate= forms.DateField(label="Arrival date", widget=forms.DateInput(attrs={"type":"date"}))
    arrivaltime= forms.TimeField(label="Arrival time", widget=forms.TimeInput(attrs={"type":"time"}))
    departuredate= forms.DateField(label="Departure date", widget=forms.DateInput(attrs={"type":"date"}))
    departuretime= forms.TimeField(label="Departure date", widget=forms.TimeInput(attrs={"type":"time"}))
    
    overnight = forms.BooleanField(label = "I am staying overnight", required=False)
    induction = forms.BooleanField(label = "I have read the induction", required=False)
    houserules = forms.BooleanField(label = "I have read the house rules", required=False)

    def clean(self):
        arrivaldate = self.cleaned_data.get("arrivaldate")
        departuredate = self.cleaned_data.get("departuredate")

        # arrival date cannot be after the departure date
        if (arrivaldate > departuredate):
            self.add_error("departuredate", ValidationError("The departure date must not be before the arrival date!"))
        # if on the same day the arrival time cannot be after the departure time
        elif (arrivaldate == departuredate):
            arrivaltime = self.cleaned_data.get("arrivaltime")
            departuretime = self.cleaned_data.get("departuretime")
            if (arrivaltime > departuretime): # visitor should arrive before departing
                self.add_error("departuretime", ValidationError("The departure time must not be before the arrival time!"))

        # if staying for more than one day the visitor should check the overnight checkbox
        if (arrivaldate < departuredate): # overnight must be checked
            if (not self.cleaned_data.get("overnight")):
                self.add_error("overnight", "This must be checked if you want to visit this location for more than one consecutive day!")
        if (self.cleaned_data.get("overnight")):
            # overnight specified
            if (not self.cleaned_data.get("houserules")):
                self.add_error("houserules", ValidationError("You must agree to the houserules."))
            if (not self.cleaned_data.get("induction")):
                self.add_error("induction", ValidationError("You must have read the site induction."))
        else:
            # overnight not specified
            if (self.cleaned_data.get("houserules")):
                self.add_error("houserules", ValidationError("You cannot check this field if you are not staying overnight."))
            if (self.cleaned_data.get("induction")):
                self.add_error("induction", ValidationError("You cannot check this field if you are not staying overnight."))

class RidgefieldVisitForm(VisitForm):
    paddock = forms.CharField(label="Enter paddock (Ridgefield Farm only)", required=False) # only for Ridgefield farm
    induction = forms.BooleanField(label=mark_safe('I have read the<a href="/static/pdf/UWA RidgeFieldFarm _Visitor and User Induction_2022_as at 10 May 2022.pdf" target="_blank">induction</a >'),required=False)
    houserules = forms.BooleanField(label=mark_safe('I have read the<a href="/static/pdf/Terms and Conditions - Accommodation at the Old Farmhouse.pdf" target="_blank">houserules</a >'),required=False)
    def clean(self):
        super().clean()
        if (self.cleaned_data.get("overnight")):
            if (not self.cleaned_data.get("paddock")):
                self.add_error("paddock", ValidationError("You must specify a paddock."))
        else:
            if (self.cleaned_data.get("paddock")):
                self.add_error("paddock", ValidationError("You cannot specify a paddock if you are not staying overnight."))

class GinginVisitForm(VisitForm):
    paddock = forms.CharField(label="Enter paddock (Ridgefield Farm only)", required=False)  # only for Ridgefield farm
    induction = forms.BooleanField(label=mark_safe('I have read the<a href="/static/pdf/Induction sheet-5.pdf" target="_blank">induction</a >'),required=False)
    houserules = forms.BooleanField(label=mark_safe('I have read the<a href="/static/pdf/GGP Gate locking procedure.pdf" target="_blank">houserules</a >'),required=False)
    def clean(self):
        super().clean()
        if (self.cleaned_data.get("overnight")):
            if (not self.cleaned_data.get("paddock")):
                self.add_error("paddock", ValidationError("You must specify a paddock."))
        else:
            if (self.cleaned_data.get("paddock")):
                self.add_error("paddock", ValidationError("You cannot specify a paddock if you are not staying overnight."))


class TeamVisitPrompt(forms.Form):
    # This is used to specify the number of visitors
    team_size = forms.IntegerField(label='Enter the number of members visiting with you (1 or more)', validators=[MinValueValidator(1)])

class TeamVisitorForm(forms.Form):
    # This is used for team registration

    # Though all fields are specified as optional, they are actually conditionally mandatory
    # If a valid username is specified, no other fields can be specified
    # If otherwise, all other fields must be specified
    team_username = forms.CharField(label="If the team member has an account, put in their username here and leave all other fields blank", required = False)
    team_first_name = forms.CharField(label="First name", required = False)
    team_last_name = forms.CharField(label="Last name", required = False)
    team_email = forms.EmailField(label="E-mail address", required = False)
    team_phone = forms.CharField(label="Phone Number", validators=[RegexValidator(r"[0-9\-\+\s]")], required = False)
    team_role = forms.ModelChoiceField(queryset = Role.objects.all(), label="Role", required = False)

    team_emergencyname = forms.CharField(label="Emergency Contact Name", validators=[RegexValidator(r"[^0-9]")], required = False)
    team_emergencyphone = forms.CharField(label="Emergency Contact Phone Number", validators=[RegexValidator(r"[0-9\-\+\s]")], required = False)
    team_relationship = forms.CharField(label="Emergency Contact Relationship (Friend, Family member, etc)", required = False)

    def clean(self):
        cd = self.cleaned_data
        # if the username is specified, check if this exists in the database
        if (cd.get("team_username") != ""):
            if (User.objects.filter(username = cd.get("team_username")).first() == None):
                self.add_error("team_username", ValidationError("This user does not exist in the database!"))
            else: # check if all other values are blank
                for (field, value) in cd.items():
                    if (field != "team_username" and value):
                        self.add_error(field, ValidationError("This field must be blank when a username is specified!"))
                        break # if we continue there will be a error in dictionary changes during iteration
        else: # username is not specified
            for (field, value) in cd.items():
                if (field != "team_username" and not value):
                    self.add_error(field, ValidationError("This field must be specified when a username is not specified!"))
                    break # if we continue there will be a error in dictionary changes during iteration

            
        

