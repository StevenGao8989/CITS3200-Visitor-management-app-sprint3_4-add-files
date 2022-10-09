from hashlib import pbkdf2_hmac
from django.test import TestCase
from visitorsite import models, forms

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

import random
import string

# 64 visitors: around 10 seconds
# 128 visitors: around 20 seconds
# 256 visitors: around 40 seconds
# 512 visitors: around 80 seconds
RANDVISITORGEN = 64

# Functions used by all test cases
# =======================================================================

def generate_randomstring(chars:str, n:int):
    return "".join(random.choices(chars, k = n))
    
def setUpRoles(roles:list):
    for i in roles:
        role = models.Role.objects.create(name=i)
        role.save()

def setUpEmergencyContacts(emergencycontacts:dict):
    for contact in emergencycontacts:
        newContact = models.EmergencyContact.objects.create(
        name=contact["name"],
        phone=contact["phone"],
        relationship=contact["relationship"]
        )
        newContact.save()

def setUpVisitors(visitors:list):
    for visitor in visitors:
        # create user object first
        user = User.objects.create_user(
            username = visitor["username"],
            email=visitor["email"],
            password=visitor["password"] # password is hashed upon constructing the object
        )
        user.first_name = visitor["first_name"],
        user.last_name = visitor["last_name"],

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
            email = visitor["email"],
            phone_number = visitor["phone"],
            role=models.Role.objects.filter(name=visitor["role"]).first(),
            emergencycontact = newEmergencyContact
            )
        newVisitor.save()

def rolesPresent(test:TestCase, roles:list):
    test.assertEqual(len(roles), len(models.Role.objects.all()))
    for role in roles:
        test.assertEqual(len(models.Role.objects.filter(name = role)), 1)

def sitesPresent(test:TestCase, sites:list):
    test.assertEqual(len(sites), len(models.Site.objects.all()))
    for site in sites:
        test.assertEqual(len(models.Site.objects.filter(name = site)), 1)

def visitorsPresent(test:TestCase, visitors:list):
    test.assertEqual(len(visitors), len(models.Visitor.objects.all()))

    for visitor in visitors:
        # test if all entries in User in are correct
        existingUser = User.objects.get(username = visitor["username"])
        # Django converts the domain part of the email to lower case (base_user.py line 20, normalize_email)
        x = visitor["email"]
        # the first part should include @ because we cannot lower this (for safety)
        normalisedemail = x[:x.rfind('@') + 1] + x[x.rfind('@') + 1:].lower()
        test.assertEqual(existingUser.email, normalisedemail)
        test.assertTrue(check_password(visitor["password"], existingUser.password))

        # test if all entries in Visitor in are correct

        # there should only be one entry of the visitor
        # get the username from the default User model since this has a one-one relationship with
        # the visitor object
        # i.e. we extended the User object with the Visitor object
        test.assertEqual(len(models.Visitor.objects.filter(user = existingUser)), 1)
        existingVisitor = models.Visitor.objects.get(user = existingUser)

        test.assertNotEqual(existingVisitor, None) # whether the visitor exists in the first place
        
        test.assertEqual(existingVisitor.phone_number, visitor["phone"])
        test.assertEqual(existingVisitor.role, models.Role.objects.get(name = visitor["role"]))

def emergencycontactsPresent(test:TestCase, emergencycontacts:list):
    test.assertEqual(len(emergencycontacts), len(models.EmergencyContact.objects.all()))

    for ec in emergencycontacts:
        # there should be only one entry of the emergency contact
        test.assertEqual(len(models.EmergencyContact.objects.filter(name = ec["name"])), 1)
        existingEc = models.EmergencyContact.objects.get(name = ec["name"])
        test.assertEqual(existingEc.phone, ec["phone"])
        test.assertEqual(existingEc.relationship, ec["relationship"])
# =======================================================================

