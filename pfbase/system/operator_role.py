"""The permission ceiling applies even if an operator is given extra grants."""
IB_OPERATOR_GROUP = 'IB operators'
IB_OPERATOR_PERMISSIONS = frozenset({'pfbase.add_user', 'pfbase.view_securityevent'})
