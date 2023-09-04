from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.urls import include, path, reverse_lazy
from django.contrib.auth import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path(
        'logout/',
        views.LogoutView.as_view(template_name='registration/logged_out.html'),
        name='logout',
    ),
    path(
        'login/',
        views.LoginView.as_view(template_name='registration/login.html'),
        name='login',
    ),
    path(
        'auth/password_change/',
        views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html'
        ),
        name='password_change',
    ),
    path(
        'password_change/done/',
        views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html'
        ),
        name='password_change_done',
    ),
    path(
        'password_reset/',
        views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html'
        ),
        name='password_reset',
    ),
    path(
        'password_reset/done/',
        views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html'
        ),
        name='reset',
    ),
    path(
        'reset/done/',
        views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='reset_done',
    ),
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('pages:homepage'),
        ),
        name='registration',
    ),
    path('pages/', include('pages.urls')),
    path('', include('blog.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)

urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.page_not_found'
handler500 = 'core.views.tr_handler500'
