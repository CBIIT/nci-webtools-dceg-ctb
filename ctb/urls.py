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
from two_factor.urls import urlpatterns as tf_urls
from django.conf.urls import include, url

urlpatterns = [
    path('admin/', admin.site.urls),
]

from django.urls import path
from django.contrib import admin
from django.conf import settings
from . import views

admin.autodiscover()

urlpatterns = [
    url(r'^$', views.landing_page, name='landing_page'),

    # About
    url(r'^about/$', views.about, name='about'),

    # For Researchers
    url(r'^research/$', views.research, name='research'),
    url(r'^research/sample_application$', views.sample_application, name='sample_application'),

    # Contact Us
    url(r'^contact/', views.contact, name='contact'),

    url(r'^search_facility/', include('donors.urls')),

    # User Details
    url(r'^users/(?P<user_id>\d+)/$', views.user_detail, name='user_detail'),

    # Account Settings
    url(r'^accounts/', include('accounts.urls')),

    # Privacy
    url(r'^privacy/', views.privacy_policy, name='privacy'),

    path('admin/', admin.site.urls),
    url(r'session_security/', include('session_security.urls')),
    url(r'^_ah/(vm_)?health$', views.health_check),
    url(r'^warning/', views.warn_page, name='warn'),
    url(r'^searcg/', views.search, name='search'),
    url(r'^extended_login/$', views.extended_login_view, name='extended_login'),
    path('', include(tf_urls)),
]

if settings.IS_DEV:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG and settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
