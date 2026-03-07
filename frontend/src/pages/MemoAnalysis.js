import React, { useState, useEffect } from 'react';
import { analyzeMemo, saveMemoRecord, checkBackendHealth } from '../services/api';
import AnalysisResultDisplay from '../components/AnalysisResultDisplay';

const RUN_TYPE_OPTIONS = [
  { value: '', label: '系统自动识别' },
  { value: 'recovery', label: '恢复跑' },
  { value: 'aerobic', label: '有氧跑' },
  { value: 'long', label: '长距离' },
  { value: 'pace', label: '节奏跑' },
  { value: 'interval', label: '间歇跑' },
  { value: 'other', label: '其他' },
];

const MemoAnalysis = () => {
  const [memoText, setMemoText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);
  const [backendOk, setBackendOk] = useState(null);
  const [logPath, setLogPath] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [runDate, setRunDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [runType, setRunType] = useState('');

  useEffect(() => {
    let isPackaged = false;
    (async () => {
      try {
        isPackaged = await (window.electronAPI?.getIsPackaged?.() ?? Promise.resolve(false));
      } catch {}
      const retries = isPackaged ? 30 : 3;
      const intervalMs = isPackaged ? 1000 : 2000;
      for (let i = 0; i < retries; i++) {
        const ok = await checkBackendHealth();
        if (ok) {
          setBackendOk(true);
          break;
        }
        if (i < retries - 1) await new Promise((r) => setTimeout(r, intervalMs));
        else {
          setBackendOk(false);
          try {
            const p = await window.electronAPI?.getLogPath?.();
            if (p) setLogPath(p);
          } catch {}
        }
      }
    })();
    const t = setInterval(() => checkBackendHealth().then(setBackendOk), 10000);
    return () => clearInterval(t);
  }, []);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = async () => {
    if (!imageFile) {
      alert('请先上传高驰截图');
      return;
    }
    if (backendOk === false) {
      const msg = window.electronAPI
        ? '后端服务未启动，请尝试重启应用。'
        : '后端服务未启动或不可用。请确认已运行启动脚本（如 ./start.sh），或先启动后端：cd backend && python3 main.py';
      alert(msg);
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await analyzeMemo(memoText, imageFile);
      setResult(response);
      setSaved(false);
    } catch (error) {
      console.error('分析失败:', error);
      const detail = error.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (detail ? JSON.stringify(detail) : error.message);
      const hint = error.code === 'ECONNREFUSED' || (error.message && error.message.includes('Network'))
        ? (window.electronAPI ? '后端未连接，请尝试重启应用。' : '请确认后端已启动（运行 ./start.sh 或先执行 cd backend && python3 main.py）')
        : msg;
      setErrorMessage(hint);
      alert('分析失败: ' + hint);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!result) return;

    setLoading(true);
    try {
      // 构建完整的分析结果
      const fullResult = {
        data_overview: result.data_overview || {},
        performance_evaluation: result.performance_evaluation || {},
        improvement_suggestions: result.improvement_suggestions || []
      };
      
      // 图片路径从分析结果中获取，如果没有则使用文件名
      const imagePath = result.image_path || imageFile.name;
      
      await saveMemoRecord(memoText, imagePath, fullResult, runDate || undefined, runType || undefined);
      setSaved(true);
      alert('保存成功！');
    } catch (error) {
      console.error('保存失败:', error);
      alert('保存失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2 tracking-tight">新建分析</h2>
      <p className="text-gray-500 mb-7 text-sm">输入备忘录并上传高驰截图，获得 AI 分析</p>

      {/* 后端状态提示 */}
      {backendOk === null && (
        <div className="mb-4 text-sm text-gray-500">
          {window.electronAPI ? '正在启动后端，请稍候...' : '正在检查后端连接...'}
        </div>
      )}
      {backendOk === false && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 text-sm">
          <strong>后端未连接</strong>：
          {window.electronAPI
            ? ' 请尝试重启应用。若仍无法连接，请确保已从 DMG 正确安装到「应用程序」文件夹。'
            : ' 请先运行项目根目录下的 '}
          {!window.electronAPI && (
            <>
              <code className="bg-red-100 px-1">./start.sh</code> 启动全部服务，或单独在 backend 目录执行 <code className="bg-red-100 px-1">python3 main.py</code>。
            </>
          )}
          {logPath && (
            <div className="mt-3 pt-3 border-t border-red-200">
              诊断日志：<code className="bg-red-100 px-1 text-xs break-all">{logPath}</code>
              <br />
              <button
                type="button"
                onClick={() => window.electronAPI?.openLog?.()}
                className="mt-2 text-xs underline text-red-700 hover:text-red-900"
              >
                打开日志文件
              </button>
            </div>
          )}
        </div>
      )}
      {backendOk === true && (
        <div className="mb-4 text-sm text-green-600">✓ 后端服务已连接</div>
      )}
      {errorMessage && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 text-amber-800 text-sm">
          {errorMessage}
        </div>
      )}

      {/* 跑步日期、训练类型（置顶，滚动时吸顶可见） */}
      <div className="mb-8 sticky top-0 z-10 bg-[#fafbfc] pb-4 mb-4 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">1. 跑步信息（可选）</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">跑步日期</label>
            <input
              type="date"
              value={runDate}
              onChange={(e) => setRunDate(e.target.value)}
              className="w-full p-3 border border-gray-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">训练类型</label>
            <select
              value={runType}
              onChange={(e) => setRunType(e.target.value)}
              className="w-full p-3 border border-gray-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              {RUN_TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <div className="text-xs text-gray-500 mt-1">不选择则系统根据数据自动识别</div>
          </div>
        </div>
      </div>

      {/* 输入区域 */}
      <div className="mb-8">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">2. 输入备忘录内容</h3>
        <textarea
          className="w-full min-h-[200px] p-5 border border-gray-200 rounded-xl bg-white text-sm text-gray-900 leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="记录你的跑步感受、配速、心率、体感等信息…"
          value={memoText}
          onChange={(e) => setMemoText(e.target.value)}
        />
      </div>

      {/* 图片上传 */}
      <div className="mb-8">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">3. 上传高驰数据截图</h3>
        <div
          className="border-2 border-dashed border-gray-200 rounded-xl p-12 text-center bg-white cursor-pointer hover:border-primary hover:bg-primary-light transition-all"
          onClick={() => document.getElementById('image-upload').click()}
        >
          {imagePreview ? (
            <img src={imagePreview} alt="预览" className="max-w-full max-h-64 mx-auto rounded-lg" />
          ) : (
            <>
              <div className="text-5xl mb-3 opacity-60">📷</div>
              <div className="text-gray-500 text-sm font-medium">点击或拖拽上传</div>
              <div className="text-xs text-gray-400 mt-2">支持 PNG、JPG 格式</div>
            </>
          )}
        </div>
        <input
          id="image-upload"
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleImageChange}
        />
        <div className="mt-4 p-4 bg-primary-light border-l-4 border-primary rounded-r-lg text-sm text-gray-600">
          提示：上传高驰 App 完整数据截图，AI 将自动识别配速、心率、步频等关键数据
        </div>
      </div>

      {/* 分析按钮 */}
      <div className="text-center mb-8">
        <button
          onClick={handleAnalyze}
          disabled={loading || !imageFile}
          className="px-10 py-3.5 bg-primary text-white text-sm font-semibold rounded-xl hover:bg-primary-hover transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {loading ? '分析中...' : '开始分析'}
        </button>
      </div>

      {/* 分析结果 */}
      {result && result.success && (
        <div className="mt-8">
          <h3 className="text-base font-semibold text-gray-900 mb-4">AI分析结果</h3>
          <AnalysisResultDisplay
            analysis={{
              data_overview: result.data_overview || {},
              performance_evaluation: result.performance_evaluation || {},
              improvement_suggestions: result.improvement_suggestions || [],
            }}
            runDate={runDate}
            runType={runType}
            runScore={result.run_score}
          />

          {/* 保存按钮 */}
          <div className="text-center mt-8 pt-6 border-t border-gray-100">
            <button
              onClick={handleSave}
              disabled={loading || saved}
              className="px-10 py-3.5 bg-primary text-white text-sm font-semibold rounded-xl hover:bg-primary-hover transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {saved ? '已保存' : '保存记录'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoAnalysis;
