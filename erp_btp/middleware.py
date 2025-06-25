import time
import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware pour mesurer les performances des requêtes API
    """
    
    def process_request(self, request):
        request.start_time = time.time()
        request.queries_start = len(connection.queries)
        
    def process_response(self, request, response):
        # Calculer le temps total
        if hasattr(request, 'start_time'):
            total_time = time.time() - request.start_time
            total_time_ms = total_time * 1000
            
            # Compter les requêtes SQL
            queries_count = len(connection.queries) - getattr(request, 'queries_start', 0)
            
            # Logger les performances pour les endpoints API
            if request.path.startswith('/api/'):
                method = request.method
                path = request.path
                status = response.status_code
                
                # Calcul du temps total des requêtes SQL
                sql_time = 0
                if hasattr(connection, 'queries'):
                    sql_time = sum(float(query['time']) for query in connection.queries[getattr(request, 'queries_start', 0):])
                    sql_time_ms = sql_time * 1000
                
                # Log avec couleurs pour faciliter la lecture
                if queries_count > 10:
                    level = "🚨 ATTENTION"
                elif queries_count > 3:
                    level = "⚠️ MOYEN"
                else:
                    level = "✅ OPTIMAL"
                
                logger.info(
                    f"{level} | {method} {path} | "
                    f"Status: {status} | "
                    f"Time: {total_time_ms:.2f}ms | "
                    f"SQL Queries: {queries_count} ({sql_time_ms:.2f}ms) | "
                    f"App Time: {(total_time_ms - sql_time_ms):.2f}ms"
                )
                
                # Ajouter les headers de performance pour le frontend
                response['X-Performance-Time'] = f"{total_time_ms:.2f}"
                response['X-Performance-Queries'] = str(queries_count)
                response['X-Performance-SQL-Time'] = f"{sql_time_ms:.2f}"
                
        return response 