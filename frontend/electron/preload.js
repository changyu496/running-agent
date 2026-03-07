const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getIsPackaged: () => ipcRenderer.invoke('get-is-packaged'),
  getLogPath: () => ipcRenderer.invoke('get-log-path'),
  openLog: () => ipcRenderer.invoke('open-log'),
});
