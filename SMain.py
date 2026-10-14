import asyncio
import json
import math
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# Physics Constants
GRAVITY = 9.81 * 0.5
FPS = 60
DT = 1 / FPS

class Target3D:
    def __init__(self, x, y, z, width=2.0, height=3.0, depth=2.0):
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.depth = depth
        self.active = True

    def check_collision(self, px, py, pz, radius=0.6):
        closest_x = max(self.x - self.width / 2, min(px, self.x + self.width / 2))
        closest_y = max(self.y - self.height / 2, min(py, self.y + self.height / 2))
        closest_z = max(self.z - self.depth / 2, min(pz, self.z + self.depth / 2))
        
        dx = px - closest_x
        dy = py - closest_y
        dz = pz - closest_z
        
        return (dx * dx + dy * dy + dz * dz) < (radius * radius)

class PhysicsEngine3D:
    def __init__(self):
        self.projectiles = []
        self.reset_targets()

    def reset_targets(self):
        self.targets = [
            Target3D(0, 1.5, -20),
            Target3D(-5, 1.5, -25),
            Target3D(5, 1.5, -25),
            Target3D(0, 4.5, -20),
            Target3D(-2.5, 7.5, -22)
        ]

    def add_projectile(self, x, y, z, vx, vy, vz, restitution):
        self.projectiles.append({
            "x": x, "y": y, "z": z,
            "vx": vx, "vy": vy, "vz": vz,
            "restitution": restitution,
            "active": True
        })

    def step(self):
        events = []
        for p in self.projectiles:
            if p["active"]:
                # 3D Integration
                p["vy"] -= GRAVITY * DT * 10
                p["x"] += p["vx"] * DT
                p["y"] += p["vy"] * DT
                p["z"] += p["vz"] * DT

                # Ground Plane Collision
                if p["y"] < 0.6:
                    p["y"] = 0.6
                    p["vy"] = -p["vy"] * p["restitution"]
                    p["vx"] *= 0.82
                    p["vz"] *= 0.82

                    if abs(p["vy"]) > 1.0:
                        events.append({"type": "bounce", "x": p["x"], "y": p["y"], "z": p["z"]})

                    if abs(p["vy"]) < 0.3:
                        p["vy"] = 0

                # Target Collision Check
                for t in self.targets:
                    if t.active and t.check_collision(p["x"], p["y"], p["z"]):
                        t.active = False
                        p["active"] = False
                        events.append({"type": "hit", "x": p["x"], "y": p["y"], "z": p["z"]})

        self.projectiles = [
            p for p in self.projectiles 
            if p["active"] and p["y"] >= 0.5 and abs(p["x"]) < 60 and abs(p["z"]) < 120
        ]

        return {
            "projectiles": self.projectiles,
            "targets": [
                {
                    "x": t.x, "y": t.y, "z": t.z, 
                    "w": t.width, "h": t.height, "d": t.depth, 
                    "active": t.active
                } 
                for t in self.targets
            ],
            "events": events
        }

