from django.apps import AppConfig
from visitorsite.globals import SITES


class VisitorsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'visitorsite'

    def addpermissions(self, site_group, otherpermissions):
        from django.contrib.auth.models import Permission
        # all site managers can add or delete emergency contacts
        siteemergencycontact_permission_codenames = [
            'add_siteemergencycontact', 
            'change_siteemergencycontact', 
            'delete_siteemergencycontact', 
            'view_siteemergencycontact'
        ]
        allpermissions = siteemergencycontact_permission_codenames + otherpermissions
        for i in allpermissions:
            site_permission = Permission.objects.get(codename = i)
            site_group.permissions.add(site_permission)
            site_group.save()


    def sitemanagerchecks(self):
        """
        Site managers should only be able to view who is visiting a specific
        site and to edit site emergency contacts.

        In Django, permission codenames for visiting sites are prefixed with
        'view_'. In this implementation, a codename for a site is as follows:
                'view_[sitename]visit'
        E.g., for Gingin Gravity Precinct, the codename is 'view_ginginvisit'

        The sitename can be referenced from the SITES constant in globals.py
        """
        from django.contrib.auth.models import Group
        
        for (site) in SITES.keys():
            site_group = Group.objects.filter(name = site.capitalize()).first()
            if (site_group == None):
                new_site_group = Group.objects.create(name = site.capitalize())
                view_site_permission_codename = "view_{sitename}visit".format(sitename = site)
                self.addpermissions(new_site_group, [view_site_permission_codename])

    def ready(self):
        print("Performing site manager checks...")
        self.sitemanagerchecks()
