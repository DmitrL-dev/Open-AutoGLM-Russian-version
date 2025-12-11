"""Web UI module for Phone Agent.

Provides a simple web dashboard to monitor and control the agent.
Runs on localhost only by default for security.
"""

import json
from pathlib import Path
from typing import Optional

# HTML template for the dashboard
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phone Agent Dashboard</title>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid var(--bg-tertiary);
        }
        
        h1 {
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .status-connected { background: var(--success); color: #000; }
        .status-disconnected { background: var(--error); }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
            margin-top: 20px;
        }
        
        .card {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 20px;
        }
        
        .card h2 {
            font-size: 1rem;
            color: var(--text-secondary);
            margin-bottom: 15px;
        }
        
        .screenshot-container {
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            aspect-ratio: 9/16;
            max-height: 600px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .screenshot-container img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        .placeholder {
            color: var(--text-secondary);
            text-align: center;
        }
        
        .task-input {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .task-input input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid var(--bg-tertiary);
            border-radius: 8px;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 1rem;
        }
        
        .task-input input:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        
        button:hover { opacity: 0.9; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .btn-primary {
            background: var(--accent);
            color: white;
        }
        
        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        .device-info {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        
        .info-item {
            background: var(--bg-primary);
            padding: 12px;
            border-radius: 8px;
        }
        
        .info-item label {
            display: block;
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }
        
        .info-item span {
            font-weight: 600;
        }
        
        .log-container {
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Consolas', monospace;
            font-size: 0.85rem;
        }
        
        .log-entry {
            padding: 4px 0;
            border-bottom: 1px solid var(--bg-tertiary);
        }
        
        .log-entry:last-child { border-bottom: none; }
        
        .log-time { color: var(--text-secondary); }
        .log-action { color: var(--accent); }
        .log-success { color: var(--success); }
        .log-error { color: var(--error); }
        
        .elements-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .element-item {
            padding: 10px;
            background: var(--bg-primary);
            border-radius: 6px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .element-item:hover { background: var(--bg-tertiary); }
        
        .element-text { font-weight: 600; }
        .element-coords { 
            font-size: 0.75rem; 
            color: var(--text-secondary);
            font-family: monospace;
        }
        
        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📱 Phone Agent Dashboard</h1>
            <span id="status-badge" class="status-badge status-disconnected">
                Checking...
            </span>
        </header>
        
        <div class="grid">
            <div class="main-panel">
                <div class="card">
                    <h2>Execute Task</h2>
                    <div class="task-input">
                        <input type="text" id="task-input" 
                               placeholder="Enter task, e.g., Open Chrome and search for weather">
                        <button class="btn-primary" onclick="executeTask()">
                            Run Task
                        </button>
                    </div>
                    
                    <h2>Quick Actions</h2>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn-secondary" onclick="executeAction('Back')">← Back</button>
                        <button class="btn-secondary" onclick="executeAction('Home')">🏠 Home</button>
                        <button class="btn-secondary" onclick="refreshScreen()">🔄 Refresh</button>
                        <button class="btn-secondary" onclick="getElements()">📋 Get Elements</button>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px;">
                    <h2>Action Log</h2>
                    <div id="log-container" class="log-container">
                        <div class="placeholder">No actions yet</div>
                    </div>
                </div>
            </div>
            
            <div class="side-panel">
                <div class="card">
                    <h2>Device</h2>
                    <div id="device-info" class="device-info">
                        <div class="info-item">
                            <label>Status</label>
                            <span id="device-status">-</span>
                        </div>
                        <div class="info-item">
                            <label>Battery</label>
                            <span id="device-battery">-</span>
                        </div>
                        <div class="info-item">
                            <label>Screen</label>
                            <span id="device-screen">-</span>
                        </div>
                        <div class="info-item">
                            <label>Current App</label>
                            <span id="device-app">-</span>
                        </div>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px;">
                    <h2>Screen</h2>
                    <div class="screenshot-container" id="screenshot-container">
                        <div class="placeholder">📱 Connect device to see screen</div>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px;">
                    <h2>UI Elements</h2>
                    <div id="elements-list" class="elements-list">
                        <div class="placeholder">Click "Get Elements" to load</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '';  // Same origin
        const API_KEY = localStorage.getItem('api_key') || '';
        
        async function apiRequest(path, options = {}) {
            const headers = { 'Content-Type': 'application/json' };
            if (API_KEY) headers['X-API-Key'] = API_KEY;
            
            const response = await fetch(API_BASE + path, { ...options, headers });
            return response.json();
        }
        
        async function checkStatus() {
            try {
                const data = await apiRequest('/');
                const badge = document.getElementById('status-badge');
                
                if (data.device_connected) {
                    badge.textContent = data.device_ready ? 'Connected' : 'Not Ready';
                    badge.className = 'status-badge ' + 
                        (data.device_ready ? 'status-connected' : 'status-disconnected');
                } else {
                    badge.textContent = 'Disconnected';
                    badge.className = 'status-badge status-disconnected';
                }
                
                // Update device info
                const deviceData = await apiRequest('/device');
                document.getElementById('device-status').textContent = 
                    deviceData.connected ? '✓ Connected' : '✗ Disconnected';
                document.getElementById('device-battery').textContent = 
                    deviceData.battery ? deviceData.battery + '%' : '-';
                document.getElementById('device-screen').textContent = 
                    deviceData.screen || '-';
                document.getElementById('device-app').textContent = 
                    deviceData.current_app?.split('/')[0] || '-';
            } catch (e) {
                console.error('Status check failed:', e);
            }
        }
        
        async function executeTask() {
            const input = document.getElementById('task-input');
            const task = input.value.trim();
            if (!task) return;
            
            addLog('Starting task: ' + task, 'action');
            
            try {
                const data = await apiRequest('/task', {
                    method: 'POST',
                    body: JSON.stringify({ task, max_steps: 50 })
                });
                
                if (data.success) {
                    addLog('Completed: ' + data.message, 'success');
                } else {
                    addLog('Failed: ' + data.message, 'error');
                }
            } catch (e) {
                addLog('Error: ' + e.message, 'error');
            }
        }
        
        async function executeAction(action) {
            addLog('Executing: ' + action, 'action');
            
            try {
                await apiRequest('/action', {
                    method: 'POST',
                    body: JSON.stringify({ 
                        action: { action, element: null, text: null }
                    })
                });
                addLog(action + ' completed', 'success');
            } catch (e) {
                addLog('Error: ' + e.message, 'error');
            }
        }
        
        async function getElements() {
            try {
                const data = await apiRequest('/ui/tree');
                const container = document.getElementById('elements-list');
                
                if (data.elements?.length) {
                    container.innerHTML = data.elements.map(el => `
                        <div class="element-item" onclick="tapElement(${el.center[0]}, ${el.center[1]})">
                            <div class="element-text">${el.text || el.resource_id || 'Unknown'}</div>
                            <div class="element-coords">[${el.center[0]}, ${el.center[1]}]</div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="placeholder">No clickable elements found</div>';
                }
            } catch (e) {
                console.error('Failed to get elements:', e);
            }
        }
        
        function tapElement(x, y) {
            addLog(`Tap at [${x}, ${y}]`, 'action');
            // Convert to normalized 0-999
            const normX = Math.min(999, Math.floor(x * 999 / 1080));
            const normY = Math.min(999, Math.floor(y * 999 / 1920));
            
            apiRequest('/action', {
                method: 'POST',
                body: JSON.stringify({
                    action: { 
                        action: 'Tap', 
                        element: { x: normX, y: normY }
                    }
                })
            });
        }
        
        function refreshScreen() {
            addLog('Refreshing screen...', 'action');
            // Would need screenshot endpoint
        }
        
        function addLog(message, type = '') {
            const container = document.getElementById('log-container');
            const time = new Date().toLocaleTimeString();
            
            // Remove placeholder if exists
            const placeholder = container.querySelector('.placeholder');
            if (placeholder) placeholder.remove();
            
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `<span class="log-time">[${time}]</span> <span class="log-${type}">${message}</span>`;
            
            container.insertBefore(entry, container.firstChild);
            
            // Keep only last 50 entries
            while (container.children.length > 50) {
                container.removeChild(container.lastChild);
            }
        }
        
        // Check status on load and periodically
        checkStatus();
        setInterval(checkStatus, 10000);
        
        // Enter key to submit
        document.getElementById('task-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeTask();
        });
    </script>
</body>
</html>
"""


def get_dashboard_html() -> str:
    """Get the dashboard HTML content."""
    return DASHBOARD_HTML


def serve_web_ui(host: str = "127.0.0.1", port: int = 3000):
    """
    Serve the Web UI.

    Args:
        host: Host to bind (localhost by default for security).
        port: Port to serve on.
    """
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    import uvicorn

    # Import and mount the API
    from phone_agent.api import create_api, APIConfig

    api_config = APIConfig(host=host, port=port)
    app = create_api(api_config)

    @app.get("/ui", response_class=HTMLResponse)
    async def web_ui():
        return get_dashboard_html()

    print(f"🌐 Web UI available at http://{host}:{port}/ui")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    serve_web_ui()
