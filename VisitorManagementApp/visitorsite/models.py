from django.db import models
from django.contrib.auth.models import User # bind to Django user for ease of maintenace
from django.contrib import admin

# Note: verbose_name will be the label of the form if modelForm is used
# ids are created by Django

class Role(models.Model):
    name = models.TextField()
    def __str__(self): return self.name

class EmergencyContact(models.Model):
    name = models.TextField()
    phone = models.TextField()
    relationship = models.TextField()
    def __str__(self): return self.name

class Visitor(models.Model):
    # user has the following fields:
    # username, password, e-mail, first name, surname
    user = models.OneToOneField(User, on_delete=models.CASCADE, null = True)
    # adapted from Django models.py (lines 356-358)
    first_name = models.CharField(("first name"), max_length=150, blank=True)
    last_name = models.CharField(("last name"), max_length=150, blank=True)
    email = models.EmailField(("email address"), blank=True)

    phone_number = models.TextField()
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    emergencycontact = models.OneToOneField(EmergencyContact, on_delete=models.CASCADE, null=True)
    def __str__(self): return self.user.username if (self.user != None) else "<Unregistered>"

    def visitor(self):
        return self
    visitor.short_description = "Visitor username"

    def firstname(self):
        return self.first_name
    firstname.short_description = "First Name"

    def lastname(self):
        return self.last_name
    lastname.short_description = "Last Name"

    def e_mail(self):
        return self.email
    e_mail.short_description = "E-mail Address"

    def phonenumber(self):
        return self.phone_number
    phonenumber.short_description = "Phone Number"

    def visitorrole(self):
        return self.role
    visitorrole.short_description = "Role"

    def emname(self):
        return self.emergencycontact.name
    emname.short_description = "Emergency Contact Name"

    def emphone(self):
        return self.emergencycontact.phone
    emphone.short_description = "Emergency Contact Phone Number"

    def emrelation(self):
        return self.emergencycontact.relationship
    emrelation.short_description = "Emergency Contact Relationship to Visitor"

class Visit(models.Model):
    """
        Visit is an abstract base class (see https://docs.djangoproject.com/en/4.1/topics/db/models/#abstract-base-classes)
        which sites that a visitor can register to can inherit from. The visit model contains all the
        fields that specific sites have. As Visit is an abstract class, there will not be a database table
        that corresponds to this model.
    """
    # may need to specify custom form entries for both
    # Django treats DateField, TimeField and DateTimeField as
    # TextField 
    # https://stackoverflow.com/questions/61077802/how-to-use-a-datepicker-in-a-modelform-in-django
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    arrival = models.DateTimeField()
    departure = models.DateTimeField()
    
    induction = models.BooleanField()
    houserules = models.BooleanField()
    overnight = models.BooleanField()
    
    # the first two fields are just stubs for now
    def name(self):
        firstname = self.visitor.first_name
        lastname = self.visitor.last_name
        kwargs = {
            "first_name": firstname,
            "last_name" : lastname,
        }
        return "{first_name} {last_name}".format(**kwargs)    

    def emname(self):
        return self.visitor.emergencycontact.name

    emname.short_description = "Emergency Contact Name"
    def emphone(self):
        return self.visitor.emergencycontact.phone
    emphone.short_description = "Emergency Contact Phone Number"

    def emrelation(self):
        return self.visitor.emergencycontact.relationship
    emrelation.short_description = "Emergency Contact Relationship to Visitor"

class RidgefieldVisit(Visit):
    paddock = models.TextField()

class GinginVisit(Visit): pass # adds no fields

class SiteEmergencyContact(models.Model):
    name = models.TextField()
    phone = models.TextField()
    site = models.TextField()
    position = models.TextField()
    def __str__(self): return self.name