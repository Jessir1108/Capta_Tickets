from datetime import datetime
from typing import List, Dict, Any, Optional


class TicketQueries:
    """Clase con todas las queries de MongoDB"""

    def __init__(self, db):
        self.db = db

    def get_descendant_classifiers(self, node_id: str) -> Optional[List[str]]:
        """Obtiene clasificadores descendientes"""
        if node_id == "Todos":
            return None
        descendants = list(self.db.classifiers.find({"ancestors": node_id}))
        return [node_id] + [d["_id"] for d in descendants]

    def get_all_classifiers(self) -> List[str]:
        """Obtiene todos los clasificadores"""
        classifiers = list(
            self.db.classifiers.find({"level": {"$gte": 2}}).sort("name", 1)
        )
        return ["Todos"] + [c["_id"] for c in classifiers]

    def build_match_query(
        self,
        start_date: datetime,
        end_date: datetime,
        estado: str,
        clasificador: str,
        only_date_range: bool = False,
    ) -> Dict[str, Any]:
        """Construye query de match base"""
        query = {}

        if estado != "Todos":
            query["currentState"] = estado

        if clasificador != "Todos":
            descendientes = self.get_descendant_classifiers(clasificador)
            if descendientes:
                query["currentClassifications.tipo_solicitud"] = {"$in": descendientes}

        if only_date_range:
            query["createdAt"] = {"$gte": start_date, "$lte": end_date}

        return query

    def count_tickets_by_state(
        self,
        state: str,
        match_query: Dict[str, Any],
        total_count: int,
        estado_filtro: str,
    ) -> int:
        """Cuenta tickets por estado"""
        if estado_filtro != "Todos":
            return total_count if estado_filtro == state else 0
        return self.db.tickets.count_documents({**match_query, "currentState": state})

    def get_metrics(self, start_date, end_date, estado, clasificador):
        """Obtiene todas las métricas - AHORA CON FILTRO DE FECHA"""
        query = self.build_match_query(start_date, end_date, estado, clasificador)

        # Agregar filtro de fecha a la query base
        query["createdAt"] = {"$gte": start_date, "$lte": end_date}

        total = self.db.tickets.count_documents(query)

        # Para contar por estado, necesitamos manejar el filtro de estado correctamente
        if estado != "Todos":
            abiertos = total if estado == "open" else 0
            en_progreso = total if estado == "in_progress" else 0
            cerrados = total if estado == "closed" else 0
        else:
            abiertos = self.db.tickets.count_documents(
                {**query, "currentState": "open"}
            )
            en_progreso = self.db.tickets.count_documents(
                {**query, "currentState": "in_progress"}
            )
            cerrados = self.db.tickets.count_documents(
                {**query, "currentState": "closed"}
            )

        pipeline = [
            {"$match": query},
            {"$group": {"_id": None, "total": {"$sum": "$reopenCount"}}},
        ]
        reaperturas_result = list(self.db.tickets.aggregate(pipeline))
        reaperturas = reaperturas_result[0]["total"] if reaperturas_result else 0

        return {
            "total": total,
            "abiertos": abiertos,
            "en_progreso": en_progreso,
            "cerrados": cerrados,
            "reaperturas": reaperturas,
        }

    def get_tickets_by_classifier(self, start_date, end_date, estado, clasificador):
        """Obtiene tickets agrupados por clasificador - CON FILTRO DE FECHA"""
        query = self.build_match_query(start_date, end_date, estado, clasificador)

        # Agregar filtro de fecha
        query["createdAt"] = {"$gte": start_date, "$lte": end_date}

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$currentClassifications.tipo_solicitud",
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]

        return list(self.db.tickets.aggregate(pipeline))

    def get_tickets_trend(self, start_date, end_date, estado, clasificador):
        """Obtiene tendencia de creación de tickets"""
        query = self.build_match_query(
            start_date, end_date, estado, clasificador, only_date_range=True
        )

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$createdAt"},
                        "month": {"$month": "$createdAt"},
                        "day": {"$dayOfMonth": "$createdAt"},
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        return list(self.db.tickets.aggregate(pipeline))

    def get_tickets_list(self, start_date, end_date, estado, clasificador, limit=50):
        """Obtiene lista de tickets"""
        match_query = {
            "createdAt": {"$lt": end_date},
            "$or": [
                {"closedAt": {"$exists": False}},
                {"closedAt": {"$gte": start_date}},
            ],
        }

        if clasificador != "Todos":
            descendientes = self.get_descendant_classifiers(clasificador)
            if descendientes:
                match_query["currentClassifications.tipo_solicitud"] = {
                    "$in": descendientes
                }

        if estado != "Todos":
            match_query["currentState"] = estado

        return list(
            self.db.tickets.find(match_query).sort("createdAt", -1).limit(limit)
        )

    def get_reopenings_stats(self, estado, clasificador):
        """Obtiene estadísticas de reaperturas"""
        query = self.build_match_query(None, None, estado, clasificador)
        total = self.db.tickets.count_documents(query)
        con_reaperturas = self.db.tickets.count_documents(
            {**query, "reopenCount": {"$gt": 0}}
        )
        return {
            "con_reaperturas": con_reaperturas,
            "sin_reaperturas": total - con_reaperturas,
            "total": total,
        }

    def get_resolution_time(self, start_date, end_date, estado, clasificador):
        """Obtiene tiempo de resolución"""
        query = self.build_match_query(start_date, end_date, estado, clasificador)

        pipeline = [
            {
                "$match": {
                    **query,
                    "closedAt": {"$exists": True},
                    "createdAt": {"$gte": start_date, "$lte": end_date},
                }
            },
            {
                "$project": {
                    "tiempo": {
                        "$divide": [
                            {"$subtract": ["$closedAt", "$createdAt"]},
                            1000 * 60 * 60 * 24,
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "promedio": {"$avg": "$tiempo"},
                    "minimo": {"$min": "$tiempo"},
                    "maximo": {"$max": "$tiempo"},
                }
            },
        ]

        result = list(self.db.tickets.aggregate(pipeline))
        return result[0] if result else None

    def get_closures_in_period(self, start_date, end_date, clasificador):
        """Obtiene cantidad de cierres en período"""
        query = {}
        if clasificador != "Todos":
            descendientes = self.get_descendant_classifiers(clasificador)
            if descendientes:
                query["currentClassifications.tipo_solicitud"] = {"$in": descendientes}

        pipeline = [
            {"$match": query} if query else {"$match": {}},
            {"$unwind": "$history"},
            {
                "$match": {
                    "history.action": "state_change",
                    "history.to": "closed",
                    "history.timestamp": {"$gte": start_date, "$lte": end_date},
                }
            },
            {"$count": "total"},
        ]

        result = list(self.db.tickets.aggregate(pipeline))
        return result[0]["total"] if result else 0

    def get_reopenings_in_period(self, start_date, end_date, clasificador):
        """Obtiene cantidad de reaperturas en período"""
        query = {}
        if clasificador != "Todos":
            descendientes = self.get_descendant_classifiers(clasificador)
            if descendientes:
                query["currentClassifications.tipo_solicitud"] = {"$in": descendientes}

        pipeline = [
            {"$match": query} if query else {"$match": {}},
            {"$unwind": "$history"},
            {
                "$match": {
                    "history.action": "state_change",
                    "history.from": "closed",
                    "history.to": {"$ne": "closed"},
                    "history.timestamp": {"$gte": start_date, "$lte": end_date},
                }
            },
            {"$count": "total"},
        ]

        result = list(self.db.tickets.aggregate(pipeline))
        return result[0]["total"] if result else 0

    def get_recent_actions(self, start_date, end_date, clasificador, limit=100):
        """Obtiene acciones recientes"""
        query = {"history.timestamp": {"$gte": start_date, "$lte": end_date}}

        if clasificador != "Todos":
            descendientes = self.get_descendant_classifiers(clasificador)
            if descendientes:
                query["currentClassifications.tipo_solicitud"] = {"$in": descendientes}

        pipeline = [
            {"$match": query},
            {"$unwind": "$history"},
            {"$match": {"history.timestamp": {"$gte": start_date, "$lte": end_date}}},
            {
                "$project": {
                    "ticketId": "$_id",
                    "titulo": "$title",
                    "accion": "$history.action",
                    "timestamp": "$history.timestamp",
                    "usuario": "$history.userId",
                    "desde": "$history.from",
                    "hacia": "$history.to",
                }
            },
            {"$sort": {"timestamp": -1}},
            {"$limit": limit},
        ]

        return list(self.db.tickets.aggregate(pipeline))
