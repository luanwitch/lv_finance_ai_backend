from ai.services.orchestrator import AIOrchestrator


class UserTest:

    id = 1
    name = "Teste"


user = UserTest()


ai = AIOrchestrator()

response = ai.analyze(user)


print(response)