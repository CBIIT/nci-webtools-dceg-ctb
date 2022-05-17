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

from __future__ import absolute_import

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

from django.conf.urls import include, url
from django.urls import path
from django.contrib import admin
from django.conf import settings

from . import views

admin.autodiscover()

urlpatterns = [
    url(r'^$', views.landing_page, name='landing_page'),

    # About
    url(r'^about/', views.about_page, name='about_page'),
    url(r'^aims/', views.aims, name='aims_page'),
    url(r'^fact_sheet/', views.fact_sheet, name='fact_sheet'),
    url(r'^management_page/', views.management_page, name='management_page'),

    # For Researchers
    url(r'^researchers_page/', views.researchers_page, name='researchers_page'),
    url(r'^access_to_materials/', views.access_to_materials, name='access_to_materials'),
    url(r'^research_projects/', views.research_projects, name='research_projects'),
    url(r'^research_projects_2001_2009/', views.research_projects_2001_2009, name='research_projects_2001_2009'),
    url(r'^research_projects_2010_2019/', views.research_projects_2010_2019, name='research_projects_2010_2019'),
    url(r'^material_available/', views.material_available, name='material_available'),
    url(r'^schema_review_of_applications/', views.schema_review_of_applications, name='schema_review_of_applications'),


    # Resources
    url(r'^resources/', views.resources, name='resources'),
    url(r'^bibliography/', views.bibliography, name='bibliography'),
    url(r'^useful_links/', views.useful_links, name='useful_links'),
    url(r'^podcasts_and_videos/', views.podcasts_and_videos, name='podcasts_and_videos'),

    # Resources
    url(r'^news/', views.news, name='news'),

    # Contact Us
    url(r'^contact/', views.contact, name='contact'),

    url(r'^users/(?P<user_id>\d+)/$', views.user_detail, name='user_detail'),
#    url(r'^cohorts/', include('cohorts.urls')),
    path('admin/', admin.site.urls),
    url(r'^accounts/', include('accounts.urls')),
    url(r'session_security/', include('session_security.urls')),
    url(r'^_ah/(vm_)?health$', views.health_check),
    url(r'^warning/', views.warn_page, name='warn'),

    url(r'^searcg/', views.search, name='search'),
    url(r'^extended_login/$', views.extended_login_view, name='extended_login'),
    url(r'^privacy/', views.privacy_policy, name='privacy'),
    # url(r'^share/', include('sharing.urls')),
]

if settings.IS_DEV:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG and settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
