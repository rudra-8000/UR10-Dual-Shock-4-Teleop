# UR10 (URSim) Teleop with DS4 (Python, no ROS)

Tested on Ubuntu 22.04 + URSim e-Series Docker + DualShock 4 (wired).


## Quickstart

1) Start URSim (example)
- Run your URSim docker command (ports 6080 and 30001-30004 exposed).
- Open Polyscope: http://localhost:6080
- Power ON + START (release brakes).

2) Setup dependencies
```bash
./setup.sh
source .venv/bin/activate
```

3) Check Connections
```bash
python3 test_connections.py
```

4) Run
```bash
python3 ds4_ur10_teleop_2.py
```

## Notes
- Script connects to URSim via RTDE at port 30004.
- If URSim container IP changes, update ROBOT_IP in the script (or improve it to auto-detect later).
