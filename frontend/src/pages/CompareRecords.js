/**
 * 跑步对比 - 并排展示两条记录
 * 入口：历史记录页勾选 2 条记录 → 点击「对比跑步」
 */
import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getRecordDetail, getFileUrl } from '../services/api';
import { formatPace } from '../utils/format';

const RUN_TYPE_LABELS = {
  recovery: '恢复跑',
  aerobic: '有氧跑',
  long: '长距离',
  pace: '节奏跑',
  interval: '间歇跑',
  other: '其他',
};

const CompareRecords = () => {
  const [searchParams] = useSearchParams();
  const idsParam = searchParams.get('ids') || '';
  const ids = idsParam.split(',').map((s) => parseInt(s.trim(), 10)).filter((n) => !Number.isNaN(n));
  const [records, setRecords] = useState([null, null]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (ids.length !== 2) {
      setError('请选择恰好 2 条记录进行对比');
      setLoading(false);
      return;
    }
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [a, b] = await Promise.all([
          getRecordDetail(ids[0]),
          getRecordDetail(ids[1]),
        ]);
        setRecords([a, b]);
      } catch (e) {
        setError('加载记录失败: ' + (e.response?.data?.detail || e.message));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [ids.join(',')]);

  if (loading) {
    return <div className="text-gray-600">加载中...</div>;
  }
  if (error || ids.length !== 2) {
    return (
      <div>
        <p className="text-red-600 mb-4">{error || '请选择恰好 2 条记录进行对比'}</p>
        <Link to="/records" className="text-primary hover:underline">← 返回历史记录</Link>
      </div>
    );
  }

  const [r1, r2] = records;
  const c1 = r1?.coros_data || {};
  const c2 = r2?.coros_data || {};
  const v1 = r1?.video_analysis || {};
  const v2 = r2?.video_analysis || {};
  const a1 = v1.angles_data || v1.symmetry_data || {};
  const a2 = v2.angles_data || v2.symmetry_data || {};

  const row = (label, val) => (
    <div className="flex justify-between py-2 text-sm border-b border-gray-100">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{val ?? '--'}</span>
    </div>
  );

  const col = (record, coros, videoAnalysis, angles) => (
    <div className="flex-1 min-w-0 p-5 border-r border-gray-200 last:border-r-0">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">
          {record.run_date || new Date(record.created_at).toLocaleDateString('zh-CN')}
          {record.run_type && RUN_TYPE_LABELS[record.run_type] && (
            <span className="ml-2 text-xs font-normal px-2 py-0.5 rounded bg-primary-light text-primary">
              {RUN_TYPE_LABELS[record.run_type]}
            </span>
          )}
        </h3>
        <Link to={`/records/${record.id}`} className="text-xs text-primary hover:underline">查看详情</Link>
      </div>
      <div className="space-y-1">
        {row('距离', coros.distance != null ? `${coros.distance} km` : null)}
        {row('配速', coros.avg_pace ? formatPace(coros.avg_pace) : null)}
        {row('心率', coros.avg_heart_rate != null ? `${coros.avg_heart_rate} bpm` : null)}
        {row('步频', coros.avg_cadence != null ? `${coros.avg_cadence} spm` : null)}
      </div>
      {(videoAnalysis.angles_data || videoAnalysis.symmetry_data) && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">视频分析</div>
          <div className="space-y-1">
            {angles.knee_angle != null && row('膝角', `${angles.knee_angle}°`)}
            {angles.torso_lean != null && row('躯干前倾', `${angles.torso_lean}°`)}
            {angles.ankle_angle != null && row('踝角', `${angles.ankle_angle}°`)}
            {angles.ankle_stability && angles.ankle_stability !== '--' && row('踝稳定性', angles.ankle_stability)}
            {angles.shoulder_balance_angle != null && row('肩膀对称', `${angles.shoulder_balance_angle}°`)}
            {angles.hip_tilt_angle != null && row('骨盆倾斜', `${angles.hip_tilt_angle}°`)}
          </div>
        </div>
      )}
      {record.video_path && (
        <div className="mt-4">
          <div className="text-xs text-gray-500 mb-2">跑步视频</div>
          <video
            src={getFileUrl(record.video_path.split(/[/\\]/).pop())}
            controls
            className="w-full rounded border border-gray-200 object-contain"
            style={{ maxHeight: '180px' }}
          />
        </div>
      )}
      {videoAnalysis.visualization_path && (
        <div className="mt-3">
          <div className="text-xs text-gray-500 mb-2">姿态可视化</div>
          {/\.(mp4|mov|webm)$/i.test(videoAnalysis.visualization_path) ? (
            <video
              src={getFileUrl(videoAnalysis.visualization_path.split(/[/\\]/).pop())}
              controls
              className="w-full rounded border border-gray-200 object-contain"
              style={{ maxHeight: '180px' }}
            />
          ) : (
            <img
              src={getFileUrl(videoAnalysis.visualization_path.split(/[/\\]/).pop())}
              alt="跑姿"
              className="w-full rounded border border-gray-200 object-contain"
              style={{ maxHeight: '180px' }}
            />
          )}
        </div>
      )}
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 tracking-tight">跑步对比</h2>
          <p className="text-gray-500 text-sm mt-1">已选 2 条记录</p>
        </div>
        <Link to="/records" className="text-sm text-primary hover:underline">← 返回历史记录</Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-0 bg-white border border-gray-200 rounded-xl overflow-hidden">
        {col(r1, c1, v1, a1)}
        {col(r2, c2, v2, a2)}
      </div>
    </div>
  );
};

export default CompareRecords;
