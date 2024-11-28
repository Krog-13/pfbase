from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from pfbase.pagination import CustomPagination
from ..serializers.organization import OrganizationSerializer, OrganizationCreateSerializer
from ..models.organization import Organization


class OrganizationAPIView(ModelViewSet):
    """
    Представление организаций
    """
    queryset = Organization.objects.all().order_by('-id')
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return OrganizationCreateSerializer  # Serializer used for POST
        return OrganizationSerializer
