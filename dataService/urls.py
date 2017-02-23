from django.conf.urls import url

from . import views

urlpatterns = [

	url(r'^chromosomes/$', views.chromosomes, name='chromosomes'),
	url(r'^genes/$', views.genes, name='genes'),
	url(r'^(?P<username>[a-zA-Z0-9_]+)/experiments/$', views.experiments, name='experiments'),
	url(r'^(?P<username>[a-zA-Z0-9_]+)/(?P<experiment>[a-zA-Z0-9_\- ]+)/files/$', views.files, name='files'),
	url(r'^(?P<username>[a-zA-Z0-9_]+)/(?P<experiment>[a-zA-Z0-9_\- ]+)/(?P<filename>[a-zA-Z0-9_\-. ]+)/statistics/$', views.statistics, name='statistics'),
	url(r'^(?P<username>[a-zA-Z0-9_]+)/(?P<experiment>[a-zA-Z0-9_\- ]+)/(?P<filename>[a-zA-Z0-9_\-. ]+)/details/$', views.details, name='details'),
	url(r'^(?P<username>[a-zA-Z0-9_]+)/(?P<experiment>[a-zA-Z0-9_\- ]+)/(?P<filename>[a-zA-Z0-9_\-. ]+)/filters/$', views.filters, name='filters')

]