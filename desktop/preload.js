// Preload script - provides secure bridge between renderer and main process
// Currently no IPC methods needed since we're just loading the web UI

// In the future, you could add methods like:
// contextBridge.exposeInMainWorld('electronAPI', {
//   minimize: () => ipcRenderer.send('minimize'),
//   maximize: () => ipcRenderer.send('maximize'),
//   close: () => ipcRenderer.send('close')
// })

// For now, this file exists to satisfy contextIsolation requirement
// No methods exposed - web UI runs independently