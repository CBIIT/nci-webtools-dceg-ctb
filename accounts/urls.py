# 
# Copyright 2015-2019, Institute for Systems Biology
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

from django.conf.urls import url, include
from allauth import urls as allauth_urls
#from allauth.socialaccount.providers.google import urls as google_urls, views as google_views

from . import views


urlpatterns = [
    # url(r'^$', views.landing_page, name='landing_page'),
#    url(r'^', include(google_urls)),
    url(r'^', include(allauth_urls)),
    url(r'^logout', views.extended_logout_view, name='account_logout'),
]
