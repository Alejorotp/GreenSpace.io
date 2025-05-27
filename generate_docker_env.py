import platform
import os
import textwrap

os_name = platform.system()

# Dockerfile base
dockerfile_common = textwrap.dedent("""
    FROM python:3.11-slim

    RUN apt-get update && apt-get install -y \\
        python3-dev \\
        python3-pip \\
        fontconfig \\
        libgl1-mesa-glx \\
        libxrender1 \\
        libxext6 \\
        libsm6 \\
        && rm -rf /var/lib/apt/lists/*

    RUN pip install pygame

    WORKDIR /app
    COPY . /app

    CMD ["python", "main.py"]
""")

# docker-compose base
compose_common = textwrap.dedent("""
    version: "3.8"
    services:
      greenspace:
        build: .
        volumes:
          - .:/app
        environment:
          - DISPLAY={display_env}
        stdin_open: true
        tty: true
""")

# OS-specific tweaks
if os_name == "Linux":
    network_mode = 'network_mode: "host"\n    devices:\n      - "/dev/dri:/dev/dri"'
    display_env = "${DISPLAY}"
elif os_name == "Darwin":
    network_mode = "# macOS: No network_mode or GPU device mappings"
    display_env = "host.docker.internal:0"
elif os_name == "Windows":
    network_mode = "# Windows: No network_mode or GPU device mappings"
    display_env = "host.docker.internal:0"
else:
    print("Unsupported OS:", os_name)
    exit(1)

# Write Dockerfile
with open("Dockerfile", "w") as f:
    f.write(dockerfile_common)
    print("[✔] Dockerfile generated.")

# Write docker-compose.yml
compose_final = compose_common.format(display_env=display_env).rstrip() + "\n    " + network_mode + "\n"

with open("docker-compose.yml", "w") as f:
    f.write(compose_final)
    print("[✔] docker-compose.yml generated.")

print(f"\nGenerated for {os_name}. Now you can run:\n  docker-compose up --build")
