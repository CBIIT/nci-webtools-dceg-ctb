###
# Copyright 2015-2022, Institute for Systems Biology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
# from datetime import datetime, timezone


# from django.db.models import Q


class Donor(models.Model):
    patient_id = models.IntegerField(default=None, null=True, blank=False)
    patient_uid = models.CharField(max_length=20, default=None, null=True, blank=False)
    country_current = models.CharField(max_length=45, default=None, null=True, blank=False)
    oblast_current = models.CharField(max_length=45, default=None, null=True, blank=False)

    # country_at_accident: Patient country
    country_at_accident = models.CharField(max_length=45, default=None, null=True, blank=False)

    # oblast_at_accident: Patient residency
    # Exposed region -
    #   In Russia, Kaluga, Tula, Oryol (Orel) and Bryansk
    #   In Ukraine, Kiev, Kiev city, Rovno, Cherkasse, Zhitomyr, Chernigov and Sumy.
    # Although technically not an oblast, Pripyat, the village closest to the reactor site is also included as a
    # location that is classified as exposed. Oblasts outside of those listed above are all classified as being
    # unexposed regions.
    oblast_at_accident = models.CharField(max_length=45, default=None, null=True, blank=False)

    gender = models.CharField(max_length=10, default=None, null=True, blank=False)

    # age: 01/01/87 should be used as the cut-off date for exposure to radioiodine either in utero or as a living
    #   individual should be used as the definition of a person who was unexposed to radioiodine from the accident.
    age = models.DecimalField(max_digits=10, decimal_places=2, default=None, null=True, blank=False)

    # age_at_first_operation: age at operation
    age_at_first_operation = models.DecimalField(max_digits=10, decimal_places=2, default=None, null=True, blank=False)

    # age_at_exposure: Age at accident
    age_at_exposure = models.DecimalField(max_digits=10, decimal_places=2, default=None, null=True, blank=False)

    # The date of birth search field is therefore fed from the age_category field
    #   1: exposed by virtue of both date of birth (born on or before 4/26/86) and residency  in one of the contaminated
    #       oblasts at the time of the accident
    #   2: unexposed by virtue of date of birth (after 01/1/87) if resident in one of the contaminated oblasts,
    #       or any date of birth and resident outside the exposed oblasts
    #   3: in utero and exposed if born between 26/4/86 and 1/1/87 and resident in one of the contaminated oblasts.
    #   Date of birth is determined from the data field age_category in the attached CTB donors excel spreadsheet.
    age_category = models.CharField(max_length=2, default=None, null=True, blank=False)

    # dosimetry: Radiation doses have been calculated for all Russian cases and the majority of Ukrainian cases (some
    #   doses still remain to be calculated). Patients who are unexposed by date of birth or residency will be
    #   classified as unknown, in addition to those for which we have no dosimetry calculation.
    dosimetry = models.DecimalField(max_digits=15, decimal_places=10, default=None, null=True, blank=False)

    diagnosis = models.CharField(max_length=15, default=None, null=True, blank=False)

    # latency = (age_at_first_operation - age_at_exposure)


class Sample(models.Model):
    donor_id = models.IntegerField(null=False, blank=False)
    patient_uid = models.CharField(max_length=20, null=False, blank=False)
    item_uid = models.CharField(max_length=45, null=True, default=None)
    # 'type': Sample Origin
    type = models.CharField(max_length=20, null=False, blank=False)

    # subtype: Sample Type
    subtype = models.CharField(max_length=20, null=True, default=None)
    origin = models.CharField(max_length=20, null=True, default=None)
    tnm_type = models.CharField(max_length=15, null=True, default=None)
    diagnosis = models.CharField(max_length=45, null=False, blank=False)
    quantity = models.CharField(max_length=20, null=True, default=None)
    quality = models.CharField(max_length=20, null=True, default=None)
    note = models.TextField(null=True, blank=True, default=None)
    _STATUS = models.IntegerField(null=False, default=-1)


class Clinical_Treatment(models.Model):
    # unique CTB identifier
    patient_id = models.IntegerField(null=False, default=-1)
    # unique CTB identifier
    patient_uid = models.CharField(max_length=45, null=True, blank=False)
    edition = models.CharField(max_length=10, default=None, null=True, blank=False)
    classification_tumour = models.CharField(max_length=10, default=None, null=True, blank=False)
    classification_normal = models.CharField(max_length=10, default=None, null=True, blank=False)
    classification_metastatic = models.CharField(max_length=10, default=None, null=True, blank=False)
    stage = models.CharField(max_length=45, default=None, null=True, blank=False)
    operation_type = models.CharField(max_length=45, default=None, null=True, blank=False)
    relapse = models.BooleanField(default=False)
    # Radioiodine treatement flag
    rit = models.BooleanField(default=False)
    # Radioiodine treatement cumulative dose
    rit_value = models.IntegerField(default=None, null=True)
    # TSH Suppression flag
    tsh_suppression = models.BooleanField(default=False)
    created = models.DateTimeField(null=True, blank=False, default=timezone.now)
    modified = models.DateTimeField(null=True, blank=False, default=timezone.now)
    # datetime.now(timezone.utc)


class Driver(models.Model):
    patient_uid = models.CharField(max_length=10, null=True, blank=False)
    gene = models.CharField(max_length=50, null=True, blank=False)


class Mdta(models.Model):
    ctb_uid = models.CharField(max_length=45, null=True, blank=False)
    date = models.DateTimeField(null=False, blank=False, default=timezone.now)
    project_uid = models.CharField(max_length=45, null=True, blank=False)
    project_label = models.CharField(max_length=45, null=True, blank=False)


class Mdta_Item(models.Model):
    mdta_id = models.IntegerField(default=None, null=True)
    item_uid = models.CharField(max_length=45, null=True, blank=False)
    item_label = models.CharField(max_length=45, null=True, blank=False)
    quantity = models.IntegerField(default=0, null=False)


class Filter(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(default="Untitled", max_length=256, null=False, blank=False)
    search_type = models.CharField(max_length=10, null=False, blank=False)
    case_count = models.IntegerField(default=0, null=False)
    value = models.CharField(default=None, max_length=512, null=False, blank=False)
    owner = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    last_date_saved = models.DateTimeField(auto_now=True)

    @classmethod
    def create(cls, name, search_type, case_count, value, owner):
        new_filter_model = cls.objects.create(name=name, search_type=search_type, case_count=case_count, value=value, owner=owner)
        new_filter_model.save()

    @classmethod
    def get_list(cls, owner):
        filter_list = cls.objects.filter(owner=owner, active=True).order_by('-last_date_saved')
        return filter_list

    @classmethod
    def destroy(cls, filter_id, owner):
        try:
            filter_obj = cls.objects.get(id=filter_id)
        except cls.DoesNotExist:
            filter_obj = None
        if filter_obj:
            if filter_obj.owner == owner:
                filter_name = filter_obj.name
                filter_obj.delete()
                return_obj = {
                    'success': "Your search '{filter_name}' has been deleted.".format(filter_name=filter_name)
                }
            else:
                return_obj = {
                    'error': "You do not have access to this search: unable to delete."
                }
        else:
            return_obj = {
                'error': "Unable to locate the search. Please try again."
            }
        return return_obj
