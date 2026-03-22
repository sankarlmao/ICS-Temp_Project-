import os
import subprocess

USERS = {
    "guest": "guest123",
    "operator": "grid_op_2026",
    "engineer": "super_grid_eng_99"
}

def create_users():
    for user, password in USERS.items():
        try:
            # Check if user exists using id command
            user_exists = subprocess.run(["id", "-u", user], capture_output=True).returncode == 0
            
            if not user_exists:
                # User doesn't exist, try to create it.
                # If group already exists, useradd -g <group> <user>
                group_exists = subprocess.run(["getent", "group", user], capture_output=True).returncode == 0
                cmd = ["useradd", "-m", "-s", "/bin/bash"]
                if group_exists:
                    cmd += ["-g", user]
                cmd.append(user)
                
                subprocess.run(cmd, check=True)
                print(f"Created user: {user}")
            else:
                # User exists (like 'operator' system account)
                print(f"User {user} already exists. Updating home and shell.")
                subprocess.run(["usermod", "-s", "/bin/bash", "-d", f"/home/{user}", "-m", user], check=False)
                # Ensure home dir exists
                os.makedirs(f"/home/{user}", exist_ok=True)
                subprocess.run(["chown", f"{user}:{user}", f"/home/{user}"], check=False)

            # Set password
            subprocess.run(["chpasswd"], input=f"{user}:{password}", text=True, check=True)
        except Exception as e:
            print(f"Error handling user {user}: {e}")

    # Ensure /home/operator exists before writing files
    os.makedirs("/home/operator", exist_ok=True)
    subprocess.run(["chown", "operator:operator", "/home/operator"], check=False)

    # Add extra files for stages
    with open("/home/operator/notes.txt", "w") as f:
        f.write("System Maintenance Note:\nEngineer password hint: super_grid_eng_99\nSCADA server at: scada-server")
    subprocess.run(["chown", "operator:operator", "/home/operator/notes.txt"], check=False)

if __name__ == "__main__":
    create_users()