# Variables used by basic test cases (JSON format)
# =======================================================================
BASICVISITORS = [
    {
    "username":"johnd",
    "first_name":"John", 
    "last_name":"Doe",
    "password":"badpassword", 
    "email":"john.doe@jd.com", 
    "phone": "1234 5678", 
    "role" : "Contractor",

    "emergencyname": "somebody", 
    "emergencyphone": "12345", 
    "relationship":"Guardian"
    },

    {
    "username":"johna",
    "first_name":"John", 
    "last_name":"Appleseed",
    "password":"badpassword2", 
    "email":"ja@aj.net", 
    "phone": "0400 999 888", 
    "role":"UWA Student",
    "emergencyname": "somebody2", 
    "emergencyphone": "111", 
    "relationship":"Guardian"
    },

    {
    "username":"ari",
    "first_name":"Ári", 
    "last_name":"Nordström",
    "password":"g&3\C}CKkM1aj8g!92,Q/j3'(NJyvB1", 
    "email":"12345678@ari.biz", 
    "phone": "+1-407-123-4567", 
    "role":"UWA Staff",
    "emergencyname": "某人", 
    "emergencyphone": "222", 
    "relationship":"母亲"
    },
]

# just in case the we change the above fields (add accents, etc)
JOHND = BASICVISITORS[0]["username"]
JOHNA = BASICVISITORS[1]["username"]
ARI = BASICVISITORS[2]["username"]

BASICROLES = ["UWA Staff", "UWA Student", "Contractor", "Other"]

BASICSITES = ["UWA Gingin Gravity Precinct", "UWA Farm Ridgefield"]
# visitors to enter some forms for visits which are different from the database
# representation
BASICVISITS = [
    {
        "_visitor" : "Ári Nordström", # in integration testing, use the Visitor object
        "arrivaldate" : "2022-12-23", # <input type="date" />
        "arrivaltime" : "22:00", # <input type="time" />
        "departuredate":"2022-12-23",
        "departuretime" : "22:30",

        "overnight" : False,
        "induction" : False,
        "houserules" : False,

        "paddock" : None
    }, 

    {
        "_visitor" : "Ári Nordström", # in integration testing, use the Visitor object
        "arrivaldate" : "2022-12-27", # <input type="date" />
        "arrivaltime" : "06:00", # <input type="time" />
        "departuredate" : "2022-12-28",
        "departuretime":"06:00",

        "overnight" : True,
        "induction" : True,
        "houserules" : True,

        "paddock" : "Mating Pots 0.71"
    }, 

    {
        "_visitor" : "John Appleseed", # in integration testing, use the Visitor object
        "arrivaldate" : "2022-12-31", # <input type="date" />
        "arrivaltime" : "07:00", # <input type="time" />
        "departuredate":"2022-12-31",
        "departuretime" : "08:30",

        "overnight" : False,
        "induction" : False,
        "houserules" : False, 

        "paddock" : None
    }, 

    # John Doe does not visit any sites (special test case)
]

# =======================================================================

# VISITOR MODEL TEST CASES
# =======================================================================
class VisitorTestBasic(TestCase):
    
    def setUp(self):
        print("Running basic visitor test case")
        setUpRoles(BASICROLES)
        setUpVisitors(BASICVISITORS)

    def test_basic(self):
        # from the basic test
        rolesPresent(self, BASICROLES)
        visitorsPresent(self, BASICVISITORS)

