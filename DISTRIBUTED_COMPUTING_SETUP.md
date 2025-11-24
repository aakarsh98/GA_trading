# Distributed Computing Setup Guide
## Using Home PC for Computational Power While Working on Mac

**Last Updated:** November 24, 2025  
**Use Case:** Offload heavy GA/NN training to powerful home PC while developing on Mac

---

## Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Quick Setup (Recommended)](#quick-setup-recommended)
3. [Detailed Setup Options](#detailed-setup-options)
4. [Method Comparison](#method-comparison)
5. [Security Best Practices](#security-best-practices)
6. [Workflow Examples](#workflow-examples)
7. [Troubleshooting](#troubleshooting)

---

## Overview & Architecture

### Architecture Diagram

```
┌─────────────────┐                    ┌─────────────────┐
│   MacBook Air   │                    │   Home PC       │
│  (Development)  │◄──────────────────►│ (Computation)   │
│                 │   SSH/API/Queue    │                 │
│ - Code editing  │                    │ - GPU Training  │
│ - Testing       │                    │ - Heavy compute │
│ - Monitoring    │                    │ - Backtesting   │
└─────────────────┘                    └─────────────────┘
         │                                      │
         │                                      │
         └──────────┬───────────────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │   GitHub Repo   │
           │   (Code Sync)   │
           └─────────────────┘
```

### What You'll Achieve

- **Develop on Mac:** Write code, test small samples, monitor progress
- **Compute on PC:** Run heavy GA optimization, NN training, large backtests
- **Seamless sync:** Automatic code and result synchronization
- **Remote control:** Trigger jobs, check status, retrieve results from Mac

---

## Quick Setup (Recommended)

### Option 1: SSH + Jupyter (Easiest)

**Setup Time:** 15 minutes  
**Best For:** Beginners, minimal configuration

#### On Home PC (Windows/Linux):

```bash
# 1. Install Python and Jupyter
pip install jupyter notebook

# 2. Start Jupyter with remote access
jupyter notebook --no-browser --port=8888 --ip=0.0.0.0

# Note the token from output
```

#### On Mac:

```bash
# 1. SSH tunnel to home PC
ssh -L 8888:localhost:8888 username@home-pc-ip

# 2. Open browser to http://localhost:8888
# Enter token from PC
# Now you have full Jupyter access to home PC!
```

**Advantages:**
- ✅ Visual interface
- ✅ Easy to monitor
- ✅ Interactive development
- ✅ Built-in file browser

---

### Option 2: Ray (Production-Grade Distributed Computing)

**Setup Time:** 30 minutes  
**Best For:** Serious projects, scalable solution

#### On Home PC:

```bash
# Install Ray
pip install ray[default]

# Start Ray head node
ray start --head --port=6379 --dashboard-host=0.0.0.0 --dashboard-port=8265

# Note the address shown (e.g., ray://192.168.1.100:6379)
```

#### On Mac:

```python
# Install Ray
pip install ray[default]

# Connect to home PC cluster
import ray
ray.init(address="ray://192.168.1.100:6379")

# Now distribute your work!
@ray.remote
def train_strategy(params):
    # Your heavy computation
    return results

# This runs on home PC
futures = [train_strategy.remote(p) for p in param_list]
results = ray.get(futures)
```

**Advantages:**
- ✅ True distributed computing
- ✅ Web dashboard (http://home-pc-ip:8265)
- ✅ Automatic load balancing
- ✅ Scales to multiple machines
- ✅ Professional-grade

---

## Detailed Setup Options

### Method 1: SSH + Screen/Tmux (Simple & Reliable)

#### Initial Setup on Home PC:

```bash
# 1. Install tmux (persistent sessions)
# Ubuntu/Debian:
sudo apt install tmux

# MacOS (if PC is Mac):
brew install tmux

# Windows (use WSL2):
wsl --install
# Then inside WSL: sudo apt install tmux

# 2. Setup SSH server
# Ubuntu/Debian:
sudo apt install openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

# Windows: Enable OpenSSH Server in Windows Features
```

#### Setup SSH Key Authentication (More Secure):

```bash
# On Mac, generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to home PC
ssh-copy-id username@home-pc-ip

# Now you can SSH without password!
```

#### Workflow:

```bash
# 1. SSH into home PC
ssh username@home-pc-ip

# 2. Start tmux session
tmux new -s trading

# 3. Navigate to project
cd ~/GA_trading

# 4. Pull latest code
git pull origin clean-start

# 5. Run your heavy computation
python src/strategies/genetic_algo_robust.py

# 6. Detach from tmux (Ctrl+B, then D)
# Job continues running!

# 7. Exit SSH
exit

# Later, check progress:
ssh username@home-pc-ip
tmux attach -t trading
```

---

### Method 2: VS Code Remote SSH (Developer-Friendly)

**Best For:** Full development environment on remote machine

#### Setup:

1. **Install VS Code on Mac** (if not already installed)

2. **Install Remote-SSH Extension:**
   - Open VS Code
   - Go to Extensions (Cmd+Shift+X)
   - Search "Remote - SSH"
   - Install by Microsoft

3. **Configure SSH:**
   ```bash
   # Create/edit SSH config on Mac
   nano ~/.ssh/config
   ```

   Add:
   ```
   Host home-pc
       HostName 192.168.1.100  # Your PC's IP
       User your-username
       IdentityFile ~/.ssh/id_ed25519
   ```

4. **Connect:**
   - Press F1 in VS Code
   - Type "Remote-SSH: Connect to Host"
   - Select "home-pc"
   - Opens new window connected to PC!

5. **Open your project:**
   - File > Open Folder
   - Navigate to ~/GA_trading
   - Now you're editing files on PC from Mac!

**Advantages:**
- ✅ Full IDE experience
- ✅ Terminal integrated
- ✅ Extensions work remotely
- ✅ Git integration
- ✅ Debug remotely

---

### Method 3: REST API Server (Advanced)

Create an API server on your PC that Mac can call.

#### On Home PC:

```python
# Create: api_server.py
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/run_strategy', methods=['POST'])
def run_strategy():
    params = request.json
    
    # Save params to file
    with open('strategy_params.json', 'w') as f:
        json.dump(params, f)
    
    # Run strategy
    result = subprocess.run(
        ['python', 'src/strategies/genetic_algo_robust.py', 
         '--params', 'strategy_params.json'],
        capture_output=True,
        text=True
    )
    
    return jsonify({
        'status': 'complete',
        'output': result.stdout,
        'error': result.stderr
    })

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    # Check job status
    return jsonify({'status': 'running', 'progress': 45})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

```bash
# Install dependencies
pip install flask

# Run server
python api_server.py
```

#### On Mac:

```python
# client.py
import requests
import json

# Submit job
params = {
    'population_size': 100,
    'generations': 50,
    'mutation_rate': 0.1
}

response = requests.post(
    'http://home-pc-ip:5000/run_strategy',
    json=params
)

print(response.json())
```

---

### Method 4: Task Queue (Celery) (Production-Ready)

**Best For:** Multiple jobs, queuing, result persistence

#### On Home PC:

```bash
# Install Redis (message broker)
# Ubuntu:
sudo apt install redis-server

# Install Celery
pip install celery redis

# Create: tasks.py
from celery import Celery

app = Celery('trading_tasks', 
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

@app.task
def train_strategy(params):
    # Your training code
    import subprocess
    result = subprocess.run(['python', 'src/strategies/genetic_algo_robust.py'])
    return {'status': 'complete', 'results': '...'}

@app.task
def backtest_strategy(strategy_params):
    # Backtest code
    return {'sharpe': 1.5, 'returns': 0.25}
```

```bash
# Start Celery worker
celery -A tasks worker --loglevel=info
```

#### On Mac:

```python
# Connect to same Redis instance
from tasks import train_strategy, backtest_strategy

# Submit task (runs on PC)
result = train_strategy.delay({'generations': 100})

# Check status
print(result.status)  # PENDING, SUCCESS, FAILURE

# Get result (blocks until complete)
output = result.get()
print(output)
```

---

## Method Comparison

| Method | Setup Difficulty | Best For | Pros | Cons |
|--------|-----------------|----------|------|------|
| **Jupyter + SSH** | ⭐ Easy | Quick experiments | Interactive, visual | Not for production |
| **Ray** | ⭐⭐ Medium | Scalable ML | Professional, dashboard | Requires setup |
| **SSH + Tmux** | ⭐ Easy | Simple scripts | Minimal setup | Manual management |
| **VS Code Remote** | ⭐ Easy | Development | Full IDE | Requires stable connection |
| **REST API** | ⭐⭐⭐ Hard | Custom workflows | Flexible | Need to code API |
| **Celery Queue** | ⭐⭐⭐ Hard | Production | Robust, scalable | Complex setup |

---

## Security Best Practices

### 1. Use SSH Keys (Not Passwords)

```bash
# Generate strong key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Use passphrase for extra security
```

### 2. Configure Firewall on Home PC

```bash
# Ubuntu/Debian - allow only your Mac's IP
sudo ufw allow from 192.168.1.50 to any port 22
sudo ufw allow from 192.168.1.50 to any port 8888
sudo ufw enable
```

### 3. Use VPN for External Access

If accessing from outside home network:
- ✅ Use Tailscale (easiest): https://tailscale.com
- ✅ Or WireGuard VPN
- ❌ Don't expose SSH to public internet directly

### 4. Keep Software Updated

```bash
# Regular updates on home PC
sudo apt update && sudo apt upgrade
```

### 5. Use Environment Variables for Secrets

```bash
# Never commit API keys!
# Create .env file:
ALPACA_API_KEY=your_key_here
BINANCE_SECRET=your_secret_here

# Add to .gitignore
echo ".env" >> .gitignore
```

---

## Workflow Examples

### Workflow 1: Daily Strategy Development

**Morning (Mac):**
```bash
# 1. Pull latest code
git pull origin clean-start

# 2. Make changes to strategy
# Edit: src/strategies/genetic_algo_robust.py

# 3. Test locally with small sample
python src/strategies/genetic_algo_robust.py --quick-test

# 4. Commit and push
git add .
git commit -m "Updated fitness function"
git push origin clean-start
```

**Afternoon (Submit to PC):**
```bash
# SSH into home PC
ssh home-pc

# Pull your changes
cd ~/GA_trading
git pull origin clean-start

# Start long-running job in tmux
tmux new -s ga_training
python src/strategies/genetic_algo_robust.py --generations 1000

# Detach: Ctrl+B, then D
exit
```

**Evening (Check Results on Mac):**
```bash
# Check progress
ssh home-pc "tail -n 50 ~/GA_trading/logs/training.log"

# Or attach to tmux
ssh home-pc
tmux attach -t ga_training

# Download results
scp home-pc:~/GA_trading/best_strategy.json ./results/
```

---

### Workflow 2: Parallel Strategy Testing with Ray

**Mac (coordinator):**
```python
import ray

# Connect to home PC cluster
ray.init(address="ray://192.168.1.100:6379")

# Define remote function
@ray.remote
def optimize_strategy(strategy_type, params):
    import subprocess
    result = subprocess.run([
        'python', 
        f'src/strategies/{strategy_type}.py',
        '--params', str(params)
    ], capture_output=True)
    return result.stdout

# Run 5 different strategies in parallel
strategies = [
    ('genetic_algo_robust.py', {'gen': 100}),
    ('genetic_algo_unrestricted.py', {'gen': 100}),
    ('genetic_algo_longterm.py', {'gen': 100}),
    ('ga_multitimeframe_topdown.py', {'gen': 100}),
    ('genetic_algo_minimal.py', {'gen': 100}),
]

# Submit all at once
futures = [optimize_strategy.remote(s, p) for s, p in strategies]

# Monitor progress on dashboard: http://192.168.1.100:8265

# Wait for all to complete
results = ray.get(futures)

# Analyze results
for i, result in enumerate(results):
    print(f"Strategy {strategies[i][0]}: {result}")
```

---

### Workflow 3: Automated Overnight Training

**Setup cron job on Mac to submit jobs:**

```bash
# Edit crontab
crontab -e

# Add line to run every night at 10 PM:
0 22 * * * /usr/local/bin/python /Users/yourname/scripts/submit_training.py
```

**submit_training.py:**
```python
#!/usr/bin/env python3
import subprocess
import datetime

# SSH and submit job
subprocess.run([
    'ssh', 'home-pc',
    f'cd ~/GA_trading && '
    f'git pull && '
    f'tmux new -d -s training_{datetime.date.today()} '
    f'"python src/strategies/genetic_algo_robust.py --generations 500"'
])
```

---

## Troubleshooting

### Issue: Can't SSH to Home PC

**Solutions:**

1. **Check home PC is on same network:**
   ```bash
   # On Mac, ping PC
   ping 192.168.1.100
   ```

2. **Check SSH is running on PC:**
   ```bash
   # On PC
   sudo systemctl status ssh  # Linux
   # or check Windows OpenSSH service
   ```

3. **Check firewall:**
   ```bash
   # On PC (Linux)
   sudo ufw status
   sudo ufw allow 22
   ```

### Issue: Jupyter notebook won't connect

**Solutions:**

1. **Check tunnel is active:**
   ```bash
   # On Mac, verify tunnel
   ps aux | grep ssh
   ```

2. **Try different port:**
   ```bash
   # On PC, start on different port
   jupyter notebook --port=8889
   
   # On Mac, tunnel to that port
   ssh -L 8889:localhost:8889 username@home-pc-ip
   ```

### Issue: Ray won't connect

**Solutions:**

1. **Check Ray is running on PC:**
   ```bash
   ray status
   ```

2. **Check network connectivity:**
   ```bash
   # On Mac
   telnet home-pc-ip 6379
   ```

3. **Check firewall allows Ray ports:**
   ```bash
   # On PC
   sudo ufw allow 6379
   sudo ufw allow 8265
   ```

### Issue: Jobs fail with "module not found"

**Solutions:**

1. **Check Python environment on PC:**
   ```bash
   # On PC
   which python
   python --version
   pip list | grep numpy  # etc
   ```

2. **Use virtual environment:**
   ```bash
   # On PC, create venv
   python -m venv ~/venvs/trading
   source ~/venvs/trading/bin/activate
   pip install -r requirements.txt
   
   # Use this venv in your scripts
   ```

### Issue: Git sync conflicts

**Solutions:**

```bash
# Before pulling
git status
git stash  # Save local changes

git pull origin clean-start

# If conflicts
git stash pop
# Resolve conflicts manually
```

---

## Performance Tips

### 1. Use NVIDIA GPU on Home PC

```python
# Check GPU availability
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

# Use GPU in your code
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
```

### 2. Monitor Resource Usage

**Install htop on PC:**
```bash
sudo apt install htop
htop
```

**Monitor GPU:**
```bash
# NVIDIA
watch -n 1 nvidia-smi

# AMD
watch -n 1 radeontop
```

### 3. Optimize Data Transfer

```bash
# Compress before transfer
tar -czf results.tar.gz results/
scp home-pc:~/GA_trading/results.tar.gz ./

# Use rsync for incremental sync
rsync -avz home-pc:~/GA_trading/results/ ./results/
```

---

## Recommended Setup for Your Use Case

Based on your needs (GA + NN training), I recommend:

### Primary: **Ray + Jupyter**

**Why:**
- Ray handles distributed ML workloads perfectly
- Jupyter for interactive development and monitoring
- Professional-grade but not too complex
- Built-in dashboard for monitoring

### Backup: **VS Code Remote SSH + Tmux**

**Why:**
- Full IDE experience
- Tmux for persistent sessions
- Simpler than Ray
- Great for debugging

### Setup Steps:

```bash
# 1. On Home PC - Install everything
pip install ray[default] jupyter notebook

# Start Ray
ray start --head --dashboard-host=0.0.0.0

# Start Jupyter
jupyter notebook --no-browser --port=8888 --ip=0.0.0.0

# 2. On Mac - Connect
pip install ray[default]

# For Ray
python -c "import ray; ray.init('ray://home-pc-ip:6379')"

# For Jupyter
ssh -L 8888:localhost:8888 home-pc
# Then open http://localhost:8888
```

---

## Next Steps

1. ✅ Choose your method (recommend Ray + Jupyter)
2. ✅ Set up SSH key authentication
3. ✅ Install software on both machines
4. ✅ Test connection
5. ✅ Clone repo on home PC
6. ✅ Run test job
7. ✅ Set up monitoring
8. ✅ Automate your workflow

---

## Additional Resources

- **Ray Documentation:** https://docs.ray.io
- **Jupyter Remote:** https://jupyter-notebook.readthedocs.io
- **VS Code Remote SSH:** https://code.visualstudio.com/docs/remote/ssh
- **Tmux Cheat Sheet:** https://tmuxcheatsheet.com
- **Tailscale Setup:** https://tailscale.com/kb/

---

**Questions or Issues?**

Common questions answered in Troubleshooting section. For your specific setup, test with simple examples before running large training jobs.

**Happy Distributed Computing!** 🚀
