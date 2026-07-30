from goals.models import Goal


class CreateGoalTool:

    @staticmethod
    def execute(user, data):

        title = data.get("name")
        target_amount = data.get("target_amount")

        # Verifica se a meta já existe
        goal = Goal.objects.filter(
            user=user,
            title=title,
            status="active"
        ).first()

        if goal:
            return {
                "message": "Você já possui essa meta cadastrada.",
                "goal_id": goal.id
            }

        # Cria nova meta
        goal = Goal.objects.create(
            user=user,
            title=title,
            description="Criada pelo LV Finance IA",
            target_amount=target_amount,
            current_amount=0,
            status="active"
        )

        return {
            "message": "Meta criada com sucesso",
            "goal_id": goal.id
        }