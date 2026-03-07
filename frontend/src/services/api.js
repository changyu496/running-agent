import axios from 'axios';

// API 地址优先级：config.json > REACT_APP_API_URL > 默认 localhost
const DEFAULT_API_URL = 'http://localhost:8000';
let _apiBaseUrl = process.env.REACT_APP_API_URL || DEFAULT_API_URL;

export function setApiBaseUrl(url) {
  _apiBaseUrl = url || DEFAULT_API_URL;
  api.defaults.baseURL = _apiBaseUrl;
}

export const getApiBaseUrl = () => _apiBaseUrl;

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

// 视频分析（姿态检测 + AI 分析耗时长，超时设为 5 分钟）
export const analyzeVideo = async (videoFile, angle, forceFlip180 = false) => {
  const formData = new FormData();
  formData.append('video', videoFile);
  formData.append('angle', angle);
  formData.append('force_flip_180', forceFlip180 ? 'true' : 'false');

  const response = await api.post('/api/video/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 300000, // 5 分钟
  });
  return response.data;
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
