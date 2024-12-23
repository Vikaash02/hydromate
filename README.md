# HydroMATE - Capstone Project 2024/2025

## Raspberry Pi: Receive Stream and Forward via Node-RED
Install Required Software

1. Update and Upgrade Raspberry Pi:
```
sudo apt update && sudo apt upgrade -y
```

2. Install Node-RED:
```
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
```

3. Install Additional Libraries for Python: Install OpenCV and Flask to capture and process the stream:
```
sudo apt install python3-opencv python3-pip -y
pip3 install flask requests
```

## Node-RED Setup

1. Start Node-RED:
```
node-red
```

2. Access Node-RED: Open a browser and navigate to:
```
http://<Raspberry-Pi-IP>:1880
```

3. Install Required Nodes:
Go to Manage Palette > Install and search for:
```
node-red-dashboard (for the user interface).
node-red-contrib-image-output (to display video).
```

4. Create the Flow:

HTTP In Node:
- Method: POST
- URL: /video_feed

Image Output Node:
- Connect the output of the HTTP In node to the Image Output node.

Dashboard UI:
- Add a dashboard and configure the Image Output node to display the video feed.

Deploy the Flow:
- Deploy the flow and test it by visiting the Node-RED dashboard at:
```
http://<Raspberry-Pi-IP>:1880/ui
```

## Automate and Run the Programs

1. Create Systemd Service for Python Script:
```
sudo nano /etc/systemd/system/esp32_to_nodered.service
```

2. Add the following content:
```
[Unit]
Description=ESP32 to Node-RED Video Forwarder
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/esp32_to_nodered.py
Restart=always
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
```

3. Enable and Start the Service:
```
sudo systemctl enable esp32_to_nodered.service
sudo systemctl start esp32_to_nodered.service
```

4. Node-RED Automation:
Enable Node-RED to start on boot:
```
sudo systemctl enable nodered.service
```
