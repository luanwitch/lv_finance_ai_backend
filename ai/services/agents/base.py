from abc import ABC, abstractmethod

class BaseAgent:

    name = None
    title = ""

    def run(self, context):
        raise NotImplementedError

    def response(
        self,
        data=None,
        recommendations=None,
        alerts=None,
        status="success"
    ):

        return {
            "agent": self.name,
            "title": self.title,
            "status": status,
            "data": data or {},
            "recommendations": recommendations or [],
            "alerts": alerts or []
        }