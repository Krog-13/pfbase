from rest_framework.throttling import UserRateThrottle


class FileUploadThrottle(UserRateThrottle):
    scope = 'file-upload'