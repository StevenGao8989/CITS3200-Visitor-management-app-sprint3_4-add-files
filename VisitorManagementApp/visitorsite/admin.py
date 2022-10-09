from django.contrib import admin
from django.apps import apps
from .models import *
import datetime
from django.utils import timezone
from django.utils.html import format_html

admin.site.register(Role)
admin.site.register(EmergencyContact)
#admin.site.register(Visitor)


class SiteEmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'site', 'position')

class VisitFilter(admin.SimpleListFilter):
    title = 'Visit Filter'
    parameter_name = 'isOnSite'

    def lookups(self, request, model_admin):
        return (
            ('current_visit', 'Current Visit'),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        if self.value() == 'current_visit':
            now = datetime.datetime.now(tz=timezone.utc)
            return queryset.filter(
                arrival__lte=now,
                departure__gte=now,
            )

class VisitorAdmin(admin.ModelAdmin):
    list_display = ('visitor', 'firstname', 'lastname', 'e_mail', 'phonenumber', 'role', 'emname', 'emphone',
                    'emrelation')

class VisitAdmin(admin.ModelAdmin):
    list_display = ('visitor', 'arrival', 'departure', 'induction',
                    'houserules', 'overnight', 'number')
    list_filter = ('arrival', 'departure', VisitFilter)

    def number(self, obj):
        return format_html('<a href="tel:{}"> {} </a>',
                           obj.visitor.phonenumber(),
                           obj.visitor.phonenumber())

    number.short_description = "Phone Number"


class RidgefieldVisitAdmin(admin.ModelAdmin):
    list_display = ('name', 'visitor', 'number', 'emname', 'emnumber', 'emrelation', 'arrival', 'departure', 'induction',
                    'houserules', 'overnight')
    list_filter = ('arrival', 'departure', VisitFilter)

    def emnumber(self, obj):
        return format_html('<a href="tel:{emn}"> {emn} </a>',
                           emn = obj.visitor.emphone())
    def number(self, obj):
        return format_html('<a href="tel:{}"> {} </a>',
                           obj.visitor.phonenumber(),
                           obj.visitor.phonenumber())

    emnumber.short_description = "Emergency Contact Phone Number"
    number.short_description = "Phone Number"

class GinginVisitAdmin(admin.ModelAdmin):
    list_display = ('name', 'visitor', 'number', 'emname', 'emnumber', 'emrelation', 'arrival', 'departure', 'induction',
                    'houserules', 'overnight')
    list_filter = ('arrival', 'departure', VisitFilter)

    def emnumber(self, obj):
        return format_html('<a href="tel:{emn}"> {emn} </a>',
                           emn = obj.visitor.emphone())
    def number(self, obj):
        return format_html('<a href="tel:{}"> {} </a>',
                           obj.visitor.phonenumber(),
                           obj.visitor.phonenumber())

    emnumber.short_description = "Emergency Contact Phone Number"
    number.short_description = "Phone Number"
    

admin.site.register(SiteEmergencyContact, SiteEmergencyContactAdmin)
admin.site.register(Visitor, VisitorAdmin)
admin.site.register(Visit, VisitAdmin)
admin.site.register(GinginVisit, GinginVisitAdmin)
admin.site.register(RidgefieldVisit, RidgefieldVisitAdmin)
