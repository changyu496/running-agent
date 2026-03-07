const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');
const os = require('os');

let mainWindow;
let pythonProcess;
let logPath = null;

function getLogPath() {
  if (logPath) return logPath;
  const dir = path.join(os.homedir(), 'Library', 'Application Support', '步知');
  try {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    logPath = path.join(dir, 'backend.log');
  } catch (e) {
    logPath = path.join(os.tmpdir(), 'running-agent-backend.log');
  }
  return logPath;
}

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  try {
    fs.appendFileSync(getLogPath(), line);
  } catch {}
  console.log(msg);
}

function getBackendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend');
  }
  return path.join(__dirname, '../../backend');
}

function getBackendExecutable() {
  const backendDir = getBackendPath();
  const exe = path.join(backendDir, 'running-agent-backend');
  return exe;
}

function checkBackendHealth() {
  return new Promise((resolve) => {
    const req = http.get('http://127.0.0.1:8000/api/health', { timeout: 2000 }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json && json.status === 'healthy');
        } catch {
          resolve(false);
        }
      });
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    title: '步知',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false, // 开发时允许加载 localhost
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // 开发环境：没有 build 时加载本地开发服务器，否则加载打包文件
  const pathToBuild = path.join(__dirname, '../build/index.html');
  if (fs.existsSync(pathToBuild)) {
    mainWindow.loadFile(pathToBuild);
  } else {
    const devUrl = 'http://localhost:3000';
    mainWindow.loadURL(devUrl).catch((err) => {
      console.error('加载失败:', err);
    });
    mainWindow.webContents.openDevTools();

    // 加载失败时显示提示
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, url) => {
      if (url === devUrl || url.startsWith(devUrl)) {
        mainWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(`
          <!DOCTYPE html><html><head><meta charset="utf-8"><title>步知</title></head>
          <body style="font-family:system-ui;padding:40px;max-width:500px;">
            <h2>无法连接前端</h2>
            <p>请确保 React 开发服务器已启动：</p>
            <pre style="background:#f0f0f0;padding:12px;border-radius:6px;">cd frontend && npm run dev:react</pre>
            <p>等待编译完成后，<a href="${devUrl}">点击此处重试</a> 或刷新窗口。</p>
          </body></html>
        `));
      }
    });
  }

  mainWindow.once('ready-to-show', () => mainWindow.show());
}

function setupIpc() {
  ipcMain.handle('get-is-packaged', () => app.isPackaged);
  ipcMain.handle('get-log-path', () => getLogPath());
  ipcMain.handle('open-log', () => {
    const p = getLogPath();
    if (fs.existsSync(p)) shell.openPath(p);
  });
}

function startPythonBackend() {
  const backendDir = getBackendPath();
  const exePath = getBackendExecutable();

  if (app.isPackaged) {
    log(`resourcesPath: ${process.resourcesPath}`);
    log(`backend: ${exePath}`);
    log(`exists: ${fs.existsSync(exePath)}`);

    if (!fs.existsSync(exePath)) {
      log('ERROR: 后端可执行文件不存在');
      return;
    }
    try {
      fs.chmodSync(exePath, 0o755);
    } catch (e) {
      log(`chmod warn: ${e.message}`);
    }
    // 移除 quarantine 属性，避免 Gatekeeper 拦截未签名二进制
    try {
      const { execSync } = require('child_process');
      execSync(`xattr -cr "${path.dirname(exePath)}"`, { stdio: 'ignore' });
    } catch (e) {
      log(`xattr warn: ${e.message}`);
    }
    const cwd = path.dirname(exePath);
    log(`spawning cwd=${cwd}`);
    pythonProcess = spawn(exePath, [], {
      cwd,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PATH: process.env.PATH || '/usr/local/bin:/usr/bin:/bin' }
    });
  } else {
    const pythonPath = process.platform === 'darwin' ? 'python3' : 'python';
    const backendPath = path.join(backendDir, 'main.py');
    if (!fs.existsSync(backendPath)) {
      console.error('后端 main.py 不存在:', backendPath);
      return;
    }
    pythonProcess = spawn(pythonPath, [backendPath], {
      cwd: backendDir,
      stdio: ['ignore', 'pipe', 'pipe']
    });
  }

  pythonProcess.stdout.on('data', (data) => {
    const s = data.toString();
    log(`[Backend] ${s}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    const s = data.toString();
    log(`[Backend stderr] ${s}`);
  });

  pythonProcess.on('error', (err) => {
    log(`ERROR: 启动后端失败 ${err.message}`);
  });

  pythonProcess.on('exit', (code, signal) => {
    if (code != null && code !== 0) {
      log(`[Backend] 进程退出 code=${code} signal=${signal}`);
    }
  });
}

// 轮询等待后端就绪，最多等待 45 秒（matplotlib 字体缓存等可能较慢）
async function waitForBackendReady() {
  for (let i = 0; i < 90; i++) {
    if (await checkBackendHealth()) return true;
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

app.whenReady().then(async () => {
  setupIpc();
  if (process.env.SKIP_BACKEND_START !== '1') {
    startPythonBackend();
    const ready = await waitForBackendReady();
    if (app.isPackaged) log(ready ? '后端就绪' : '后端未就绪（超时）');
  }
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
