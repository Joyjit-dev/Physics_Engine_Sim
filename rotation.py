'''import asyncio
import json
import math
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

FPS = 60
DT = 1.0 / FPS

class RotationalPhysicsEngine:
    def __init__(self):
        # Kinematic state
        self.theta = 0.0      # Angular position (rad)
        self.omega = 0.0      # Angular velocity (rad/s)
        
        # Physical properties
        self.base_I = 2.0     # Moment of inertia of the central axle and rod
        self.m = 2.0          # Mass of each adjustable weight
        self.r = 3.0          # Radius (distance from center to weight)
        self.I = self.calculate_inertia(self.m, self.r)
        
        # Forces
        self.friction = 0.2
        self.applied_torque = 0.0

    def calculate_inertia(self, m, r):
        # I = I_base + 2 * m * r^2
        return self.base_I + (2.0 * m * (r ** 2))

    def update_parameters(self, new_m, new_r, torque, friction):
        new_I = self.calculate_inertia(new_m, new_r)
        
        # Strict Conservation of Angular Momentum: L = I * omega
        # If the user changes mass or radius mid-spin, omega must adjust instantly.
        if new_I != self.I:
            L = self.I * self.omega
            self.omega = L / new_I
            self.I = new_I
            
        self.m = new_m
        self.r = new_r
        self.applied_torque = torque
        self.friction = friction

    def step(self):
        # Net Torque = Applied Torque - Frictional Torque (proportional to velocity)
        frictional_torque = self.friction * self.omega
        tau_net = self.applied_torque - frictional_torque
        
        # alpha = tau / I
        alpha = tau_net / self.I
        
        # Integration
        self.omega += alpha * DT
        self.theta += self.omega * DT
        
        # Normalize theta to prevent float overflow over long running times
        self.theta = self.theta % (2 * math.PI)

        return {
            "theta": self.theta,
            "omega": self.omega,
            "alpha": alpha,
            "I": self.I,
            "m": self.m,
            "r": self.r
        }

engine = RotationalPhysicsEngine()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Rotational Mechanics Sandbox</title>
    <style>
        body { margin: 0; overflow: hidden; background: #0a0a0a; font-family: 'Segoe UI', sans-serif; user-select: none; }
        #ui {
            position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
            display: flex; gap: 25px; background: rgba(15, 15, 20, 0.9);
            backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 35px; border-radius: 12px; color: white; align-items: center;
        }
        #telemetry {
            position: absolute; top: 25px; left: 25px;
            background: rgba(15, 15, 20, 0.9); padding: 20px; border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1); color: #2ecc71;
            font-family: monospace; font-size: 15px; line-height: 1.6;
        }
        .telemetry-label { color: #aaa; font-weight: bold; display: inline-block; width: 140px; }
        .group { display: flex; flex-direction: column; align-items: center; font-size: 11px; font-weight: bold; letter-spacing: 1px; color: #aaa; }
        input[type=range] { accent-color: #3498db; cursor: pointer; margin: 8px 0; width: 120px; }
        span.val { color: #3498db; font-size: 14px; }
        button {
            padding: 12px 24px; background: #e67e22; color: white; border: none;
            border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;
            transition: 0.1s;
        }
        button:active { background: #d35400; transform: scale(0.95); }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="telemetry">
        <div><span class="telemetry-label">Inertia (I):</span> <span id="tel-i">0.00</span> kg·m²</div>
        <div><span class="telemetry-label">Angular Vel (ω):</span> <span id="tel-w">0.00</span> rad/s</div>
        <div><span class="telemetry-label">Acceleration (α):</span> <span id="tel-a">0.00</span> rad/s²</div>
    </div>

    <div id="ui">
        <div class="group">
            <label>Radius (r)</label>
            <input type="range" id="radius" min="1" max="8" step="0.1" value="3" oninput="sendState()">
            <span class="val" id="val-r">3.0 m</span>
        </div>
        <div class="group">
            <label>Mass (m)</label>
            <input type="range" id="mass" min="0.5" max="10" step="0.5" value="2" oninput="sendState()">
            <span class="val" id="val-m">2.0 kg</span>
        </div>
        <div class="group">
            <label>Friction</label>
            <input type="range" id="friction" min="0" max="2" step="0.1" value="0.2" oninput="sendState()">
            <span class="val" id="val-f">0.2</span>
        </div>
        <button id="torqueBtn">APPLY TORQUE</button>
    </div>

    <script>
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x0a0a0a, 0.015);

        const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 15, 20);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 2, 0);
        controls.update();

        // Lighting
        scene.add(new THREE.AmbientLight(0x404040, 1.5));
        const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
        dirLight.position.set(10, 20, 10);
        dirLight.castShadow = true;
        scene.add(dirLight);

        // Ground
        const grid = new THREE.GridHelper(100, 50, 0x333333, 0x111111);
        scene.add(grid);

        // Rotor Assembly (Group containing axle, rod, and masses)
        const rotor = new THREE.Group();
        scene.add(rotor);

        // Central Axle
        const axleGeo = new THREE.CylinderGeometry(0.3, 0.3, 8, 32);
        const axleMat = new THREE.MeshStandardMaterial({ color: 0x7f8c8d, metalness: 0.8, roughness: 0.2 });
        const axle = new THREE.Mesh(axleGeo, axleMat);
        axle.position.y = 4;
        axle.castShadow = true;
        rotor.add(axle);

        // Crossbar
        const rodGeo = new THREE.CylinderGeometry(0.15, 0.15, 18, 16);
        const rodMat = new THREE.MeshStandardMaterial({ color: 0xbdc3c7 });
        const rod = new THREE.Mesh(rodGeo, rodMat);
        rod.rotation.z = Math.PI / 2;
        rod.position.y = 6;
        rod.castShadow = true;
        rotor.add(rod);

        // Masses
        const massGeo = new THREE.SphereGeometry(1, 32, 32);
        const massMat = new THREE.MeshStandardMaterial({ color: 0xe74c3c, metalness: 0.3, roughness: 0.4 });
        
        const massLeft = new THREE.Mesh(massGeo, massMat);
        massLeft.position.y = 6;
        massLeft.castShadow = true;
        rotor.add(massLeft);

        const massRight = new THREE.Mesh(massGeo, massMat);
        massRight.position.y = 6;
        massRight.castShadow = true;
        rotor.add(massRight);

        // WebSocket & Input Handling
        let isApplyingTorque = false;
        const ws = new WebSocket("ws://" + location.host + "/ws");

        const torqueBtn = document.getElementById("torqueBtn");
        
        // Use pointer events to handle both mouse and touch
        torqueBtn.addEventListener("pointerdown", () => { isApplyingTorque = true; sendState(); });
        torqueBtn.addEventListener("pointerup", () => { isApplyingTorque = false; sendState(); });
        torqueBtn.addEventListener("pointerleave", () => { isApplyingTorque = false; sendState(); });

        function sendState() {
            const r = parseFloat(document.getElementById("radius").value);
            const m = parseFloat(document.getElementById("mass").value);
            const f = parseFloat(document.getElementById("friction").value);
            
            document.getElementById("val-r").innerText = r.toFixed(1) + " m";
            document.getElementById("val-m").innerText = m.toFixed(1) + " kg";
            document.getElementById("val-f").innerText = f.toFixed(1);

            // Scale visually based on mass
            const scale = Math.cbrt(m); 
            massLeft.scale.set(scale, scale, scale);
            massRight.scale.set(scale, scale, scale);
            
            massLeft.position.x = -r;
            massRight.position.x = r;

            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    r: r,
                    m: m,
                    friction: f,
                    torque: isApplyingTorque ? 50.0 : 0.0
                }));
            }
        }

        ws.onopen = () => sendState();

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Sync rotation from the physics engine
            rotor.rotation.y = data.theta;

            // Update telemetry
            document.getElementById("tel-i").innerText = data.I.toFixed(2);
            document.getElementById("tel-w").innerText = data.omega.toFixed(2);
            document.getElementById("tel-a").innerText = data.alpha.toFixed(2);
            
            // Server dictates the positions in case of initialization sync
            massLeft.position.x = -data.r;
            massRight.position.x = data.r;
        };

        function animate() {
            requestAnimationFrame(animate);
            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        animate();
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    async def receive_inputs():
        try:
            while True:
                data = await websocket.receive_text()
                command = json.loads(data)
                engine.update_parameters(
                    new_m=command.get("m", engine.m),
                    new_r=command.get("r", engine.r),
                    torque=command.get("torque", 0.0),
                    friction=command.get("friction", engine.friction)
                )
        except WebSocketDisconnect:
            pass

    asyncio.create_task(receive_inputs())

    try:
        while True:
            state = engine.step()
            await websocket.send_text(json.dumps(state))
            await asyncio.sleep(DT)
    except WebSocketDisconnect:
        pass

'''

