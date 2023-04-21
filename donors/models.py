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


class Donor(models.Model):
    # patient_id: eg. UA####, RF####, BY####
    patient_id = models.IntegerField(default=None, null=True, blank=False)
    # patient_uid: CBT uid
    patient_uid = models.CharField(max_length=20, default=None, null=True, blank=False)
    # gender: female, male
    gender = models.CharField(max_length=10, default=None, null=True, blank=False)
    # oblast_at_accident: Patient residency
    # Exposed region -
    #   In Russia, Kaluga, Tula, Oryol (Orel) and Bryansk
    #   In Ukraine, Kiev, Kiev city, Rovno, Cherkasse, Zhitomyr, Chernigov and Sumy.
    # Although technically not an oblast, Pripyat, the village closest to the reactor site is also included as a
    # location that is classified as exposed. Oblasts outside of those listed above are all classified as being
    # unexposed regions.
    oblast_at_accident = models.CharField(max_length=45, default=None, null=True, blank=False)
    # country_at_accident: Patient country - Belarus, Ukraine, Russia
    country_at_accident = models.CharField(max_length=45, default=None, null=True, blank=False)
    # diagnosis: deferred = Deferred
    # FA = Follicular adenoma
    # FC = Follicular carcinoma
    # FT = Follicular tumour
    # FT UMP = follicular tumour of uncertain malignant potential
    # metastatic = Metastatic
    # MTC = Medullary carcinoma
    # NIFTP = Noninvasive follicular thyroid neoplasm with papillary-like nuclear features
    # nodule = Benign nodule
    # none = No diagnosis
    # normal = Normal
    # other = Other
    # PDC = Poorly differentiated carcinoma
    # PTC = Papillary carcinoma
    # TTT = Two tumour types
    # u PTC = Micro papillary carcinoma
    # WDCA NOS = Well differentiated carcinoma not otherwise specified
    # WDT UMP = Well differentiated tumour of uncertain malignant potential
    diagnosis = models.CharField(max_length=15, default=None, null=True, blank=False)
    # age_at_first_operation: age at operation
    age_at_first_operation = models.IntegerField(default=None, null=True, blank=False)
    # age_at_exposure: Age at accident
    age_at_exposure = models.IntegerField(default=None, null=True, blank=False)
    # age_category: 1 = <1987,  2 = 1987+
    age_category = models.IntegerField(default=None, null=True, blank=False)
    # dosimetry: Valid dose value, NULL = Missing value
    dosimetry = models.DecimalField(max_digits=15, decimal_places=10, default=None, null=True, blank=False)
    # country_current = models.CharField(max_length=45, default=None, null=True, blank=False)
    # oblast_current = models.CharField(max_length=45, default=None, null=True, blank=False)


class Sample(models.Model):
    donor_id = models.IntegerField(null=False, blank=False)
    patient_uid = models.CharField(max_length=20, null=False, blank=False)
    item_uid = models.CharField(max_length=45, null=True, default=None)
    type = models.CharField(max_length=20, null=False, blank=False)
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

# class Mdta(models.Model):
#     ctb_uid = models.CharField(max_length=45, null=True, blank=False)
#     date = models.DateTimeField(null=False, blank=False, default=timezone.now)
#     project_uid = models.CharField(max_length=45, null=True, blank=False)
#     project_label = models.CharField(max_length=45, null=True, blank=False)
#
#
# class Mdta_Item(models.Model):
#     mdta_id = models.IntegerField(default=None, null=True)
#     item_uid = models.CharField(max_length=45, null=True, blank=False)
#     item_label = models.CharField(max_length=45, null=True, blank=False)
#     quantity = models.IntegerField(default=0, null=False)


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
