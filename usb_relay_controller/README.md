# usb_relay_controller

ROS 2 Humble package for DCTTech/JK USBRelay4 HID relay modules.

## Relay Map

```text
Relay 1 -> red lamp
Relay 2 -> yellow lamp
Relay 3 -> green lamp
Relay 4 ON  -> NO, steady mode
Relay 4 OFF -> NC, blink mode
```

Two USBRelay4 modules can be controlled independently or together.

## Build

```bash
cd ~/ros2_ws
colcon build --packages-select usb_relay_controller
source install/setup.bash
```

## Udev Rule

```bash
sudo cp ~/ros2_ws/src/usb_relay_controller/udev/99-usb-relay.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Unplug and reconnect the relay boards after installing the rule.

## Check USB Relays

```bash
~/ros2_ws/src/usb_relay_controller/tools/relay_test list
```

Expected output with two modules:

```text
16c0:05df bus=1 addr=6  <-- USBRelay index=0
16c0:05df bus=1 addr=7  <-- USBRelay index=1
```

## Run

```bash
ros2 run usb_relay_controller usb_relay_controller --ros-args -p module_count:=2
```

Or:

```bash
ros2 launch usb_relay_controller usb_relay_controller.launch.py
```

## Commands

Publish commands to `/relay_cmd`:

```bash
ros2 topic pub --once /relay_cmd std_msgs/msg/String "{data: module1 red on}"
ros2 topic pub --once /relay_cmd std_msgs/msg/String "{data: module2 yellow on}"
ros2 topic pub --once /relay_cmd std_msgs/msg/String "{data: all green on}"
ros2 topic pub --once /relay_cmd std_msgs/msg/String "{data: all off}"
ros2 topic pub --once /relay_cmd std_msgs/msg/String "{data: all steady}"
ros2 topic pub --once /relay_cmd std_msgs/msg/String "{data: all blink}"
```

`all` sends commands to both modules. `module1` maps to USBRelay index 0 and
`module2` maps to USBRelay index 1.

## Direct Tool

```bash
tools/relay_test list
tools/relay_test --index 0 on 1
tools/relay_test --index 0 off 1
tools/relay_test --index 1 on 1
tools/relay_test --index 1 off 1
```