import asyncio
import json
import math
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

FPS = 60
DT = 1.0 / FPS

class RotationalPhysicsEngine:
    def __init__(self):
        # Kinematic state
        self.theta = 0.0      
        self.omega = 0.0      
        
        # Physical properties
        self.base_I = 2.0     
        self.m = 2.0          
        self.r = 3.0          
        self.I = self.calculate_inertia(self.m, self.r)
        
        # Forces
        self.friction = 0.2
        self.applied_torque = 0.0

    def calculate_inertia(self, m, r):
        # Total I = I_base + 2 * m * r^2
        return self.base_I + (2.0 * m * (r ** 2))

    def update_parameters(self, new_m, new_r, torque, friction):
        new_I = self.calculate_inertia(new_m, new_r)
        
        
        
        if new_I != self.I:
            L = self.I * self.omega
            self.omega = L / new_I
            self.I = new_I
            
        self.m = new_m
        self.r = new_r
        self.applied_torque = torque
        self.friction = friction

    def step(self):
        
        frictional_torque = self.friction * self.omega
        tau_net = self.applied_torque - frictional_torque
        
        
        alpha = tau_net / self.I
        
        
        self.omega += alpha * DT
        self.theta += self.omega * DT
        self.theta = self.theta % (2 * math.pi)

        
        L = self.I * self.omega
        KE = 0.5 * self.I * (self.omega ** 2)

        return {
            "theta": self.theta,
            "omega": self.omega,
            "alpha": alpha,
            "I": self.I,
            "L": L,
            "KE": KE,
            "m": self.m,
            "r": self.r,
            "torque": self.applied_torque
        }

