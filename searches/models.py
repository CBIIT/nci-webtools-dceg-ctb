from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q

# Create your models here.


class Search(models.Model):
    id = models.AutoField(primary_key=True, null=False, blank=False)
    name = models.CharField(max_length=128, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)

    # Returns the highest level of permission the user has.
    def get_perm(self, request):
        perm = self.search_perms_set.filter(user_id=request.user.id).order_by('perm')

        if perm.count() > 0:
            return perm[0]
        else:
            return None

    def get_owner(self):
        return self.search_perms_set.filter(perm=Search_Perms.OWNER)[0].user


class Search_Perms(models.Model):
    READER = 'READER'
    OWNER = 'OWNER'
    PERMISSIONS = (
        (READER, 'Reader'),
        (OWNER, 'Owner')
    )
    search = models.ForeignKey(Search, null=False, blank=False, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=False, blank=True, on_delete=models.CASCADE)
    perm = models.CharField(max_length=10, choices=PERMISSIONS, default=READER)


class AttributeQuerySet(models.QuerySet):

    def get_attr_ranges(self, as_dict=False):
        if as_dict:
            ranges = {}
            for range in Attribute_Ranges.objects.filter(attribute__in=self.all()):
                if range.attribute_id not in ranges:
                    ranges[range.attribute_id] = []
                ranges[range.attribute_id].append(range)
            return ranges
        return Attribute_Ranges.objects.select_related('attribute').filter(attribute__in=self.all())


class AttributeManager(models.Manager):
    def get_queryset(self):
        return AttributeQuerySet(self.model, using=self._db)


class Attribute(models.Model):
    CONTINUOUS_NUMERIC = 'N'
    CATEGORICAL_NUMERIC = 'M'
    CATEGORICAL = 'C'
    TEXT = 'T'
    STRING = 'S'
    DATE = 'D'
    DATA_TYPES = (
        (CONTINUOUS_NUMERIC, 'Continuous Numeric'),
        (CATEGORICAL, 'Categorical String'),
        (CATEGORICAL_NUMERIC, 'Categorical Number'),
        (TEXT, 'Text'),
        (STRING, 'String'),
        (DATE, 'Date')
    )
    id = models.AutoField(primary_key=True, null=False, blank=False)
    objects = AttributeManager()
    name = models.CharField(max_length=64, null=False, blank=False)
    display_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    data_type = models.CharField(max_length=1, blank=False, null=False, choices=DATA_TYPES, default=CATEGORICAL)
    active = models.BooleanField(default=True)
    preformatted_values = models.BooleanField(default=False)
    units = models.CharField(max_length=256, blank=True, null=True)
    default_ui_display = models.BooleanField(default=True, null=False, blank=False)

    def get_display_values(self):
        display_vals = self.attribute_display_values_set.all()
        result = {}

        for val in display_vals:
            result[val.raw_value] = val.display_value

        return result

    @classmethod
    def get_ranged_attrs(cls):
        return list(cls.objects.filter(data_type=cls.CONTINUOUS_NUMERIC, active=True).values_list('name', flat=True))

    def __str__(self):
        return "{} ({}), Type: {}".format(
            self.name, self.display_name, self.data_type)


class FilterQuerySet(models.QuerySet):
    def get_filter_set(self):
        filters = {}
        for fltr in self.select_related('attribute').all():
            filter_name = ("{}{}".format(fltr.name.lower(),fltr.numeric_op)) if fltr.numeric_op else fltr.attribute.name
            filters[filter_name] = fltr.value.split(fltr.value_delimiter)
        return filters

    def get_filter_set_array(self):
        filters = []
        for fltr in self.select_related('attribute').all():
            filters.append({
                'id': fltr.attribute.id,
                'name': ("{}{}".format(fltr.name.lower(),fltr.numeric_op)) if fltr.numeric_op else fltr.attribute.name,
                'display_name': fltr.attribute.display_name,
                'values': fltr.value.split(fltr.value_delimiter)
            })
        return filters


class FilterManager(models.Manager):
    def get_queryset(self):
        return FilterQuerySet(self.model, using=self._db)


class Filter(models.Model):
    BTW = 'B'
    GTE = 'GE'
    LTE = 'LE'
    GT = 'G'
    LT = 'L'
    NUMERIC_OPS = (
        (BTW, '_btw'),
        (GTE, '_gte'),
        (LTE, '_lte'),
        (GT, '_gt'),
        (LT, '_lt')
    )
    DEFAULT_VALUE_DELIMITER = ','
    ALTERNATIVE_VALUE_DELIMITERS = [';','|','^']
    objects = FilterManager()
    resulting_search = models.ForeignKey(Search, null=False, blank=False, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, null=False, blank=False, on_delete=models.CASCADE)
    value = models.TextField(null=False, blank=False)
    numeric_op = models.CharField(max_length=4, null=True, blank=True, choices=NUMERIC_OPS)
    value_delimiter = models.CharField(max_length=4, null=False, blank=False, default=DEFAULT_VALUE_DELIMITER)

    def get_numeric_filter(self):
        if self.numeric_op:
            return "{}{}".format(self.attribute.name.lower(),self.numeric_op)
        return None

    def get_filter(self):
        return {
            "()".format(self.attribute.name if not self.numeric_op else self.get_numeric_filter()): self.value.split(self.value_delimiter)
        }

    def __repr__(self):
        return "{ %s }" % ("\"{}\": [{}]".format(self.attribute.name if not self.numeric_op else self.get_numeric_filter(), self.value))

    def __str__(self):
        return self.__repr__()


class Attribute_Display_ValuesQuerySet(models.QuerySet):
    def to_dict(self):
        dvals = {}
        dvattrs = self.all()
        for dv in dvattrs:
            if dv.attribute_id not in dvals:
                dvals[dv.attribute_id] = {}
            dvals[dv.attribute_id][dv.raw_value] = dv.display_value

        return dvals


class Attribute_Display_ValuesManager(models.Manager):
    def get_queryset(self):
        return Attribute_Display_ValuesQuerySet(self.model, using=self._db)


class Attribute_Display_Values(models.Model):
    id = models.AutoField(primary_key=True, null=False, blank=False)
    attribute = models.ForeignKey(Attribute, null=False, blank=False, on_delete=models.CASCADE)
    raw_value = models.CharField(max_length=256, null=False, blank=False)
    display_value = models.CharField(max_length=256, null=False, blank=False)
    objects = Attribute_Display_ValuesManager()

    class Meta(object):
        unique_together = (("raw_value", "attribute"),)

    def __str__(self):
        return "{} - {}".format(self.raw_value, self.display_value)

