import inspect
import textwrap
import yaml
from collections import defaultdict
from functools import lru_cache
from hubitat_maker_api_client.api_client import HubitatAPIClient
from hubitat_maker_api_client.client import HubitatClient
from typing import get_type_hints
from typing_inspect import get_origin, get_args

from secretary.ext_apis.base import ExternalAPI


class HubitatAPI(ExternalAPI):
    def overview(self) -> str:
        return "Query and control the user's smart home."

    def usage_guide(self) -> str:
        client_doc = self._hubitat_client_doc()

        return textwrap.dedent(
            """\
            # API Specification

            This class provides access to the smart home via Hubitat's Maker API:
            ```
            {client_doc}
            ```

            # Usage

            To use this API, build a python function with the following signature:

            ```
            def `function_name`(client):
            ```

            - function_name should describe the request to be fulfilled
            - return value is str and should answer the request in a way readable by an LLM agent
            - use `client` as needed to interact with the smart home

            The resulting function definition should be returned as the `function_definition`
            argument to the `invoke_api` tool.

            ## Examples of `function_definition` arguments to the `invoke_api` tool calls

            If asked to turn off a particular light:

            ```
            def turn_off_example_a_light(client):
                client.turn_off_switch('Example A Light')
                return 'Turned off Example A Light'
            ```

            If asked to lock all doors:

            ```
            def lock_all_doors(client):
                doors = ['Example A Door', 'Example B Door']
                for door in doors:
                    client.lock_door(door)

                return 'Locked doors: ' + ', '.join(doors)
            ```

            If asked to turn off all lights in the living room:

            ```
            def turn_off_living_room_lights(client):
                lights = ['Living Room Example A Light', 'Living Room Example B Light']
                for light in lights:
                    client.turn_off_switch(light)

                return 'Turned off lights: ' + ', '.join(lights)
            ```
            """
        ).format(
            client_doc=client_doc,
        )

    def initial_data(self) -> str:
        return textwrap.dedent(
            """\
            get_current_home_status()

            {current_home_status}
            """
        ).format(
            current_home_status=self._get_current_home_status()
        )

    def tool_spec_for_invoke_api(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "invoke_api",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "function_definition": {"type": "string"},
                    },
                    "required": ["function_definition"],
                }
            }
        }

    def invoke_api(self, **args) -> str:
        function_definition = args['function_definition']

        client = get_hubitat_client()

        func_name = function_definition.split('(')[0].split('def ')[1]

        invocation_func = textwrap.dedent(
            """\
            {function_definition}

            retval = {func_name}(client)
            """
        ).format(
            function_definition=function_definition,
            func_name=func_name,
        )

        invocation_func_locals = {'client': client}

        # Securely execute the dynamic code
        exec(invocation_func, {'__builtins__': None}, invocation_func_locals)

        retval = invocation_func_locals['retval']

        return f'{func_name}(client) -> {retval}'

    def _hubitat_client_doc(self) -> str:
        """Generate a description of the API with method signatures."""
        func_decl_lines = []
        for name, method in inspect.getmembers(HubitatClient, predicate=inspect.isfunction):
            if name.startswith('_'):
                continue

            type_hints = get_type_hints(method)
            params = []

            for param, hint in type_hints.items():
                if param == 'return':
                    continue
                origin = get_origin(hint)
                args = get_args(hint)
                if origin:
                    param_type = f"{origin.__name__}[{', '.join(arg.__name__ if hasattr(arg, '__name__') else str(arg) for arg in args)}]"
                else:
                    param_type = hint.__name__ if hasattr(hint, '__name__') else str(hint)
                params.append(f'{param}: {param_type}')

            return_hint = type_hints.get('return', None)
            if return_hint:
                origin = get_origin(return_hint)
                args = get_args(return_hint)
                if origin:
                    return_type = f"{origin.__name__}[{', '.join(arg.__name__ if hasattr(arg, '__name__') else str(arg) for arg in args)}]"
                else:
                    return_type = return_hint.__name__ if hasattr(return_hint, '__name__') else str(return_hint)
            else:
                return_type = 'None'

            # Format the method signature
            signature = f"    def {name}({', '.join(['self'] + params)}) -> {return_type}:"
            func_decl_lines.append(signature)

        return 'class HubitatClient:\n' + '\n'.join(func_decl_lines)

    def _get_current_home_status(self) -> str:
        WHITELISTED_CAPABILITIES = [
            'ContactSensor',
            'Lock',
            'MotionSensor',
            'SwitchLevel',
        ]

        client = get_hubitat_client()

        rooms = sorted(list(client.get_rooms()))
        capabilities = sorted([cap for cap in client.get_capabilities() if cap in WHITELISTED_CAPABILITIES])

        _room_to_capability_to_devices: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        for room in rooms:
            for capability in capabilities:
                _room_to_capability_to_devices[room][capability] = sorted(list(
                    client.get_devices_by_capability_and_room(capability, room)
                ))

        # Remove empty device arrays and prepare for yaml serialization
        room_to_capability_to_devices: dict[str, dict[str, list[str]]] = dict()
        for room, capability_to_devices in _room_to_capability_to_devices.items():
            for capability, devices in capability_to_devices.items():
                if devices:
                    if room not in room_to_capability_to_devices:
                        room_to_capability_to_devices[room] = dict()
                    if capability not in room_to_capability_to_devices[room]:
                        room_to_capability_to_devices[room][capability] = devices

        capability_to_device_to_attributes = client._get_capability_to_alias_to_attributes()
        for room, capability_to_devices in room_to_capability_to_devices.items():
            for capability, devices in capability_to_devices.items():
                for i, device in enumerate(devices):
                    attrs = capability_to_device_to_attributes[capability][device]
                    if capability == 'ContactSensor':
                        devices[i] += f' ({attrs["contact"]})'
                    elif capability == 'Lock':
                        devices[i] += f' ({attrs["lock"]})'
                    elif capability == 'MotionSensor':
                        devices[i] += f' ({attrs["motion"]})'
                    elif capability == 'SwitchLevel':
                        if attrs['switch'] == 'on':
                            devices[i] += f' ({attrs["switch"]} at {attrs["level"]}%)'
                        else:
                            devices[i] += f' ({attrs["switch"]})'

                    if 'temperature' in attrs:
                        devices[i] += f' ({attrs["temperature"]}°F)'

        return yaml.dump(dict(room_to_capability_to_devices), default_flow_style=False)


@lru_cache(maxsize=1)
def get_hubitat_client() -> HubitatClient:
    return HubitatClient(
        # TODO: Personalize smart home config
        HubitatAPIClient(
            app_id=41,
            hub_id='624b485f-ff84-4db2-a2ce-f0eefc4d3b22',
            access_token='1998ee16-1470-42b3-a9b4-6686ae2d8fb6',
        )
    )
