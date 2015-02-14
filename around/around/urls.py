from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'around.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^data_models/', include('data_models.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
