from django.urls import path

from visitorsite import views, teamviews

urlpatterns = [
    # welcome page
    path("", views.index),

    # accessible without login
    path("register", views.register),
    path("login", views.login),
    
    # accesible with login
    path("logout", views.logout),
    path("account", views.account),
    path("deleteaccount", views.deleteaccount),
    path("changeemergency", views.changeemergency),
    path("changedetails", views.changedetails),
    path("password", views.password),
    path("newvisit/<str:site>", views.newvisit),
    path("sitecontacts", views.site_emergency_contacts),
    path("transitionpage", views.transitionpage),
    path("bulkregister", teamviews.teamregister),
    path("teamtransitionpage/<int:n>", teamviews.teamtransitionpage),
    path("teamtransitionpage/<int:n>/<str:site>", teamviews.teamnewvisit, name = "teamnewvisit")
    
]