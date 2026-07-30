import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String


@dataclass(frozen=True)
class RelayModule:
    name: str
    index: int


class UsbRelayController(Node):
    def __init__(self):
        super().__init__('usb_relay_controller')

        self.declare_parameter(
            'relay_test_path',
            '',
        )
        self.declare_parameter('module_count', 2)
        self.declare_parameter('default_target', 'all')
        self.declare_parameter('command_topic', 'relay_cmd')
        self.declare_parameter('status_topic', 'relay_status')
        self.declare_parameter('reset_on_start', False)
        self.declare_parameter('command_delay_sec', 0.0)
        self.declare_parameter('retry_count', 2)

        self.relay_test_path = self.resolve_relay_test_path(
            self.get_parameter_value('relay_test_path')
        )
        self.default_target = self.get_parameter_value('default_target').lower()
        module_count = self.get_parameter('module_count').get_parameter_value().integer_value
        self.command_delay_sec = (
            self.get_parameter('command_delay_sec').get_parameter_value().double_value
        )
        self.retry_count = self.get_parameter('retry_count').get_parameter_value().integer_value
        command_topic = self.get_parameter_value('command_topic')
        status_topic = self.get_parameter_value('status_topic')

        self.modules = [
            RelayModule(name=f'module{i + 1}', index=i)
            for i in range(max(1, int(module_count)))
        ]
        self.module_aliases = self.build_module_aliases()
        self.color_relays = {
            'red': 1,
            'r': 1,
            '빨강': 1,
            '빨간색': 1,
            'yellow': 2,
            'y': 2,
            '노랑': 2,
            '노란색': 2,
            'green': 3,
            'g': 3,
            '그린': 3,
            '초록': 3,
            '녹색': 3,
        }

        self.subscription = self.create_subscription(
            String,
            command_topic,
            self.handle_command,
            10,
        )
        self.status_pub = self.create_publisher(String, status_topic, 10)

        self.discover_modules()

        if self.get_parameter('reset_on_start').get_parameter_value().bool_value:
            self.apply_to_targets(self.modules, self.all_off)

        self.get_logger().info(
            f'USB relay controller ready. command topic={command_topic}, '
            f'modules={len(self.modules)}, default_target={self.default_target}'
        )

    def get_parameter_value(self, name):
        return self.get_parameter(name).get_parameter_value().string_value

    def resolve_relay_test_path(self, configured_path):
        if configured_path:
            return configured_path

        share_dir = Path(get_package_share_directory('usb_relay_controller'))
        packaged_tool = share_dir / 'tools' / 'relay_test'
        if packaged_tool.exists():
            return str(packaged_tool)

        source_tool = Path('/home/zxc/ros2_ws/src/usb_relay_controller/tools/relay_test')
        if source_tool.exists():
            return str(source_tool)

        return '/home/zxc/Downloads/usb_relay_linux_test/relay_test'

    def build_module_aliases(self):
        aliases = {
            'all': 'all',
            'both': 'all',
            'same': 'all',
            '전체': 'all',
            '둘다': 'all',
            '동시': 'all',
        }

        for module in self.modules:
            number = module.index + 1
            aliases[module.name] = module.name
            aliases[f'm{number}'] = module.name
            aliases[f'module{number}'] = module.name
            aliases[f'relay{number}'] = module.name
            aliases[f'보드{number}'] = module.name
            aliases[f'{number}번'] = module.name
            aliases[str(number)] = module.name

        return aliases

    def run_relay_test(self, module, *args):
        command = [self.relay_test_path, '--index', str(module.index), *args]
        last_output = ''

        for attempt in range(max(1, int(self.retry_count) + 1)):
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            output = (result.stdout + result.stderr).strip()
            if result.returncode == 0:
                return output

            last_output = output or f'command failed: {" ".join(command)}'
            time.sleep(self.command_delay_sec)

        raise RuntimeError(last_output)

    def run_relay_test_parallel(self, targets, *args):
        processes = []
        for module in targets:
            command = [self.relay_test_path, '--index', str(module.index), *args]
            processes.append((
                module,
                command,
                subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                ),
            ))

        errors = []
        names = []
        for module, command, process in processes:
            stdout, stderr = process.communicate(timeout=2.0)
            output = (stdout + stderr).strip()
            if process.returncode == 0:
                names.append(module.name)
            else:
                errors.append(output or f'command failed: {" ".join(command)}')

        if errors:
            raise RuntimeError('; '.join(errors))

        return names

    def discover_modules(self):
        result = subprocess.run(
            [self.relay_test_path, 'list'],
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
        output = (result.stdout + result.stderr).strip()
        found = re.findall(r'USBRelay index=(\d+)', output)
        if not found:
            self.get_logger().warn('No USBRelay module detected. Check USB connection/udev permission.')
            return

        self.get_logger().info(f'Detected USBRelay indexes: {", ".join(found)}')

    def set_relay(self, module, relay, enabled):
        self.run_relay_test(module, 'on' if enabled else 'off', str(relay))

    def all_off(self, module):
        self.run_relay_test(module, 'off', 'all')

    def set_mode(self, module, mode):
        if mode in ('steady', 'on', '점등'):
            self.set_relay(module, 4, True)
            return 'steady'

        if mode in ('blink', 'blinking', 'flash', '점멸'):
            self.set_relay(module, 4, False)
            return 'blink'

        raise ValueError('mode must be steady/on/점등 or blink/flash/점멸')

    def resolve_targets(self, token):
        alias = self.module_aliases.get(token.lower())
        if alias == 'all':
            return self.modules

        if alias:
            return [module for module in self.modules if module.name == alias]

        raise ValueError(f'unknown target "{token}"')

    def apply_to_targets(self, targets, action):
        results = []
        for module in targets:
            action(module)
            results.append(module.name)
            if self.command_delay_sec > 0.0:
                time.sleep(self.command_delay_sec)
        return results

    def apply_relay_to_targets(self, targets, relay, enabled):
        return self.apply_to_targets(
            targets,
            lambda module: self.set_relay(module, relay, enabled),
        )

    def apply_all_off_to_targets(self, targets):
        return self.apply_to_targets(targets, self.all_off)

    def apply_mode_to_targets(self, targets, mode):
        relay4_on = mode in ('steady', 'on', '점등')
        if not relay4_on and mode not in ('blink', 'blinking', 'flash', '점멸'):
            raise ValueError('mode must be steady/on/점등 or blink/flash/점멸')
        names = self.apply_relay_to_targets(targets, 4, relay4_on)
        return names, 'steady' if relay4_on else 'blink'

    def publish_status(self, text):
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)
        self.get_logger().info(text)

    def handle_command(self, msg):
        command = msg.data.strip()
        if not command:
            return

        try:
            status = self.execute_command(command)
            self.publish_status(f'ok: {status}')
        except Exception as error:
            self.publish_status(f'error: {command}: {error}')

    def split_target(self, tokens):
        if tokens and tokens[0].lower() in self.module_aliases:
            return self.resolve_targets(tokens[0]), tokens[1:]

        return self.resolve_targets(self.default_target), tokens

    def execute_command(self, command):
        tokens = command.lower().replace(',', ' ').split()
        if not tokens:
            raise ValueError('empty command')

        targets, tokens = self.split_target(tokens)
        if not tokens:
            raise ValueError('missing command after target')

        if tokens in (['off'], ['all', 'off'], ['off', 'all']):
            names = self.apply_all_off_to_targets(targets)
            return f'{names} all relays off'

        if tokens in (['mode', 'steady'], ['steady'], ['점등']):
            names, _ = self.apply_mode_to_targets(targets, 'steady')
            return f'{names} mode steady'

        if tokens in (['mode', 'blink'], ['mode', 'flash'], ['blink'], ['flash'], ['점멸']):
            names, _ = self.apply_mode_to_targets(targets, 'blink')
            return f'{names} mode blink'

        if len(tokens) == 2 and tokens[0] in self.color_relays:
            relay = self.color_relays[tokens[0]]
            if tokens[1] in ('on', '1', 'true', '켜', '켜기'):
                names = self.apply_relay_to_targets(targets, relay, True)
                return f'{names} {tokens[0]} on relay {relay}'
            if tokens[1] in ('off', '0', 'false', '꺼', '끄기'):
                names = self.apply_relay_to_targets(targets, relay, False)
                return f'{names} {tokens[0]} off relay {relay}'

        if len(tokens) >= 2 and tokens[0] == 'set' and tokens[1] in self.color_relays:
            color = tokens[1]
            relay = self.color_relays[color]
            mode = tokens[2] if len(tokens) >= 3 else None

            self.apply_relay_to_targets(targets, 1, False)
            self.apply_relay_to_targets(targets, 2, False)
            self.apply_relay_to_targets(targets, 3, False)
            names = self.apply_relay_to_targets(targets, relay, True)
            if mode:
                names, _ = self.apply_mode_to_targets(targets, mode)
            return f'{names} set {color}' + (f' mode {mode}' if mode else '')

        raise ValueError(
            'commands: [module1|module2|all] red/yellow/green on|off, '
            '[module1|module2|all] set red|yellow|green [steady|blink], '
            '[module1|module2|all] steady|blink, [module1|module2|all] all off'
        )


def main(args=None):
    rclpy.init(args=args)
    node = UsbRelayController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
