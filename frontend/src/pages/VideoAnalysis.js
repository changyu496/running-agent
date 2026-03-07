/**
 * 视频跑姿分析 - 三栏布局（上传 | 可视化 | 指标）+ 分析内容
 * 参考原型：ui-prototype.html 页面3
 */
import React, { useState, useEffect } from 'react';
import { analyzeVideo, saveVideoRecord, getRecords, getFileUrl } from '../services/api';
import VideoAnalysisTextDisplay from '../components/VideoAnalysisTextDisplay';

const RUN_TYPE_LABELS = {
  recovery: '恢复跑',
  aerobic: '有氧跑',
  long: '长距离',
  pace: '节奏跑',
  interval: '间歇跑',
  other: '其他',
};

const VideoAnalysis = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [angle, setAngle] = useState('side');
  const [forceFlip180, setForceFlip180] = useState(false);
  const [pace, setPace] = useState('');
  const [feel, setFeel] = useState('normal');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);
  const [memoRecords, setMemoRecords] = useState([]);
  const [selectedRecordId, setSelectedRecordId] = useState('');

  useEffect(() => {
    getRecords({ limit: 100 }).then((list) => {
      setMemoRecords(list.filter((r) => r.record_type === 'memo' || r.record_type === 'both'));
    }).catch(() => setMemoRecords([]));
  }, []);

  const handleVideoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setVideoPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = async () => {
    if (!videoFile) {
      alert('请先上传跑步视频');
      return;
    }
    setLoading(true);
    try {
      const response = await analyzeVideo(videoFile, angle, forceFlip180);
      setResult(response);
      setSaved(false);
    } catch (error) {
      console.error('分析失败:', error);
      const msg = error.response?.data?.detail || error.message;
      const hint = msg.includes('timeout') || msg.includes('exceeded')
        ? '分析超时。视频分析需 1–3 分钟，请使用 10–30 秒的短视频重试。'
        : msg;
      alert('分析失败: ' + hint);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!result) return;
    if (!selectedRecordId) {
      alert('请先选择要关联的跑步记录');
      return;
    }
    setLoading(true);
    try {
      await saveVideoRecord({
        record_id: selectedRecordId,
        video_path: result.video_path,
        video_angle: result.video_angle,
        keypoints_data: result.keypoints_data,
        angles_data: result.angles_data,
        symmetry_data: result.symmetry_data || '',
        visualization_path: result.visualization_path,
        overall_score: result.overall_score,
        analysis_text: result.analysis_text || ''
      });
      setSaved(true);
      alert('保存成功！已关联到所选跑步记录');
    } catch (error) {
      console.error('保存失败:', error);
      alert('保存失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const angles = result?.angles_data ? (() => {
    try {
      return typeof result.angles_data === 'string' ? JSON.parse(result.angles_data) : result.angles_data;
    } catch { return {}; }
  })() : {};
  const symmetry = result?.symmetry_data ? (() => {
    try {
      return typeof result.symmetry_data === 'string' ? JSON.parse(result.symmetry_data) : result.symmetry_data;
    } catch { return {}; }
  })() : {};

  const visFilename = result?.visualization_path ? result.visualization_path.split(/[/\\]/).pop() : null;
  const visUrl = visFilename ? getFileUrl(visFilename) : null;
  const isVisVideo = visFilename && /\.(mp4|mov|webm)$/i.test(visFilename);
  const [visLoadError, setVisLoadError] = useState(false);

  useEffect(() => {
    if (result) setVisLoadError(false);
  }, [result]);

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">视频跑姿分析</h2>
      <p className="text-gray-600 mb-6 text-sm">
        MediaPipe PoseLandmarker（33 关键点）→ PoseAnalyzer（PoseMetrics + PoseScore）→ PoseVisualizer（骨架 + 角度）
      </p>

      {/* 三栏布局 */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 min-h-[500px]">
        {/* 左栏：上传 + 信息 */}
        <div className="md:col-span-3 bg-gray-50 border border-gray-200 rounded-lg p-5">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">上传</div>
          <div
            className="border border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer bg-white hover:border-gray-900 hover:bg-gray-50 transition-colors"
            onClick={() => document.getElementById('video-upload').click()}
          >
            {videoPreview ? (
              <video src={videoPreview} controls className="max-w-full max-h-32 object-contain mx-auto" />
            ) : (
              <>
                <div className="text-3xl mb-2">🎬</div>
                <div className="text-sm text-gray-600">点击或拖拽上传</div>
                <div className="text-xs text-gray-500 mt-1">MP4 / MOV</div>
              </>
            )}
          </div>
          <input id="video-upload" type="file" accept="video/*" className="hidden" onChange={handleVideoChange} />

          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-5 mb-3">信息</div>
          <input
            type="text"
            placeholder="配速（可选）"
            value={pace}
            onChange={(e) => setPace(e.target.value)}
            className="w-full px-3 py-2 bg-white border border-gray-200 rounded text-sm text-gray-900 mb-2"
          />
          <select
            value={feel}
            onChange={(e) => setFeel(e.target.value)}
            className="w-full px-3 py-2 bg-white border border-gray-200 rounded text-sm text-gray-900 mb-2"
          >
            <option value="easy">体感：轻松</option>
            <option value="normal">体感：正常</option>
            <option value="tired">体感：疲劳</option>
          </select>
          <div className="flex gap-3 text-sm text-gray-600 mb-4">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="radio" name="angle" value="side" checked={angle === 'side'} onChange={(e) => setAngle(e.target.value)} />
              侧面
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="radio" name="angle" value="back" checked={angle === 'back'} onChange={(e) => setAngle(e.target.value)} />
              背面
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-amber-700 cursor-pointer mb-4">
            <input type="checkbox" checked={forceFlip180} onChange={(e) => setForceFlip180(e.target.checked)} />
            <span>画面倒置时勾选（旋转 180°）</span>
          </label>
          <div className="text-center">
            <button
              onClick={handleAnalyze}
              disabled={loading || !videoFile}
              className="w-full py-2.5 px-4 bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed rounded transition-colors"
            >
              {loading ? '分析中（约 1–3 分钟）...' : '开始分析'}
            </button>
            <button
              onClick={handleSave}
              disabled={!result || saved || !selectedRecordId}
              className="w-full mt-3 py-2 px-4 bg-transparent border border-gray-200 text-gray-600 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed rounded transition-colors"
            >
              {saved ? '已保存' : '保存记录'}
            </button>
          </div>
        </div>

        {/* 中栏：可视化 */}
        <div className="md:col-span-6 bg-gray-50 border border-gray-200 rounded-lg p-5">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">分析结果</div>
          <div className="bg-gray-100 border border-gray-200 rounded-lg min-h-[360px] flex items-center justify-center overflow-hidden">
            {result && (visUrl || videoPreview) ? (
              <div className="relative w-full max-h-[400px] flex flex-col items-center">
                {isVisVideo && visUrl && !visLoadError ? (
                  <video
                    src={visUrl}
                    controls
                    className="max-w-full object-contain"
                    style={{ maxHeight: '400px' }}
                    onError={() => setVisLoadError(true)}
                  />
                ) : isVisVideo && visUrl && visLoadError ? (
                  <div className="p-6 text-center bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="text-amber-700 font-medium mb-2">可视化视频加载失败</div>
                    <div className="text-sm text-amber-600 mb-3">视频格式可能不被浏览器支持，请尝试用原视频预览</div>
                    <video src={videoPreview} controls className="max-w-full max-h-64 object-contain" />
                  </div>
                ) : visUrl ? (
                  <img
                    src={visUrl}
                    alt="跑姿骨架"
                    className="max-w-full object-contain border border-gray-200 rounded"
                    style={{ maxHeight: '400px' }}
                    onError={(e) => { e.target.onerror = null; e.target.src = videoPreview || ''; }}
                  />
                ) : (
                  <video
                    src={videoPreview}
                    controls
                    className="max-w-full object-contain"
                    style={{ maxHeight: '360px' }}
                  />
                )}
              </div>
            ) : (
              <div className="text-center p-8 text-gray-500 text-sm">
                <div className="text-4xl mb-3">🏃</div>
                <div>视频播放时，骨架线 + 角度弧实时跟随运动</div>
                <div className="text-xs mt-2 text-gray-400">类似 Ochy · MediaPipe 33 关键点</div>
              </div>
            )}
          </div>
          {result && (
            <div className="mt-4 p-3 bg-gray-100 border border-gray-200 rounded text-xs text-gray-600">
              拍摄角度：<strong className="text-gray-900">{angle === 'side' ? '侧面' : '背面'}</strong>
              {' | '}
              分析重点：{angle === 'side' ? '步态、角度、落地方式' : '对称性、对齐度'}
            </div>
          )}
        </div>

        {/* 右栏：指标 */}
        <div className="md:col-span-3 bg-gray-50 border border-gray-200 rounded-lg p-5">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">指标</div>
          {result ? (
            <>
              <div className="bg-gray-200 border border-gray-200 rounded-xl p-5 text-center mb-4">
                <div className="text-3xl font-bold text-gray-900">{result.overall_score ?? '--'}</div>
                <div className="text-xs text-gray-600 mt-1">综合评分</div>
              </div>
              {angle === 'side' ? (
                <div className="space-y-3">
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">躯干前倾</span>
                      <span className="text-lg font-bold text-gray-900">{angles.torso_lean ?? '--'}°</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">理想范围 8-15°</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">膝关节角度</span>
                      <span className="text-lg font-bold text-gray-900">{angles.knee_angle ?? '--'}°</span>
                    </div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">踝关节角度</span>
                      <span className="text-lg font-bold text-gray-900">{angles.ankle_angle ?? '--'}°</span>
                    </div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">头部倾斜</span>
                      <span className="text-lg font-bold text-gray-900">{angles.head_tilt ?? '--'}°</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">左右平衡</span>
                      <span className="text-lg font-bold text-gray-900">{symmetry.shoulder_balance ?? '--'}</span>
                    </div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">骨盆倾斜</span>
                      <span className="text-lg font-bold text-gray-900">{symmetry.hip_tilt_angle ?? '--'}°</span>
                    </div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">肩膀对称</span>
                      <span className="text-lg font-bold text-gray-900">{symmetry.shoulder_balance_angle ?? '--'}°</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center text-gray-400 text-sm py-8">上传视频并分析后显示指标</div>
          )}
        </div>
      </div>

      {/* 分析内容：对称性评估 + 对齐度分析（完整保留） */}
      {result?.analysis_text && (
        <div className="mt-6">
          <VideoAnalysisTextDisplay analysisText={result.analysis_text} />
        </div>
      )}

      {/* 关联记录选择（分析完成后显示） */}
      {result && (
        <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="text-sm font-semibold text-gray-900 mb-2">选择关联的跑步记录（保存前必选）</div>
          <select
            value={selectedRecordId}
            onChange={(e) => setSelectedRecordId(e.target.value)}
            className="w-full max-w-md p-2 border border-gray-300 rounded text-sm bg-white"
          >
            <option value="">请选择要关联的跑步记录</option>
            {memoRecords.map((r) => (
              <option key={r.id} value={r.id}>
                {r.run_date || new Date(r.created_at).toLocaleDateString('zh-CN')} · {r.distance ? `${r.distance} km` : '备忘录'} · {RUN_TYPE_LABELS[r.run_type] || r.record_type}
              </option>
            ))}
          </select>
          {memoRecords.length === 0 && (
            <div className="text-xs text-amber-700 mt-2">暂无跑步记录，请先在「备忘录分析」中保存一条记录</div>
          )}
        </div>
      )}
    </div>
  );
};

export default VideoAnalysis;
