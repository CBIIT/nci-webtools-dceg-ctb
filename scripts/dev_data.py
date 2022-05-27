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

from __future__ import print_function

from builtins import str
import logging
import json
import traceback
import requests
import os
import re
from os.path import join, dirname, exists
from argparse import ArgumentParser
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from uuid import uuid4
from random import randrange
from csv import reader as csv_reader

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ctb.settings")

from ctb import secret_settings, settings

import django
django.setup()

from django.contrib.auth.models import User
from donors.models import Donor, Case, Sample
from searches.models import Attribute

SAMPLE_SUBTYPE = ["RNA", "DNA", None]
SAMPLE_TYPE = ["EDTA", "Serum", "Frozen", "FFPE"]
SAMPLE_SITE = ["Blood", "Normal", "Tumor"]
CLINICAL_T = ["T1", "T1a", "T1b", "T2", "T3", "T3a", "T3b", "T4", "T4a", "T4b"]
CLINICAL_N = ["Nx", "N0", "N0a", "N0b", "N1", "N1a", "N1b"]
CLINICAL_M = ["Mx", "M0", "M1"]
CLINICAL_OP = ["Total Thyroidectomy", "Less than total"]
CLINICAL_STAGE = ["I", "II", "IIa", "IIb", "IIc", "III", "IV"]
DONOR_DIAG = ["Papillary Carcinoma", "Medullary Carcinoma", "Follicular Adenoma", "FT UMP", "WDT UMP", "Nodule", "Other"]
DONOR_GENDER = ["Male", "Female"]
DONOR_DOSIMETRY = ["Unknown", "<100mGy", "100-500 mGy", ">500 mGy"]

attr_type_map = {
    "CONTINUOUS NUMERIC": Attribute.CONTINUOUS_NUMERIC,
    "CATEGORICAL NUMERIC": Attribute.CATEGORICAL_NUMERIC,
    "STRING": Attribute.STRING,
    "CATEGORICAL": Attribute.CATEGORICAL
}

isb_superuser = User.objects.get(username="ctb")

logger = logging.getLogger('main_logger')

donor_ids = []
sample_ids = []

donors = []
samples = []
cases = []

for i in range(50):
    donor_ids.append("donor-{}".format(uuid4()))
    sample_ids.append("sample-{}".format(uuid4()))

for i in range(50):
    donor = {
        "donor_id": donor_ids[i],
        "diagnosis": DONOR_DIAG[randrange(0, (len(DONOR_DIAG)))],
        "gender": DONOR_GENDER[randrange(0, 2)],
        "age_category": randrange(1, 4),
        "dosimetry": DONOR_DOSIMETRY[randrange(0, (len(DONOR_DOSIMETRY)))],
        "exposed_region": randrange(0, 2)
    }
    donors.append(Donor(**donor))

Donor.objects.bulk_create(donors)

for i in range(50):
    sample = {
        "donor": Donor.objects.get(donor_id=donor_ids[i]),
        "sample_id": sample_ids[i],
        "site": SAMPLE_SITE[randrange(0, (len(SAMPLE_SITE)))],
        "type": SAMPLE_TYPE[randrange(0, (len(SAMPLE_TYPE)))],
        "subtype": SAMPLE_SUBTYPE[randrange(0, (len(SAMPLE_SUBTYPE)))]
    }

    samples.append(Sample(**sample))

Sample.objects.bulk_create(samples)

for i in range(50):
    case = {
        "donor": Donor.objects.get(donor_id=donor_ids[i]),
        "tumor_size": randrange(0, 20),
        "t_status": CLINICAL_T[randrange(0, (len(SAMPLE_SITE)))],
        "n_status": CLINICAL_N[randrange(0, (len(CLINICAL_N)))],
        "m_status": CLINICAL_M[randrange(0, (len(CLINICAL_M)))],
        "clinical_stage": CLINICAL_STAGE[randrange(0, (len(CLINICAL_STAGE)))],
        "operation_type": CLINICAL_OP[randrange(0, 2)],
        "relapse": randrange(0, 2),
        "radio_treatment": randrange(0, 2),
        "tsh_suppression": randrange(0, 2),
    }

    cases.append(Case(**case))

Case.objects.bulk_create(cases)

attributes = []

attr_file = open("csv/attr.csv", "r")

for line in csv_reader(attr_file):
    attr = {
        "name": line[0],
        "display_name": line[1],
        "data_type": attr_type_map[line[2]]
    }
    attributes.append(Attribute(**attr))

Attribute.objects.bulk_create(attributes)

