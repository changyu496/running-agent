import axios from 'axios';

const TOKEN_KEY = 'buzhi_token';

// API 地址优先级：config.json > REACT_APP_API_URL > 默认 localhost
const DEFAULT_API_URL = 'http://localhost:8000';
let _apiBaseUrl = process.env.REACT_APP_API_URL || DEFAULT_API_URL;

export function setApiBaseUrl(url) {
  _apiBaseUrl = url || DEFAULT_API_URL;
  api.defaults.baseURL = _apiBaseUrl;
}

export const getApiBaseUrl = () => _apiBaseUrl;

/** 是否连接本地后端（localhost / 127.0.0.1） */
export const isLocalMode = () => {
  const url = (_apiBaseUrl || '').toLowerCase();
  return url.includes('localhost') || url.includes('127.0.0.1');
};

export function getToken() {
  return typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
}

export function setToken(token) {
  if (typeof localStorage !== 'undefined') localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (typeof localStorage !== 'undefined') localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn() {
  return !!getToken();
}

/** 带 token 的文件 URL（img src 无法带 header，用 query 传 token） */
export function getFileUrl(pathOrFilename) {
  const base = getApiBaseUrl().replace(/\/$/, '');
  const token = getToken();
  // pathOrFilename 可为 uploads/images/xxx.jpg 或仅 xxx.jpg
  const path = `${base}/api/files/${encodeURIComponent(pathOrFilename)}`;
  return token ? `${path}?token=${encodeURIComponent(token)}` : path;
}

// 从 config.json 加载并设置 API 地址（在 App 启动时调用）
export const loadApiConfig = async () => {
  try {
    const base = typeof window !== 'undefined' && window.location
      ? window.location.href.replace(/\/[^/]*$/, '/')
      : '';
    const res = await fetch(base + 'config.json', { cache: 'no-store' });
    if (res.ok) {
      const cfg = await res.json();
      if (cfg.apiUrl) {
        setApiBaseUrl(cfg.apiUrl);
        return cfg.apiUrl;
      }
    }
  } catch (_) {}
  return _apiBaseUrl;
};

export const API_BASE_URL = _apiBaseUrl;

const api = axios.create({
  baseURL: _apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// 请求拦截：自动附加 JWT
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 响应拦截：401 时清除 token 并触发登出
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      clearToken();
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth:logout'));
      }
    }
    return Promise.reject(err);
  }
);

// 登录
export const login = async (username, password) => {
  const res = await api.post('/api/auth/login', { username, password });
  setToken(res.data.access_token);
  return res.data;
};

// 检查后端是否可用（首次可传更长超时以应对冷启动）
export const checkBackendHealth = async (timeoutMs = 5000) => {
  try {
    const base = getApiBaseUrl();
    const res = await axios.get(`${base}/api/health`, { timeout: timeoutMs });
    return res.data && res.data.status === 'healthy';
  } catch {
    return false;
  }
};

// 备忘录分析
export const analyzeMemo = async (memoText, imageFile) => {
  const formData = new FormData();
  formData.append('memo_text', memoText);
  formData.append('image', imageFile);
  
  const response = await api.post('/api/memo/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000, // 2 分钟超时
  });
  return response.data;
};

export const saveMemoRecord = async (memoText, imagePath, analysisResult, runDate, runType) => {
  const formData = new FormData();
  formData.append('memo_text', memoText);
  formData.append('image_path', imagePath);
  formData.append('analysis_result', JSON.stringify(analysisResult));
  if (runDate) formData.append('run_date', runDate);
  if (runType) formData.append('run_type', runType);
  
  const response = await api.post('/api/memo/save', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// 历史记录
export const getRecords = async (params = {}) => {
  const response = await api.get('/api/records/list', { params });
  return response.data;
};

export const getRecordDetail = async (recordId) => {
  const response = await api.get(`/api/records/${recordId}`);
  return response.data;
};

export const deleteRecord = async (recordId) => {
  const response = await api.delete(`/api/records/${recordId}`);
  return response.data;
};

export const updateRecord = async (recordId, { run_date, run_type }) => {
  const response = await api.patch(`/api/records/${recordId}`, { run_date, run_type });
  return response.data;
};

// 视频分析（姿态检测 + AI 分析耗时长，超时设为 10 分钟）
// onUploadProgress: (percent) => void，上传进度回调，0-100
export const analyzeVideo = async (videoFile, angle, forceFlip180 = false, onUploadProgress) => {
  const formData = new FormData();
  formData.append('video', videoFile);
  formData.append('angle', angle);
  formData.append('force_flip_180', forceFlip180 ? 'true' : 'false');

  const response = await api.post('/api/video/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 600000, // 10 分钟（大视频上传+分析）
    onUploadProgress: onUploadProgress ? (e) => {
      const total = e.total || (videoFile?.size ? videoFile.size * 1.05 : 0);
      const percent = total && e.loaded > 0
        ? Math.min(95, Math.round((e.loaded / total) * 100))
        : (e.loaded > 0 ? Math.min(95, Math.round((e.loaded / (videoFile?.size || 1)) * 100)) : 0);
      onUploadProgress(percent);
    } : undefined,
  });
  return response.data;
};

export const getVideoLogs = async () => {
  const response = await api.get('/api/video/logs');
  return response.data?.logs || [];
};

export const saveVideoRecord = async (videoData) => {
  const formData = new FormData();
  Object.keys(videoData).forEach(key => {
    formData.append(key, videoData[key]);
  });
  
  const response = await api.post('/api/video/save', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// 数据统计
export const getStats = async () => {
  const response = await api.get('/api/stats/overview');
  return response.data;
};

export const getStatsTrends = async (metric = 'heart_rate', days = 30) => {
  const response = await api.get('/api/stats/trends', { params: { metric, days } });
  return response.data;
};

// 智能指导
export const getGuidance = async () => {
  const response = await api.get('/api/guidance/');
  return response.data;
};

// 记录关联
export const linkRecords = async (recordIds) => {
  const response = await api.post('/api/records/link', recordIds, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

export const unlinkRecord = async (recordId) => {
  const response = await api.post(`/api/records/unlink/${recordId}`);
  return response.data;
};

export const autoLinkRecords = async () => {
  const response = await api.post('/api/records/auto-link');
  return response.data;
};
