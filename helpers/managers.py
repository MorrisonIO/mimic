class Managers:
    def __init__(self, group):
        self.group = group

    def __iter__(self):
        from django.contrib.auth.models import User, Group
        from django.core.exceptions import ObjectDoesNotExist

        try:
            group = Group.objects.get(name=self.group)
        except ObjectDoesNotExist:
            return iter([])

        users = User.objects.filter(groups=group, is_active=True)

        return iter([(u.get_full_name(), u.email) for u in users if u.email])

    def __str__(self):
        return '\n'.join([' '.join(x) for x in self])

    def __unicode__(self):
        return unicode(str(self))
