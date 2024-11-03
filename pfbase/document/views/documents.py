"""
Main views by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from pfbase.base_views import AbstractModelAPIView
from pfbase.pagination import CustomPagination
from ..serializers.documents import DocumentSerializer
from ..serializers.indicators import IndicatorSerializer
from ..models.documents import Documents
from ..models.indicators import DcmIndicators


# Views for Documents
class DocumentsViewSet(AbstractModelAPIView):
    """
    Представление Documents
    """
    queryset = Documents.objects.all().order_by("-id")
    serializer_class = DocumentSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=True, methods=['get'])
    def indicator(self, request, pk=None):
        """
        Получения индикторов по :pk ABCDocument
        """
        indicators = DcmIndicators.objects.filter(document_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = IndicatorSerializer(indicators, many=True, context={'request': request})
        return Response(serializer.data)
