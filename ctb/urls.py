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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from two_factor.urls import urlpatterns as tf_urls
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
]

admin.autodiscover()

urlpatterns = [
    re_path(r'^$', views.landing_page, name='landing_page'),

    # About
    re_path(r'^about/$', views.about, name='about'),

    # For Research
    re_path(r'^research/$', views.research, name='research'),
    re_path(r'^research/research_projects/$', views.research_projects, name='research_projects'),

    # Contact Us
    re_path(r'^contact/', views.contact, name='contact'),

    # CTB keyword search
    re_path(r'^ctb_search', views.ctb_search, name='ctb_search'),

    # Search Facility
    re_path(r'^search_facility/', include('donors.urls')),

    # User Details
    re_path(r'^users/(?P<user_id>\d+)/$', views.user_detail, name='user_detail'),

    # Account Settings
    re_path(r'^accounts/', include('accounts.urls')),

    # Privacy
    re_path(r'^privacy/', views.privacy_policy, name='privacy'),

    path('admin/', admin.site.urls),
    re_path(r'session_security/', include('session_security.urls')),
    re_path(r'^_ah/(vm_)?health$', views.health_check),
    re_path(r'^warning/', views.warn_page, name='warn'),
    re_path(r'^searcg/', views.search, name='search'),
    re_path(r'^extended_login/$', views.extended_login_view, name='extended_login'),
    path('', include(tf_urls)),

    # sitemap
    re_path(r'^sitemap/', views.sitemap, name='sitemap'),
    # Approval
    path('approval/', views.approve_account),
]


if settings.DEBUG and settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]
