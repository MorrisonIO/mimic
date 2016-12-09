from django.db.models import Manager

class ManagerWithPublic(Manager):
    """
    Returns all public Entries.
    """
    def public(self):
        return self.get_query_set().filter(status__exact='public')