class VisitorTestRandomVisitors(TestCase):

    Roles16 = [generate_randomstring(string.ascii_letters, random.randint(5,100)) for i in range(16)]

    VisitorsMany = [] # populate later

    def generateVisitors(self, number):
        return [
            {"username":generate_randomstring(string.ascii_letters, random.randint(5, 100)),
            "first_name":generate_randomstring(string.ascii_letters, random.randint(5, 50)),
            "last_name":generate_randomstring(string.ascii_letters, random.randint(5, 50)),
            "password":generate_randomstring(string.digits, random.randint(8, 64)), 
            "email": # [random string]@[random string].com
                    generate_randomstring(string.ascii_letters + string.digits, random.randint(5, 20)) + 
                    "@" + 
                    generate_randomstring(string.ascii_letters, 5) +
                    ".com", 
            "phone": generate_randomstring(string.digits, random.randint(5, 20)), 
            "role" : self.Roles16[random.randint(0, 15)], # pick a random role
            "emergencyname" : generate_randomstring(string.ascii_letters, random.randint(5, 100)), 
            "emergencyphone": generate_randomstring(string.digits, random.randint(5, 20)),
            "relationship" : generate_randomstring(string.ascii_letters, random.randint(5, 20))
            }
            for i in range(number)
        ]
    def setUp(self):     
        n = RANDVISITORGEN
        print(f"Running visitor test case involving {n} randomly generated visitors...")
        self.VisitorsMany = self.generateVisitors(n)
        setUpRoles(self.Roles16)
        setUpVisitors(self.VisitorsMany)
        
    def remove_all_visitors(self):
        for i in self.VisitorsMany:
            toRemove = models.Visitor.objects.get(user = User.objects.get(username = i["username"]))
            toRemove.delete()
            self.assertRaises(models.Visitor.DoesNotExist, models.Visitor.objects.get, user = User.objects.get(username = i["username"]))
    
    def test_basic(self):
        # from the basic test
        rolesPresent(self, self.Roles16)
        visitorsPresent(self, self.VisitorsMany)
        self.remove_all_visitors()
        self.assertEqual(len(models.Visitor.objects.all()), 0)

# =======================================================================

def setUpVisitorProfileForms(visitors:list):
    visitorProfileForms = []
    for visitor in visitors:
        data = {
            "username": visitor["username"],
            "password": visitor["password"],
            "first_name": visitor["first_name"],
            "last_name": visitor["last_name"],
            "email": visitor["email"],
            "phone": visitor["phone"],
            "role": models.Role.objects.get(name = visitor["role"]),
            "password" : visitor["password"],
            "password_chk" : visitor["password"],

            "emergencyname": visitor["emergencyname"],
            "emergencyphone": visitor["emergencyphone"],
            "relationship" : visitor["relationship"]
        }
        newVisit = forms.VisitorProfileForm(data = data)
        visitorProfileForms.append(newVisit)
    return visitorProfileForms

def testVisitorProfileForms(test:TestCase, visitorProfileForms:list):
    for i in visitorProfileForms:
        test.assertTrue(i.is_valid())

# USER FORM TEST CASES
class VisitorFormTestCaseBasic(TestCase):
    visitorForms = None
    def setUp(self):
        setUpRoles(BASICROLES)
        self.visitorForms = setUpVisitorProfileForms(BASICVISITORS)
    def test_visitor_form(self):
        testVisitorProfileForms(self, self.visitorForms)

# VISIT FORM TEST CASES 
# =======================================================================

def setUpVisitForms(visits:list):

    visitForms = []
    for visit in visits:

        data = {
            "arrivaldate": visit["arrivaldate"],
            "arrivaltime": visit["arrivaltime"],
            "departuredate": visit["departuredate"],
            "departuretime": visit["departuretime"],

            "overnight" : visit["overnight"],
            "induction" : visit["induction"],
            "houserules" : visit["houserules"],

            "paddock" : visit["paddock"]
        }

        newVisit = forms.RidgefieldVisitForm(data = data)
        visitForms.append(newVisit)
    return visitForms

def testVisitForms(test:TestCase, visitForms:list):
    for i in visitForms:
        test.assertTrue(i.is_valid())
        

class VisitFormTestCaseBasic(TestCase):
    
    visitForms = None
    def setUp(self):
        self.visitForms = setUpVisitForms(BASICVISITS)
        print("Running basic visit test case")

    def test_visit_form(self):
        testVisitForms(self, self.visitForms)