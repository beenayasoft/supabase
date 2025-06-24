from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quote, QuoteItem
from .serializers import QuoteDetailSerializer


class EnhancedQuoteViewSetMixin:
    """
    Mixin contenant les endpoints optimisés pour le tableau de devis flexible.
    À ajouter au QuoteViewSet existant.
    """

    @action(detail=True, methods=['put', 'patch'])
    def bulk_update(self, request, pk=None):
        """
        Mettre à jour un devis complet avec tous ses éléments en une seule requête.
        Optimise les performances en évitant les multiples appels API.
        
        Payload:
        {
            "project_name": "Nom du projet",
            "project_address": "Adresse du projet",
            "notes": "Notes du devis",
            "terms_and_conditions": "Conditions générales",
            "validity_period": 30,
            "items": [
                {
                    "type": "work",
                    "parentId": null,
                    "position": 1,
                    "designation": "Nom de la prestation",
                    "description": "Description détaillée",
                    "unit": "m²",
                    "quantity": 10,
                    "unitPrice": 25.50,
                    "discount": 5,
                    "vatRate": 20,
                    "margin": 15,
                    "workId": "uuid-ouvrage"
                },
                ...
            ]
        }
        """
        try:
            quote = self.get_object()
            data = request.data
            
            with transaction.atomic():
                # Mettre à jour les informations du devis
                quote_fields = {
                    'project_name': data.get('project_name', quote.project_name),
                    'project_address': data.get('project_address', quote.project_address),
                    'notes': data.get('notes', quote.notes),
                    'terms_and_conditions': data.get('terms_and_conditions', quote.terms_and_conditions),
                    'validity_period': data.get('validity_period', quote.validity_period),
                }
                
                for field, value in quote_fields.items():
                    setattr(quote, field, value)
                
                # Traiter les éléments si fournis
                if 'items' in data:
                    items_data = data['items']
                    
                    # Supprimer tous les éléments existants
                    quote.items.all().delete()
                    
                    # Créer les nouveaux éléments
                    for item_data in items_data:
                        backend_item_data = {
                            'quote': quote,
                            'type': item_data.get('type', 'product'),
                            'parent_id': item_data.get('parentId'),
                            'position': item_data.get('position', 0),
                            'reference': item_data.get('reference', ''),
                            'designation': item_data.get('designation', ''),
                            'description': item_data.get('description', ''),
                            'unit': item_data.get('unit', ''),
                            'quantity': item_data.get('quantity', 1),
                            'unit_price': item_data.get('unitPrice', 0),
                            'discount': item_data.get('discount', 0),
                            'vat_rate': str(item_data.get('vatRate', '20')),
                            'margin': item_data.get('margin', 0),
                            'work_id': item_data.get('workId'),
                        }
                        
                        QuoteItem.objects.create(**backend_item_data)
                
                # Sauvegarder et recalculer les totaux
                quote.save()
                quote.update_totals()
            
            # Retourner le devis complet mis à jour
            detail_serializer = QuoteDetailSerializer(quote)
            return Response({
                "detail": "Devis mis à jour avec succès.",
                "quote": detail_serializer.data
            })
            
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la mise à jour: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Créer un devis complet avec tous ses éléments en une seule requête.
        """
        try:
            data = request.data
            
            with transaction.atomic():
                # Créer le devis
                quote_data = {
                    'tier_id': data.get('tier'),
                    'project_name': data.get('project_name', ''),
                    'project_address': data.get('project_address', ''),
                    'notes': data.get('notes', ''),
                    'terms_and_conditions': data.get('terms_and_conditions', ''),
                    'validity_period': data.get('validity_period', 30),
                    'created_by': request.user.username if request.user else None,
                }
                
                quote = Quote.objects.create(**quote_data)
                
                # Ajouter les éléments si fournis
                if 'items' in data:
                    items_data = data['items']
                    
                    for item_data in items_data:
                        backend_item_data = {
                            'quote': quote,
                            'type': item_data.get('type', 'product'),
                            'parent_id': item_data.get('parentId'),
                            'position': item_data.get('position', 0),
                            'reference': item_data.get('reference', ''),
                            'designation': item_data.get('designation', ''),
                            'description': item_data.get('description', ''),
                            'unit': item_data.get('unit', ''),
                            'quantity': item_data.get('quantity', 1),
                            'unit_price': item_data.get('unitPrice', 0),
                            'discount': item_data.get('discount', 0),
                            'vat_rate': str(item_data.get('vatRate', '20')),
                            'margin': item_data.get('margin', 0),
                            'work_id': item_data.get('workId'),
                        }
                        
                        QuoteItem.objects.create(**backend_item_data)
                
                # Recalculer les totaux
                quote.update_totals()
            
            # Retourner le devis complet
            detail_serializer = QuoteDetailSerializer(quote)
            return Response({
                "detail": "Devis créé avec succès.",
                "quote": detail_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la création: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnhancedQuoteItemViewSetMixin:
    """
    Mixin contenant les endpoints optimisés pour la gestion des éléments de devis.
    À ajouter au QuoteItemViewSet existant.
    """

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Réorganiser l'ordre des éléments de devis par drag-and-drop.
        
        Payload:
        {
            "quote_id": "uuid",
            "items": [
                {"id": "uuid", "position": 1},
                {"id": "uuid", "position": 2},
                ...
            ]
        }
        """
        try:
            quote_id = request.data.get('quote_id')
            items_data = request.data.get('items', [])
            
            if not quote_id:
                return Response(
                    {"detail": "quote_id est requis"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier que le devis existe
            try:
                quote = Quote.objects.get(pk=quote_id)
            except Quote.DoesNotExist:
                return Response(
                    {"detail": "Devis non trouvé"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Mettre à jour les positions
            with transaction.atomic():
                for item_data in items_data:
                    item_id = item_data.get('id')
                    new_position = item_data.get('position')
                    
                    if item_id and new_position is not None:
                        try:
                            item = QuoteItem.objects.get(pk=item_id, quote=quote)
                            item.position = new_position
                            item.save(update_fields=['position'])
                        except QuoteItem.DoesNotExist:
                            continue
            
            return Response({
                "detail": "Ordre des éléments mis à jour avec succès.",
                "updated_items": len(items_data)
            })
            
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la réorganisation: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def batch_operations(self, request):
        """
        Effectuer plusieurs opérations sur les éléments en lot.
        
        Payload:
        {
            "quote_id": "uuid",
            "operations": [
                {
                    "type": "create|update|delete",
                    "data": { ... }
                },
                ...
            ]
        }
        """
        try:
            quote_id = request.data.get('quote_id')
            operations = request.data.get('operations', [])
            
            if not quote_id:
                return Response(
                    {"detail": "quote_id est requis"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                quote = Quote.objects.get(pk=quote_id)
            except Quote.DoesNotExist:
                return Response(
                    {"detail": "Devis non trouvé"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            results = []
            
            with transaction.atomic():
                for operation in operations:
                    op_type = operation.get('type')
                    op_data = operation.get('data', {})
                    
                    if op_type == 'create':
                        # Créer un nouvel élément
                        item_data = {
                            'quote': quote,
                            'type': op_data.get('type', 'product'),
                            'parent_id': op_data.get('parentId'),
                            'position': op_data.get('position', 0),
                            'reference': op_data.get('reference', ''),
                            'designation': op_data.get('designation', ''),
                            'description': op_data.get('description', ''),
                            'unit': op_data.get('unit', ''),
                            'quantity': op_data.get('quantity', 1),
                            'unit_price': op_data.get('unitPrice', 0),
                            'discount': op_data.get('discount', 0),
                            'vat_rate': str(op_data.get('vatRate', '20')),
                            'margin': op_data.get('margin', 0),
                            'work_id': op_data.get('workId'),
                        }
                        
                        item = QuoteItem.objects.create(**item_data)
                        results.append({
                            'operation': 'create',
                            'success': True,
                            'item_id': str(item.id)
                        })
                        
                    elif op_type == 'update':
                        # Mettre à jour un élément existant
                        item_id = op_data.get('id')
                        if item_id:
                            try:
                                item = QuoteItem.objects.get(pk=item_id, quote=quote)
                                
                                # Mapper les champs frontend vers backend
                                field_mapping = {
                                    'parentId': 'parent_id',
                                    'unitPrice': 'unit_price',
                                    'vatRate': 'vat_rate',
                                    'workId': 'work_id'
                                }
                                
                                # Mettre à jour les champs fournis
                                for field, value in op_data.items():
                                    if field in field_mapping:
                                        backend_field = field_mapping[field]
                                        if backend_field == 'vat_rate':
                                            setattr(item, backend_field, str(value))
                                        else:
                                            setattr(item, backend_field, value)
                                    elif hasattr(item, field):
                                        setattr(item, field, value)
                                
                                item.save()
                                results.append({
                                    'operation': 'update',
                                    'success': True,
                                    'item_id': str(item.id)
                                })
                                
                            except QuoteItem.DoesNotExist:
                                results.append({
                                    'operation': 'update',
                                    'success': False,
                                    'error': 'Élément non trouvé',
                                    'item_id': item_id
                                })
                                
                    elif op_type == 'delete':
                        # Supprimer un élément
                        item_id = op_data.get('id')
                        if item_id:
                            try:
                                item = QuoteItem.objects.get(pk=item_id, quote=quote)
                                item.delete()
                                results.append({
                                    'operation': 'delete',
                                    'success': True,
                                    'item_id': item_id
                                })
                                
                            except QuoteItem.DoesNotExist:
                                results.append({
                                    'operation': 'delete',
                                    'success': False,
                                    'error': 'Élément non trouvé',
                                    'item_id': item_id
                                })
                
                # Recalculer les totaux du devis
                quote.update_totals()
            
            return Response({
                "detail": "Opérations effectuées avec succès.",
                "results": results
            })
            
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors des opérations en lot: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 