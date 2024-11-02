#!/bin/bash

bluetoothctl << EOF
power on
agent NoInputNoOutput
discoverable on
pairable on
EOF
