const { app, BrowserWindow, Tray, Menu, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

let mainWindow = null;
let tray = null;
let serverProcess = null;
let autoOpenPollInterval = null;
let flagFileWatcher = null;
const PORT = 18865;
const POLL_INTERVAL = 5000; // 每5秒检查一次新数据（作为备用）
const FLAG_FILE = path.join(path.dirname(__dirname), 'state', 'new_event.flag');
let lastEventCount = 0;

// Check if server is already running
function checkServerRunning() {
  return new Promise((resolve) => {
    const req = http.request({
      hostname: 'localhost',
      port: PORT,
      path: '/api/stats',
      method: 'GET',
      timeout: 2000
    }, (res) => {
      resolve(true);
    });

    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

// Check for new events and auto-open window
async function checkNewEvents() {
  try {
    const stats = await fetchStats();
    if (stats && stats.total_events > lastEventCount) {
      console.log(`New events detected: ${stats.total_events} (was ${lastEventCount})`);
      lastEventCount = stats.total_events;
      showAndRefreshWindow();
    }
  } catch (error) {
    console.error('Error checking events:', error);
  }
}

// Fetch stats from API
function fetchStats() {
  return new Promise((resolve, reject) => {
    http.get(`http://localhost:${PORT}/api/stats`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

// Show window and refresh data - force to foreground
function showAndRefreshWindow() {
  if (mainWindow) {
    // Restore if minimized
    if (mainWindow.isMinimized()) {
      mainWindow.restore();
    }

    // Show the window
    mainWindow.show();

    // Force window to foreground (Windows specific tricks)
    // Temporarily set always on top to bring window to front
    mainWindow.setAlwaysOnTop(true, 'floating');

    // Focus the window
    mainWindow.focus();

    // Flash the frame to attract attention (optional)
    mainWindow.flashFrame(true);

    // Reset always on top after a short delay
    setTimeout(() => {
      mainWindow.setAlwaysOnTop(false);
      mainWindow.flashFrame(false);
    }, 100);

    // Move to top of window stack
    mainWindow.moveTop();

    // Refresh the page after window is visible
    setTimeout(() => {
      mainWindow.reload();
      console.log('Window shown, focused, and refreshed');
    }, 200);
  }
}

// Watch for notification flag file (immediate notification)
function startFlagFileWatcher() {
  // Check if flag file exists initially
  if (fs.existsSync(FLAG_FILE)) {
    const flagContent = fs.readFileSync(FLAG_FILE, 'utf8');
    console.log('Flag file found:', flagContent);
    showAndRefreshWindow();
    // Delete the flag file after handling
    try {
      fs.unlinkSync(FLAG_FILE);
    } catch (e) {
      console.error('Error deleting flag file:', e);
    }
  }

  // Watch the state directory for file changes
  const stateDir = path.dirname(FLAG_FILE);
  if (fs.existsSync(stateDir)) {
    try {
      flagFileWatcher = fs.watch(stateDir, (eventType, filename) => {
        if (filename === 'new_event.flag' && eventType === 'rename') {
          // File was created or renamed
          setTimeout(() => {
            if (fs.existsSync(FLAG_FILE)) {
              const flagContent = fs.readFileSync(FLAG_FILE, 'utf8');
              console.log('New event detected via flag file:', flagContent);
              showAndRefreshWindow();
              // Delete the flag file
              try {
                fs.unlinkSync(FLAG_FILE);
              } catch (e) {
                console.error('Error deleting flag file:', e);
              }
            }
          }, 100); // Small delay to ensure file is fully written
        }
      });
      console.log('Flag file watcher started on:', stateDir);
    } catch (e) {
      console.error('Failed to start file watcher:', e);
      // Fallback to polling only
    }
  } else {
    console.log('State directory not found, using polling only');
  }
}

// Stop flag file watcher
function stopFlagFileWatcher() {
  if (flagFileWatcher) {
    flagFileWatcher.close();
    flagFileWatcher = null;
    console.log('Flag file watcher stopped');
  }
}
function startAutoOpenPolling() {
  // Initial fetch to get current count
  fetchStats().then(stats => {
    if (stats) {
      lastEventCount = stats.total_events;
      console.log(`Initial event count: ${lastEventCount}`);
    }
  }).catch(console.error);

  // Start polling interval
  autoOpenPollInterval = setInterval(checkNewEvents, POLL_INTERVAL);
  console.log('Auto-open polling started');
}

// Stop polling
function stopAutoOpenPolling() {
  if (autoOpenPollInterval) {
    clearInterval(autoOpenPollInterval);
    autoOpenPollInterval = null;
    console.log('Auto-open polling stopped');
  }
}
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

// Start Python server (only if not already running)
async function startServer() {
  // Check if server is already running
  const isRunning = await checkServerRunning();

  if (isRunning) {
    console.log('Server already running on port', PORT, '- skipping startup');
    return;
  }

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
    show: false, // Don't show until loaded
    focusable: true, // Ensure window can be focused
    skipTaskbar: false, // Show in taskbar
  });

  mainWindow.loadURL(`http://localhost:${PORT}`);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
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

  // Ensure window can be brought to front when hidden and shown again
  mainWindow.on('show', () => {
    mainWindow.focus();
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
        showAndRefreshWindow(); // 使用统一的显示方法
      }
    },
    {
      label: '强制前台显示',
      click: () => {
        if (mainWindow) {
          // 最强力的前台显示方法
          mainWindow.restore();
          mainWindow.show();
          mainWindow.setAlwaysOnTop(true, 'screen-saver'); // 最高优先级
          mainWindow.focus();
          mainWindow.flashFrame(true);

          setTimeout(() => {
            mainWindow.setAlwaysOnTop(false);
            mainWindow.flashFrame(false);
          }, 1000);
        }
      }
    },
    {
      label: '刷新数据',
      click: () => {
        if (mainWindow) {
          mainWindow.reload();
          console.log('Data refreshed manually');
        }
      }
    },
    {
      label: '重启服务',
      click: async () => {
        stopFlagFileWatcher();
        stopAutoOpenPolling();
        stopServer();
        setTimeout(async () => {
          await startServer();
          setTimeout(() => {
            startFlagFileWatcher();
            startAutoOpenPolling();
          }, 2000);
        }, 1000);
      }
    },
    {
      label: '查看日志',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
          mainWindow.webContents.openDevTools();
        }
      }
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        app.isQuitting = true;
        stopFlagFileWatcher();
        stopAutoOpenPolling();
        stopServer();
        app.quit();
      }
    }
  ]);

  tray.setToolTip('Agent Notify - Claude/Codex Hook');
  tray.setContextMenu(contextMenu);

  tray.on('double-click', () => {
    showAndRefreshWindow(); // 使用统一的显示方法
  });
}

// App lifecycle
app.whenReady().then(async () => {
  console.log('App ready, checking server...');
  await startServer();

  // Wait for server to be ready before creating window
  setTimeout(async () => {
    createWindow();
    createTray();
    startFlagFileWatcher(); // Watch for immediate notifications
    startAutoOpenPolling(); // Backup polling mechanism
    console.log('Window, tray, flag watcher, and polling started');

    // Fetch initial stats
    try {
      const stats = await fetchStats();
      if (stats) {
        lastEventCount = stats.total_events;
        console.log('Initial stats:', stats);
      }
    } catch (e) {
      console.log('Stats fetch failed (server might still be starting)');
    }
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
  stopFlagFileWatcher();
  stopAutoOpenPolling();
  stopServer();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});