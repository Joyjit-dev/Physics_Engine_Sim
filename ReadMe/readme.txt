# 3D Interactive Physics Sandbox



A real-time 3D physics simulation and cannon sandbox built with FastAPI, WebSockets, and Three.js. Control elevation, azimuth, velocity, and bounciness to blast targets in a 3D environment.



## Features



- Real-Time Physics Engine: Custom 3D kinematics, gravity integration, ground plane collisions, and restitution (bounciness) calculations running on the server.

- Interactive Three.js Frontend: 3D cannon model with procedural barrel rotation, dynamic trajectory arc prediction, particle explosion effects on impact/bounce, and soft shadow mapping.

- WebSocket Communication: Bidirectional low-latency state synchronization between the Python backend and browser client at 60 FPS.

- Sandbox Controls: Real-time UI sliders for elevation angle, azimuth/yaw, projectile velocity, and material bounciness.



## Tech Stack



- Backend: Python, FastAPI, Uvicorn, WebSockets

- Frontend: HTML5, JavaScript (ES6+), Three.js (r128), OrbitControls



## Installation & Setup



1. Prerequisites

Ensure you have Python 3.8+ installed along with FastAPI and Uvicorn.



2. Install Dependencies

pip install fastapi uvicorn



3. Run the Application

Save your server script as SMain.py, navigate to your project directory, and start the development server with hot-reload enabled:



uvicorn SMain:app --reload



4. Play the Sandbox

Open your browser and navigate to:

http://127.0.0.1:8000



## Controls & Usage



- Orbit Camera: Click and drag to rotate the view around the target area; scroll to zoom.

- Elevation Angle: Adjusts the vertical pitch of the cannon barrel (0 to 90 degrees).

- Azimuth / Yaw: Swivels the cannon left or right (-60 to 60 degrees).

- Velocity: Sets the initial muzzle speed of the projectile (10 to 70).

- Bounciness: Configures surface restitution upon ground impact (0 to 100%).

- FIRE CANNON: Launches a dynamic projectile into the 3D grid.

- RESET: Returns all destroyed targets back to their initial positions.