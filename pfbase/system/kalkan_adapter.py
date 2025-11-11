"""
Модуль работы с библиотекой kalkan + SDK
Верификация подписанных данных и валидация сертификата через OCSP

Примеры кодов для получения информации из сертификата:
enums.CertProp.KC_SUBJECT_SERIALNUMBER  # ИИН format (serialNumber=IINxxxxxxxxxxxx)
enums.CertProp.KC_SUBJECT_SURNAME # Фамилия
enums.CertProp.KC_SUBJECT_COMMONNAME # Фамилия Имя
enums.CertProp.KC_SUBJECT_GIVENNAME # Отчество
enums.CertProp.KC_SUBJECT_EMAIL # Email
"""
from pfbase.exception import KalkanLibraryNotFound, KalkanError
from pykalkan import Adapter, exceptions
from threading import Lock


class KalkanAdapter:
    _instance = None
    _lock = Lock()
    _lib_path = "/usr/lib/libkalkancryptwr-64.so"

    @classmethod
    def get_adapter(cls) -> Adapter:
        with cls._lock:
            if cls._instance is None:
                try:
                    adapter = Adapter(cls._lib_path)
                except OSError:
                    raise KalkanLibraryNotFound
                adapter.init()
                cls._instance = adapter
            return cls._instance

    def verify_data(self, signature: str, data: str, cert_code: list = None) -> dict:
        """Function to verify ECP signature and validate certificate via OCSP."""
        adapter = self.get_adapter()
        try:
            output = {}
            result = adapter.verify_data(signature, data)
            cert = result.get("Cert").decode()
            validate_result = adapter.x509_validate_certificate_ocsp(cert)
            verify_info = result.get("Info").decode()

            if cert_code:
                for code in cert_code:
                    cert_info = adapter.x509_certificate_get_info(cert, code)
                    output[code.name] = cert_info.decode("utf-8", errors="ignore").strip()
            output["verification"] = True
            return output
        except exceptions.KalkanException:
            raise KalkanError

    @classmethod
    def finalize(cls):
        if cls._instance:
            cls._instance.finalize()
            cls._instance = None
