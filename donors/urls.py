# 
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
# 

from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^dashboard/', views.dashboard, name='dashboard'),
    re_path(r'^saved_searches/', views.saved_searches, name='saved_searches'),
    re_path(r'^get_search_list/', views.get_search_list, name='get_search_list'),
    re_path(r'^get_submissions_list/', views.get_submissions_list, name='get_submissions_list'),
    re_path(r'^save_filters', views.save_filters, name='save_filters'),
    re_path(r'^delete_filters/(?P<filter_id>\d+)/', views.delete_filters, name='delete_filters'),
    re_path(r'^open_file/(?P<submission_id>.*)/(?P<att>\d+)/', views.open_file, name='open_file'),
    re_path(r'^search_samples/search_tissue_samples', views.search_tissue_samples, name='search_tissue_samples'),
    re_path(r'^search_samples/filter_tissue_samples', views.filter_tissue_samples, name='filter_tissue_samples'),
    re_path(r'^search_samples/search_clinical', views.search_clinical, name='search_clinical'),
    re_path(r'^search_samples/clinical_search_facility', views.clinical_search_facility, name='clinical_search_facility'),
    re_path(r'^search_samples/driver_search_facility', views.driver_search_facility, name='driver_search_facility'),
    re_path(r'^search_samples/make_application', views.make_application, name='make_application'),
    re_path(r'^search_samples/application_submit', views.application_submit, name='application_submit')

]