engine = RotationalPhysicsEngine()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>3D Rotational Physics Sandbox</title>
    <style>
        body { margin: 0; overflow: hidden; background: #080b10; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; user-select: none; }
        #ui {
            position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
            display: flex; gap: 20px; background: rgba(15, 20, 28, 0.9);
            backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 18px 30px; border-radius: 14px; color: white; align-items: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        }
        #telemetry {
            position: absolute; top: 25px; left: 25px;
            background: rgba(15, 20, 28, 0.9); padding: 20px 25px; border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.1); color: #2ecc71;
            font-family: 'Courier New', Courier, monospace; font-size: 14px; line-height: 1.8;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        }
        .telemetry-label { color: #8a9ba8; font-weight: bold; display: inline-block; width: 170px; }
        .group { display: flex; flex-direction: column; align-items: center; font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #8a9ba8; text-transform: uppercase; }
        input[type=range] { accent-color: #2ecc71; cursor: pointer; margin: 8px 0; width: 110px; }
        span.val { color: #2ecc71; font-size: 13px; font-weight: bold; }
        .torque-toggle {
            padding: 12px 20px; background: #27ae60; color: white; border: none;
            border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 13px;
            letter-spacing: 1px; transition: all 0.2s ease;
        }
        .torque-toggle.active { background: #e74c3c; animation: pulse 1s infinite alternate; }
        @keyframes pulse { from { box-shadow: 0 0 5px #e74c3c; } to { box-shadow: 0 0 20px #e74c3c; } }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="telemetry">
        <div><span class="telemetry-label">Inertia (I):</span> <span id="tel-i">0.00</span> kg·m²</div>
        <div><span class="telemetry-label">Angular Vel (ω):</span> <span id="tel-w">0.00</span> rad/s</div>
        <div><span class="telemetry-label">Acceleration (α):</span> <span id="tel-a">0.00</span> rad/s²</div>
        <div><span class="telemetry-label">Momentum (L):</span> <span id="tel-l">0.00</span> kg·m²/s</div>
        <div><span class="telemetry-label">Kinetic Energy (E_k):</span> <span id="tel-ke">0.00</span> J</div>
    </div>

    <div id="ui">
        <div class="group">
            <label>Radius (r)</label>
            <input type="range" id="radius" min="1" max="8" step="0.1" value="3" oninput="sendState()">
            <span class="val" id="val-r">3.0 m</span>
        </div>
        <div class="group">
            <label>Mass (m)</label>
            <input type="range" id="mass" min="0.5" max="10" step="0.5" value="2" oninput="sendState()">
            <span class="val" id="val-m">2.0 kg</span>
        </div>
        <div class="group">
            <label>Friction</label>
            <input type="range" id="friction" min="0" max="2" step="0.1" value="0.2" oninput="sendState()">
            <span class="val" id="val-f">0.2</span>
        </div>
        <button id="torqueBtn" class="torque-toggle" onclick="toggleTorque()">TORQUE: OFF</button>
    </div>

    <script>
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x080b10);
        scene.fog = new THREE.FogExp2(0x080b10, 0.012);

        const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 16, 24);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 4, 0);
        controls.update();

        // Lighting
        scene.add(new THREE.AmbientLight(0xffffff, 0.4));
        const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
        dirLight.position.set(15, 30, 15);
        dirLight.castShadow = true;
        scene.add(dirLight);

        // Ground Grid
        const grid = new THREE.GridHelper(100, 50, 0x2ecc71, 0x1c2833);
        scene.add(grid);

        // Rotor Group
        const rotor = new THREE.Group();
        scene.add(rotor);

        // Axle
        const axleGeo = new THREE.CylinderGeometry(0.35, 0.35, 8, 32);
        const axleMat = new THREE.MeshStandardMaterial({ color: 0x7f8c8d, metalness: 0.8, roughness: 0.2 });
        const axle = new THREE.Mesh(axleGeo, axleMat);
        axle.position.y = 4;
        axle.castShadow = true;
        rotor.add(axle);

        // Crossbar
        const rodGeo = new THREE.CylinderGeometry(0.15, 0.15, 18, 16);
        const rodMat = new THREE.MeshStandardMaterial({ color: 0xecf0f1, metalness: 0.5 });
        const rod = new THREE.Mesh(rodGeo, rodMat);
        rod.rotation.z = Math.PI / 2;
        rod.position.y = 6;
        rod.castShadow = true;
        rotor.add(rod);

        // Rotating Mass Spheres
        const massGeo = new THREE.SphereGeometry(1, 32, 32);
        const massMat = new THREE.MeshStandardMaterial({ color: 0xe74c3c, metalness: 0.3, roughness: 0.3 });
        
        const massLeft = new THREE.Mesh(massGeo, massMat);
        massLeft.position.y = 6;
        massLeft.castShadow = true;
        rotor.add(massLeft);

        const massRight = new THREE.Mesh(massGeo, massMat);
        massRight.position.y = 6;
        massRight.castShadow = true;
        rotor.add(massRight);

        // Torque Vector Indicator (Ring around axle)
        const torqueRingGeo = new THREE.TorusGeometry(1.5, 0.1, 16, 100);
        const torqueRingMat = new THREE.MeshBasicMaterial({ color: 0xe74c3c, visible: false });
        const torqueRing = new THREE.Mesh(torqueRingGeo, torqueRingMat);
        torqueRing.rotation.x = Math.PI / 2;
        torqueRing.position.y = 6;
        rotor.add(torqueRing);

        let torqueActive = false;
        const ws = new WebSocket("ws://" + location.host + "/ws");

        function toggleTorque() {
            torqueActive = !torqueActive;
            const btn = document.getElementById("torqueBtn");
            if (torqueActive) {
                btn.innerText = "TORQUE: ON";
                btn.classList.add("active");
                torqueRingMat.visible = true;
            } else {
                btn.innerText = "TORQUE: OFF";
                btn.classList.remove("active");
                torqueRingMat.visible = false;
            }
            sendState();
        }

        function sendState() {
            const r = parseFloat(document.getElementById("radius").value);
            const m = parseFloat(document.getElementById("mass").value);
            const f = parseFloat(document.getElementById("friction").value);
            
            document.getElementById("val-r").innerText = r.toFixed(1) + " m";
            document.getElementById("val-m").innerText = m.toFixed(1) + " kg";
            document.getElementById("val-f").innerText = f.toFixed(1);

            // Dynamically resize mass visuals by volume
            const scale = Math.cbrt(m / 2); 
            massLeft.scale.setScalar(scale);
            massRight.scale.setScalar(scale);
            
            massLeft.position.x = -r;
            massRight.position.x = r;

            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    r: r,
                    m: m,
                    friction: f,
                    torque: torqueActive ? 40.0 : 0.0
                }));
            }
        }

        ws.onopen = () => sendState();

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Apply rotation angle from simulation
            rotor.rotation.y = data.theta;

            // Sync telemetry metrics
            document.getElementById("tel-i").innerText = data.I.toFixed(2);
            document.getElementById("tel-w").innerText = data.omega.toFixed(2);
            document.getElementById("tel-a").innerText = data.alpha.toFixed(2);
            document.getElementById("tel-l").innerText = data.L.toFixed(2);
            document.getElementById("tel-ke").innerText = data.KE.toFixed(2);
            
            massLeft.position.x = -data.r;
            massRight.position.x = data.r;
        };

        function animate() {
            requestAnimationFrame(animate);
            if (torqueActive) {
                torqueRing.rotation.z += 0.1;
            }
            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        animate();
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    async def receive_inputs():
        try:
            while True:
                data = await websocket.receive_text()
                command = json.loads(data)
                engine.update_parameters(
                    new_m=command.get("m", engine.m),
                    new_r=command.get("r", engine.r),
                    torque=command.get("torque", 0.0),
                    friction=command.get("friction", engine.friction)
                )
        except WebSocketDisconnect:
            pass

    asyncio.create_task(receive_inputs())

    try:
        while True:
            state = engine.step()
            await websocket.send_text(json.dumps(state))
            await asyncio.sleep(DT)
    except WebSocketDisconnect:
        pass