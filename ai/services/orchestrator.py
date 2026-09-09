from ai.services.context_builder import ContextBuilder
from ai.services.insight_service import InsightService
from ai.services.registry import AGENTS
from ai.services.score_service import ScoreCalculator


class AIOrchestrator:

    def analyze(self, user):

        context = ContextBuilder.build(user)

        results = {}

        for agent_class in AGENTS:

            agent = agent_class()

            results[agent.name] = agent.run(context)

        results["score"] = ScoreCalculator().calculate(context)

        results["insights"] = InsightService().generate(context)

        return results