engine = PhysicsEngine3D()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>3D Interactive Physics Sandbox</title>
    <style>
        body { margin: 0; overflow: hidden; background: #050505; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        #ui {
            position: absolute;
            bottom: 25px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 20px;
            background: rgba(15, 15, 20, 0.85);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 18px 30px;
            border-radius: 12px;
            color: white;
            align-items: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .group { display: flex; flex-direction: column; align-items: center; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
        label { font-weight: 700; margin-bottom: 6px; color: #aaa; }
        span { color: #2ecc71; font-weight: bold; margin-top: 4px; font-size: 13px; }
        input[type=range] { accent-color: #2ecc71; cursor: pointer; }
        button {
            padding: 10px 22px;
            background: #27ae60;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 13px;
            transition: all 0.2s ease;
        }
        button:hover { background: #219150; transform: translateY(-2px); }
        button.reset { background: #e74c3c; }
        button.reset:hover { background: #c0392b; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="ui">
        <div class="group">
            <label>Elevation Angle</label>
            <input type="range" id="elevation" min="0" max="90" value="45" oninput="updateUI()">
            <span id="elevVal">45°</span>
        </div>
        <div class="group">
            <label>Azimuth / Yaw</label>
            <input type="range" id="azimuth" min="-60" max="60" value="0" oninput="updateUI()">
            <span id="aziVal">0°</span>
        </div>
        <div class="group">
            <label>Velocity</label>
            <input type="range" id="velocity" min="10" max="70" value="40" oninput="updateUI()">
            <span id="velVal">40</span>
        </div>
        <div class="group">
            <label>Bounciness</label>
            <input type="range" id="bounciness" min="0" max="100" value="65" oninput="updateUI()">
            <span id="bounceVal">0.65</span>
        </div>
        <button onclick="fireCannon()">FIRE CANNON</button>
        <button class="reset" onclick="resetTargets()">RESET</button>
    </div>

    <script>
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0e17);
        scene.fog = new THREE.FogExp2(0x0a0e17, 0.015);

        const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 12, 22);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 3, -15);
        controls.update();

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xfffaed, 1.2);
        dirLight.position.set(30, 50, 20);
        dirLight.castShadow = true;
        dirLight.shadow.mapSize.width = 2048;
        dirLight.shadow.mapSize.height = 2048;
        scene.add(dirLight);

        // Ground Mesh + Grid Overlay
        const groundGeo = new THREE.PlaneGeometry(120, 150);
        const groundMat = new THREE.MeshStandardMaterial({ color: 0x1b2631, roughness: 0.8 });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);

        const grid = new THREE.GridHelper(150, 60, 0x2ecc71, 0x34495e);
        grid.position.y = 0.01;
        scene.add(grid);

        // Cannon Rig Base
        const cannonBase = new THREE.Group();
        cannonBase.position.set(0, 0.8, 0);
        scene.add(cannonBase);

        // Pivot parent for proper barrel rotation
        const barrelPivot = new THREE.Group();
        cannonBase.add(barrelPivot);

        // Barrel pointing along local -Z
        const barrelGeo = new THREE.CylinderGeometry(0.4, 0.55, 3.2, 32);
        barrelGeo.rotateX(-Math.PI / 2);
        barrelGeo.translate(0, 0, -1.6);
        
        const barrelMat = new THREE.MeshStandardMaterial({ color: 0x2c3e50, metalness: 0.8, roughness: 0.2 });
        const barrel = new THREE.Mesh(barrelGeo, barrelMat);
        barrel.castShadow = true;
        barrelPivot.add(barrel);

        // Wheels
        const wheelGeo = new THREE.CylinderGeometry(0.75, 0.75, 0.3, 24);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x8e44ad, roughness: 0.5 });
        const leftWheel = new THREE.Mesh(wheelGeo, wheelMat);
        leftWheel.rotation.z = Math.PI / 2;
        leftWheel.position.set(-0.95, 0, 0);
        leftWheel.castShadow = true;
        
        const rightWheel = leftWheel.clone();
        rightWheel.position.x = 0.95;
        cannonBase.add(leftWheel);
        cannonBase.add(rightWheel);

        // Dynamic Trajectory Arc Line
        const trajectoryGeo = new THREE.BufferGeometry();
        const trajectoryMat = new THREE.LineDashedMaterial({ color: 0x2ecc71, dashSize: 0.5, gapSize: 0.2 });
        const trajectoryLine = new THREE.Line(trajectoryGeo, trajectoryMat);
        scene.add(trajectoryLine);

        let particles = [];

        function createExplosion(x, y, z, color=0xe74c3c) {
            for(let i=0; i<20; i++) {
                const geo = new THREE.SphereGeometry(0.15, 8, 8);
                const mat = new THREE.MeshBasicMaterial({ color: color });
                const p = new THREE.Mesh(geo, mat);
                p.position.set(x, y, z);
                p.userData = {
                    vx: (Math.random() - 0.5) * 12,
                    vy: Math.random() * 10 + 2,
                    vz: (Math.random() - 0.5) * 12,
                    life: 1.0
                };
                scene.add(p);
                particles.push(p);
            }
        }

        let projectileMeshes = [];
        let targetMeshes = [];

        const ws = new WebSocket("ws://" + location.host + "/ws");

        function getCannonParams() {
            const elevDeg = parseFloat(document.getElementById("elevation").value);
            const aziDeg = parseFloat(document.getElementById("azimuth").value);
            const speed = parseFloat(document.getElementById("velocity").value);

            const elevRad = elevDeg * (Math.PI / 180);
            const aziRad = aziDeg * (Math.PI / 180);

            // Correct rotation order: Positive pitch tilts barrel upward towards -Z
            const rotationEuler = new THREE.Euler(elevRad, aziRad, 0, 'YXZ');
            
            const dir = new THREE.Vector3(0, 0, -1);
            dir.applyEuler(rotationEuler);

            const vx = dir.x * speed;
            const vy = dir.y * speed;
            const vz = dir.z * speed;

            const muzzleOffset = new THREE.Vector3(0, 0, -3.2).applyEuler(rotationEuler);
            const muzzlePos = cannonBase.position.clone().add(muzzleOffset);

            return { vx, vy, vz, elevRad, aziRad, rotationEuler, muzzlePos };
        }

        function updateUI() {
            document.getElementById("elevVal").innerText = document.getElementById("elevation").value + "°";
            document.getElementById("aziVal").innerText = document.getElementById("azimuth").value + "°";
            document.getElementById("velVal").innerText = document.getElementById("velocity").value;
            document.getElementById("bounceVal").innerText = (document.getElementById("bounciness").value / 100).toFixed(2);

            const params = getCannonParams();

            // Orient the barrel pivot container
            barrelPivot.rotation.copy(params.rotationEuler);

            drawTrajectory(params);
        }

        function drawTrajectory(params) {
            const points = [];
            let px = params.muzzlePos.x;
            let py = params.muzzlePos.y;
            let pz = params.muzzlePos.z;
            let vx = params.vx, vy = params.vy, vz = params.vz;
            const dt = 0.05;

            for (let i = 0; i < 60; i++) {
                points.push(new THREE.Vector3(px, py, pz));
                vy -= (9.81 * 0.5) * dt * 10;
                px += vx * dt;
                py += vy * dt;
                pz += vz * dt;
                if (py < 0.6) break;
            }

            trajectoryGeo.setFromPoints(points);
            trajectoryLine.computeLineDistances();
        }

        function fireCannon() {
            const params = getCannonParams();
            const bounciness = parseFloat(document.getElementById("bounciness").value) / 100;

            ws.send(JSON.stringify({
                action: "shoot",
                x: params.muzzlePos.x,
                y: params.muzzlePos.y,
                z: params.muzzlePos.z,
                vx: params.vx, 
                vy: params.vy, 
                vz: params.vz,
                restitution: bounciness
            }));
        }

        function resetTargets() {
            ws.send(JSON.stringify({ action: "reset_targets" }));
        }

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.events) {
                data.events.forEach(e => {
                    if (e.type === "hit") createExplosion(e.x, e.y, e.z, 0xf1c40f);
                    if (e.type === "bounce") createExplosion(e.x, e.y, e.z, 0x3498db);
                });
            }

            // Sync Targets
            data.targets.forEach((t, i) => {
                if (!targetMeshes[i]) {
                    const geo = new THREE.BoxGeometry(t.w, t.h, t.d);
                    const mat = new THREE.MeshStandardMaterial({ color: 0xe74c3c, metalness: 0.1, roughness: 0.4 });
                    const mesh = new THREE.Mesh(geo, mat);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    scene.add(mesh);
                    targetMeshes[i] = mesh;
                }
                targetMeshes[i].position.set(t.x, t.y, t.z);
                targetMeshes[i].visible = t.active;
            });

            // Sync Projectiles
            while (projectileMeshes.length > data.projectiles.length) {
                const mesh = projectileMeshes.pop();
                scene.remove(mesh);
            }

            data.projectiles.forEach((p, i) => {
                if (!projectileMeshes[i]) {
                    const geo = new THREE.SphereGeometry(0.6, 32, 32);
                    const mat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.9, roughness: 0.1 });
                    const mesh = new THREE.Mesh(geo, mat);
                    mesh.castShadow = true;
                    scene.add(mesh);
                    projectileMeshes[i] = mesh;
                }
                projectileMeshes[i].position.set(p.x, p.y, p.z);
            });
        };

        function animate() {
            requestAnimationFrame(animate);

            // Particle Decay
            for (let i = particles.length - 1; i >= 0; i--) {
                const p = particles[i];
                p.position.x += p.userData.vx * 0.016;
                p.position.y += p.userData.vy * 0.016;
                p.position.z += p.userData.vz * 0.016;
                p.userData.vy -= 9.8 * 0.016;
                p.userData.life -= 0.03;
                p.scale.setScalar(p.userData.life);

                if (p.userData.life <= 0) {
                    scene.remove(p);
                    particles.splice(i, 1);
                }
            }

            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        updateUI();
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
                if command.get("action") == "shoot":
                    engine.add_projectile(
                        command.get("x", 0), 
                        command.get("y", 1.5), 
                        command.get("z", 0),
                        command["vx"], command["vy"], command["vz"],
                        command.get("restitution", 0.65)
                    )
                elif command.get("action") == "reset_targets":
                    engine.reset_targets()
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



# to run this file use cd "D:\Chapter 1\megaproject2"
#                          uvicorn SMain:app --reload