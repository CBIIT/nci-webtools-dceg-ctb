from allauth.account.auth_backends import AuthenticationBackend


class CustomAuthenticationBackend(AuthenticationBackend):
    def _check_password(self, user, password):
        return user.check_password(password)

