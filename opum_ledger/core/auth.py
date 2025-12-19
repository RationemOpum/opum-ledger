from blacksheep import Application
from blacksheep.server.authentication.apikey import APIKey, APIKeyAuthentication
from essentials.secrets import Secret
from guardpost import Policy
from guardpost.common import AuthenticatedRequirement

from opum_ledger.settings import Settings


def use_auth(app: Application, settings: Settings):
    rw_api_key_auth = APIKeyAuthentication(
        APIKey(
            secret=Secret(settings.auth.rw_x_api_key, direct_value=True),
            roles=["writer", "reader"],
        ),
        param_name="X-API-Key",
        location="header",
    )
    ro_api_key_auth = APIKeyAuthentication(
        APIKey(
            secret=Secret(settings.auth.ro_x_api_key, direct_value=True),
            roles=["reader"],
        ),
        param_name="X-API-Key",
        location="header",
    )

    app.use_authentication().add(rw_api_key_auth)
    app.use_authentication().add(ro_api_key_auth)

    authz = app.use_authorization()
    authz.default_policy = Policy("authenticated", AuthenticatedRequirement())
