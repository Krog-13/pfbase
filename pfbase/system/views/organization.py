from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from pfbase.pagination import CustomPagination
from ..serializers.organization import OrganizationSerializer, OrganizationCreateSerializer
from ..models.organization import Organization
from rest_framework.response import Response


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

    def list(self, request, *args, **kwargs):
        no_page = request.query_params.get('paginate', 'true').lower() == 'false'

        if no_page:
            # Return all organizations without pagination
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        return super().list(request, *args, **kwargs)
