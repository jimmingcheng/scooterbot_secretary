import textwrap
from agents import Agent as OpenAIAgent
from agents.mcp import MCPServer
from agents.model_settings import ModelSettings


class TeslaAgent(OpenAIAgent):
    def __init__(self, user_id: str, mcp_server: MCPServer) -> None:
        self.user_id = user_id

        super().__init__(
            name=self.__class__.__name__,
            model='gpt-4.1-mini',
            instructions=self.get_instructions(),
            output_type=str,
            mcp_servers=[mcp_server],
            model_settings=ModelSettings(tool_choice="required"),
        )

    def get_instructions(self) -> str:
        return textwrap.dedent(
            '''\
            # Instructions

            1. Always start by getting the current vehicle statuses. The VIN numbers will be available here
            2. Directly answer questions about the vehicles or execute commands using the VIN numbers

            ## user_id

            {user_id}

            ## Replies

            When replying to the user, follow these guidelines

            - Round all numbers to the nearest whole number
            - Express heading in direction only, not in degrees (e.g. northwest)
            - When car is moving, always include distance from home, heading, and street
            - When car is plugged in, always include charge limit and current miles of range
            - When car is parked, don't mention speed or heading
            - Say "As of <time ago>" separately for each car

            ### Example Replies

            Q: where is the car?
            A: As of <time ago>, <car name> is parked at <location> <n> minutes from home.
            A: As of <time ago>, <car name> is <n> minutes from home and driving north on <street name> at <n> mph.
            A: As of <time ago>, <car name> is <n> minutes from home and driving south on <street name> at <n> mph. It's heading to <destination> and will arrive in <n> minutes.

            Q: how much charge do I have?
            A: As of <time ago>, <car name> is unplugged with <n> miles of range.
            A: As of <time ago>, <car name> is plugged in and ready to charge up to <p> percent with <n> miles of range.
            A: As of <time ago>, <car name> is plugged in and charging to <p> percent with <n> miles of range.
            A: As of <time ago>, <car name> is plugged in and supercharging to <p> percent with <n> miles of range.
            '''
        ).format(
            user_id=self.user_id,
        )
