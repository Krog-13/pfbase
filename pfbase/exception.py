class DuplicateDocumentJournal(Exception):
    """Duplicate Document"""
    pass


class AccessDenied(Exception):
    """Access Denied"""
    pass


class WrongType(Exception):
    """Wrong type for indicator value"""
    pass
