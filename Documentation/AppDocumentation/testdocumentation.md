UWA Research Infrastructure Centres Site Registration Application
================================================================
Test Documentation
------------------

The tests can be run with the following command:
    ./manage.py test visitorsite

These tests are unit tests for the project. They simply test if the forms
and models are working as is, atomically. As these are not integration or
project acceptance tests, there are no cases where the forms interact
with the models. These will be performed by integration tests.

# VisitorTestBasic
This uses pre-defined lists of roles, emergency contacts and visitors
to test if the database holds up and the foreign keys are present.

Expected result: All visitors are entered into the database. All fields are
added without modifications, except for the e-mail address field where the
domain is converted to lower case via Django normalisation. All foreign
keys are correctly added.

# VisitorTestRandomVisitors
This is the same as the basic test case, however it uses a specified number
of randomly generated roles, emergency contacts and visitors. Some visitors
may have the same emergency contacts (duplicates not allowed).

Expected result: All visitors are entered into the database. All fields are
added without modifications, except for the e-mail address field where the
domain is converted to lower case via Django normalisation. All foreign
keys are correctly added.

# VisitFormTestCaseBasic
This tests the visit form (but not the model) to see if all form fields are
working.

Expected result: All forms are valid

# VisitorFormTestCaseBasic
This tests the visitor form (but not the model) to see if all form fields
are working.

Expected result: All forms are valid

