"""Pass the authenticated actor to PostgreSQL without leaking context across requests."""
from contextlib import contextmanager
import ipaddress

from django.db import connections, transaction
from django.urls import Resolver404, resolve


@contextmanager
def database_audit_actor(user=None, request=None, *, using='default'):
    actor_id = str(user.pk) if user is not None and user.is_authenticated else ''
    address = getattr(request, 'META', {}).get('REMOTE_ADDR', '')
    try:
        address = str(ipaddress.ip_address(address)) if address else ''
    except ValueError:
        address = ''
    # SET LOCAL binds attribution to this transaction, not the pooled connection.
    with transaction.atomic(using=using):
        connection = connections[using]
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('pfbase.actor_id', true), current_setting('pfbase.actor_address', true)")
            previous_actor, previous_address = cursor.fetchone()
            cursor.execute("SELECT set_config('pfbase.actor_id', %s, true), set_config('pfbase.actor_address', %s, true)",
                           [actor_id, address])
        # On an exception atomic() restores the previous context by rollback.
        # Do not execute cleanup SQL in a transaction aborted by a SQL error.
        yield
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('pfbase.actor_id', %s, true), set_config('pfbase.actor_address', %s, true)",
                               [previous_actor or '', previous_address or ''])


def set_authenticated_audit_actor(request, user):
    """Called by JWT auth only inside a transaction opened by our middleware."""
    if not getattr(request._request, '_database_audit_transaction', False):
        return
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('pfbase.actor_id', %s, true)", [str(user.pk)])
    request._request._database_audit_authenticated = True


class DatabaseAuditMiddleware:
    # Credential failures must commit their lockout counters and audit records.
    public_auth_routes = {'token_obtain_pair', 'token_refresh', 'token_verify',
                          'password-reset', 'password-reset-confirm'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return self.get_response(request)
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return self.get_response(request)
        if match.url_name in self.public_auth_routes or (match.namespace == 'admin' and match.url_name == 'login'):
            return self.get_response(request)
        with database_audit_actor(request.user, request):
            request._database_audit_transaction = True
            request._database_audit_authenticated = request.user.is_authenticated
            response = self.get_response(request)
            # A handled validation/server error must not commit partial DCM writes.
            # Authentication failures may still commit their session-revocation log.
            if response.status_code >= 400 and response.status_code not in {401, 403} and request._database_audit_authenticated:
                transaction.set_rollback(True)
            return response
