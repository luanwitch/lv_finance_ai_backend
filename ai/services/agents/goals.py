from .base import BaseAgent

class GoalsAgent(BaseAgent):

    name = "goals"
    title = "Metas Financeiras"


    def run(self, context):

        goals = context.goals


        total = len(goals)

        completed = 0
        total_target = 0
        total_current = 0


        for goal in goals:

            total_target += goal.target_amount

            total_current += goal.current_amount


            if goal.status == "completed":
                completed += 1


        progress = 0

        if total_target > 0:

            progress = round(
                (total_current / total_target) * 100,
                2
            )


        return self.response(
            data={
                "total_goals": total,
                "completed": completed,
                "progress": progress,
                "remaining": float(
                    total_target - total_current
                )
            }
        )