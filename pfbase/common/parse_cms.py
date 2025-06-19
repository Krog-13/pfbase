from asn1crypto import cms, pem
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from rest_framework.views import APIView, Response, status
from rest_framework import serializers

#Сериалайзер для парсинга
class EDSVerifySerializer(serializers.Serializer):
    content = serializers.CharField()
    signature = serializers.CharField()


#Фукнция для Api
class EDSVerifyView(APIView):
    def post(self, request):
        serializer = EDSVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        signature_pem = serializer.validated_data['signature']
        result = parse_cms(signature_pem, 'organization')
        detail = 'Подпись распарсена успешно' if result['success'] else 'Ошибка при разборе подписи'

        return Response({
            'detail': detail,
            **result
        })


# Сам парсер
def parse_cms(pem_data: str, cert_type='personal') -> dict:
    try:
        pem_bytes = pem_data.encode('utf-8')
        if pem.detect(pem_bytes):
            _, _, der_bytes = pem.unarmor(pem_bytes)
        else:
            der_bytes = pem_bytes

        content_info = cms.ContentInfo.load(der_bytes)

        if content_info['content_type'].native != 'signed_data':
            raise ValueError('Это не CMS SignedData')

        signed_data = content_info['content']
        certs = signed_data['certificates'] or []

        if not certs:
            raise ValueError('Сертификаты не найдены в CMS')

        signer_cert_der = certs[0].chosen.dump()
        cert = x509.load_der_x509_certificate(signer_cert_der, default_backend())

        subject_attrs = { attr.oid._name: attr.value for attr in cert.subject }
        issuer_attrs = { attr.oid._name: attr.value for attr in cert.issuer }

        personal_fields = ['commonName', 'surname', 'givenName', 'serialNumber',  'countryName']

        organization_fields = ['commonName', 'organizationName', 'organizationalUnitName', 'serialNumber', 'countryName']

        if cert_type == 'personal':
            wanted = personal_fields
        elif cert_type == 'organization':
            wanted = organization_fields
        else:
            wanted = []

        data = {}
        for key in wanted:
            if key in subject_attrs:
                data[key] = subject_attrs[key]

        data['issuer_commonName'] = issuer_attrs.get('commonName')
        data['issuer_organizationName'] = issuer_attrs.get('organizationName')
        data['issuer_countryName'] = issuer_attrs.get('countryName')

        return {
            'success': True,
            'payload': data
        }

    except Exception as e:
        return {
            'success': False,
            'payload': { 'error': str(e) }
        }