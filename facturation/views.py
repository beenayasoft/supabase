from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Facture, LigneFacture, PaiementFacture
from .serializers import FactureSerializer, LigneFactureSerializer, PaiementFactureSerializer
from devis.models import Devis
from django.shortcuts import get_object_or_404

class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.all()
    serializer_class = FactureSerializer

    def create(self, request, *args, **kwargs):
        devis_id = request.data.get('devis')
        if not devis_id:
            return Response({'detail': 'Un devis accepté est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        devis = get_object_or_404(Devis, pk=devis_id, statut='accepte')
        if hasattr(devis, 'facture'):
            return Response({'detail': 'Une facture existe déjà pour ce devis.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.statut != 'brouillon':
            return Response({'detail': 'Seules les factures en brouillon peuvent être modifiées.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='devis/(?P<devis_id>[^/.]+)')
    def by_devis(self, request, devis_id=None):
        factures = Facture.objects.filter(devis_id=devis_id)
        serializer = self.get_serializer(factures, many=True)
        return Response(serializer.data)

class PaiementFactureViewSet(viewsets.ModelViewSet):
    queryset = PaiementFacture.objects.all()
    serializer_class = PaiementFactureSerializer

class LigneFactureViewSet(viewsets.ModelViewSet):
    queryset = LigneFacture.objects.all()
    serializer_class = LigneFactureSerializer