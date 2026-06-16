const { app, BrowserWindow, Tray, Menu, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let tray = null;
let serverProcess = null;
const PORT = 18865;

// Find Python executable
function getPythonExecutable() {
  // Try different Python commands
  const pythonCommands = ['python', 'python3', 'python.exe', 'python3.exe'];

  // On Windows, try common installation paths
  if (process.platform === 'win32') {
    const pythonPaths = [
      'python',
      'python3',
      path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python3*', 'python.exe'),
      path.join(process.env.ProgramFiles || '', 'Python3*', 'python.exe'),
    ];
    return 'python'; // Default to 'python' on Windows
  }

  return 'python3'; // Default to 'python3' on Linux/Mac
}

// Start Python server
function startServer() {
  const resourcePath = process.resourcesPath || path.join(__dirname, '..');
  const serverPath = path.join(resourcePath, 'agent_notify');

  const pythonExe = getPythonExecutable();
  const serverArgs = ['-m', 'agent_notify.server', String(PORT)];

  console.log('Starting server:', pythonExe, serverArgs.join(' '));
  console.log('Server path:', serverPath);

  serverProcess = spawn(pythonExe, serverArgs, {
    cwd: serverPath,
    env: { ...process.env, PYTHONPATH: serverPath },
    stdio: 'inherit' // Show server logs in console
  });

  serverProcess.on('error', (err) => {
    console.error('Server error:', err);
    dialog.showErrorBox('Server Error', `Failed to start Python server: ${err.message}\n\nPlease ensure Python 3 is installed.`);
  });

  serverProcess.on('exit', (code) => {
    console.log('Server exited with code:', code);
  });
}

// Stop Python server
function stopServer() {
  if (serverProcess) {
    console.log('Stopping server...');
    serverProcess.kill();
    serverProcess = null;
  }
}

// Create main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Agent Notify',
    icon: path.join(__dirname, 'icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    backgroundColor: '#0a0e27', // Match dark theme
    show: false // Don't show until loaded
  });

  mainWindow.loadURL(`http://localhost:${PORT}`);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Handle close - minimize to tray instead
  mainWindow.on('close', (e) => {
    if (!app.isQuitting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Create tray icon
function createTray() {
  const iconPath = path.join(__dirname, 'icon.ico');
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '打开界面',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: '重启服务',
      click: () => {
        stopServer();
        setTimeout(() => startServer(), 1000);
      }
    },
    {
      label: '查看日志',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.webContents.openDevTools();
        }
      }
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        app.isQuitting = true;
        stopServer();
        app.quit();
      }
    }
  ]);

  tray.setToolTip('Agent Notify - Claude/Codex Hook');
  tray.setContextMenu(contextMenu);

  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

// App lifecycle
app.whenReady().then(() => {
  console.log('App ready, starting server...');
  startServer();

  // Wait for server to start before creating window
  setTimeout(() => {
    createWindow();
    createTray();
    console.log('Window and tray created');
  }, 3000);
});

// Don't quit when all windows closed (stay in tray)
app.on('window-all-closed', () => {
  // On macOS, apps usually stay active until user explicitly quits
  if (process.platform !== 'darwin') {
    // Don't quit - stay in tray
  }
});

app.on('before-quit', () => {
  app.isQuitting = true;
  stopServer();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});