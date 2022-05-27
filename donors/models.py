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
from django.db.models import Q


class Donor(models.Model):
    donor_id = models.CharField(max_length=100, unique=True)
    diagnosis = models.CharField(max_length=256, null=True, blank=False)
    gender = models.CharField(max_length=32, null=True, blank=False)
    age_category = models.IntegerField(blank=False, null=True)
    dosimetry = models.CharField(max_length=100, null=True, blank=False)
    exposed_region = models.BooleanField(default=False)


class Case(models.Model):
    donor = models.ForeignKey(Donor, null=False, blank=False, on_delete=models.CASCADE)
    tumor_size = models.CharField(max_length=100, null=True, blank=False)
    t_status = models.CharField(max_length=16, null=True, blank=False)
    n_status = models.CharField(max_length=16, null=True, blank=False)
    m_status = models.CharField(max_length=16, null=True, blank=False)
    clinical_stage = models.CharField(max_length=32, null=True, blank=False)
    operation_type = models.CharField(max_length=100, null=True, blank=False)
    relapse = models.BooleanField(default=False)
    radio_treatment = models.BooleanField(default=False)
    tsh_suppression = models.BooleanField(default=False)


class Sample(models.Model):
    donor = models.ForeignKey(Donor, null=False, blank=False, on_delete=models.CASCADE)
    sample_id = models.CharField(max_length=100, unique=True, blank=False, null=False)
    site = models.CharField(max_length=100, null=True, blank=False)
    type = models.CharField(max_length=100, null=True, blank=False)
    subtype = models.CharField(max_length=100, null=True, blank=False)
