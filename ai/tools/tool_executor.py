from ai.tools.tool_registry import TOOLS


class ToolExecutor:

    @staticmethod
    def execute(user, tool_name, data):

        tool = TOOLS.get(tool_name)

        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' não encontrada"
            }

        try:

            result = tool.execute(
                user,
                data
            )

            return {
                "success": True,
                "result": result
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

