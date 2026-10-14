# 3D Rotational Physics Sandbox

An interactive, browser-based 3D simulation for exploring rotational mechanics. The project combines a **FastAPI** backend that calculates rotational physics with a **Three.js** frontend that renders a rotating axle, crossbar, and adjustable masses in real time.

## Features

- **Interactive 3D scene** rendered with Three.js.
- **Adjustable mass and radius** using sliders.
- **Adjustable friction** to observe its effect on angular motion.
- **Torque control** to apply a constant external torque while the simulation runs.
- **Live telemetry** for:
  - Moment of inertia (`I`)
  - Angular velocity (`ω`)
  - Angular acceleration (`α`)
  - Angular momentum (`L`)
  - Rotational kinetic energy (`KE`)
- **Orbit controls** to rotate the camera and inspect the assembly from different angles.
- **WebSocket communication** between the browser and the FastAPI physics engine.

## Tech Stack

- **Python**
- **FastAPI** — HTTP endpoint and WebSocket server
- **Three.js** — interactive 3D rendering
- **HTML and CSS** — interface and styling
- **JavaScript** — frontend controls and real-time updates
- **WebSockets** — continuous exchange of simulation state

## Physics Model

The simulation models a central axle and two equal point masses positioned symmetrically at radius `r`.

### Moment of inertia

The total moment of inertia is calculated as:

```text
I = I_base + 2mr²
```

Where:
- `I` is the total moment of inertia.
- `I_base` is the moment of inertia assigned to the central axle and rod.
- `m` is the mass of each adjustable weight.
- `r` is the distance from the rotation axis to each weight.

### Net torque and angular acceleration

The frictional torque is modeled as proportional to angular velocity:

```text
τ_friction = bω
τ_net = τ_applied - τ_friction
α = τ_net / I
```

Where `b` is the friction coefficient, `ω` is angular velocity, and `α` is angular acceleration.

### Angular motion

The engine updates angular velocity and angular position at a fixed simulation time step:

```text
ω_next = ω + αΔt
θ_next = θ + ω_nextΔt
```

The angle is normalized to the range from `0` to `2π` for display.

### Angular momentum and kinetic energy

The simulation also calculates:

```text
L = Iω
KE = ½Iω²
```

When the moment of inertia changes, the backend adjusts angular velocity to preserve angular momentum at that instant, using `L = Iω`. External torque and friction can subsequently change angular momentum.

> **Note:** This is an educational model. It uses a simplified inertia model, linear velocity-proportional friction, and a fixed time step; it is not intended as a full engineering-grade rigid-body simulator.

## Project Structure

The supplied code places the FastAPI backend and HTML/CSS/JavaScript frontend in a single Python file:

```text
rotational-physics-sandbox/
└── main.py
```

The filename `main.py` is a suggested name. Save the supplied Python code under that name, or adjust the run command to match your filename.

## Requirements

- Python 3.10 or newer recommended
- A modern browser with WebGL support
- Internet access when loading the Three.js libraries from their CDNs

## Installation

1. **Create a project folder** and save the supplied code as `main.py`.

2. **Create and activate a virtual environment** (recommended).

   Windows PowerShell:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   macOS or Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install fastapi "uvicorn[standard]"
   ```

## Run the Project

From the project folder, run:

```bash
uvicorn main:app --reload
```

If your Python file has a different name, replace `main` with the filename without `.py`.

Open the local address printed by Uvicorn, typically:

```text
http://127.0.0.1:8000
```

The browser connects to the backend through the `/ws` WebSocket endpoint. Keep the server running while using the simulation.

## Controls

| Control | What it does |
| --- | --- |
| **Radius** | Changes the distance of the two masses from the rotation axis. |
| **Mass** | Changes the mass of each weight and its visual scale. |
| **Friction** | Changes the coefficient used in the frictional-torque calculation. |
| **Torque: OFF / ON** | Toggles the applied external torque. |
| **Mouse drag** | Orbits the camera around the 3D scene. |
| **Mouse wheel** | Zooms the camera in or out. |

Changing the mass or radius updates the model's moment of inertia. While the simulation is spinning, the backend adjusts angular velocity to conserve angular momentum during that parameter change.

## Notes and Limitations

- The supplied code uses a single global physics-engine instance. Multiple simultaneous browser clients would therefore share the same simulation state.
- The simulation uses a fixed time step of `1 / 60` seconds.
- The frontend loads Three.js and OrbitControls from external CDNs, so those resources must be reachable by the browser.
- For deployment behind HTTPS, configure secure WebSockets (`wss://`) rather than relying on a hard-coded `ws://` connection.
- The supplied frontend and backend should be tested together after saving the code. This README documents the provided implementation and does not claim that it has been run or deployed.

## Learning Goals

Use the sandbox to investigate how changing mass, radius, applied torque, and friction affects rotational inertia and angular motion. Compare the live telemetry with the equations above to build intuition for rotational dynamics.

## License

No license was specified in the supplied project. Add a `LICENSE` file before distributing or reusing the project if you want to define its terms.