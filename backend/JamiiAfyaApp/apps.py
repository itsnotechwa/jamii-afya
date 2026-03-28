from django.apps import AppConfig


class JamiiafyaappConfig(AppConfig):
    name = 'JamiiAfyaApp'

#This is the configuration for the audit app, which contains the AuditLog model and middleware for logging user actions.
class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'

#This is the configuration for the contributions app, which contains the Contribution model and related views and serializers for managing user contributions to group pools.
class ContributionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contributions'

#This is the configuration for the emergencies app, which contains models and views for managing emergency requests, approvals, and related documents within the application.
class EmergenciesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emergencies'

#This is the configuration for the groups app, which contains models and views for managing user groups, memberships, and related functionality such as group creation, joining, and member management.
class GroupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.groups'

#This is the configuration for the notifications app, which contains models and views for managing user notifications within the application, including sending alerts for new emergency requests and other relevant events.
class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'

#This is the configuration for the users app, which contains models and views for managing user accounts, authentication, and related functionality within the application.
class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

# This is the configuration for the mpesa app, which contains models and views for integrating with the M-Pesa payment system, allowing users to make contributions and receive payouts through M-Pesa.
class MpesaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mpesa'
