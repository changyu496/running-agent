import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getRecords, autoLinkRecords, linkRecords } from '../services/api';
import { formatPace } from '../utils/format';

const RUN_TYPE_LABELS = {
  recovery: '恢复跑',
  aerobic: '有氧跑',
  long: '长距离',
  pace: '节奏跑',
  interval: '间歇跑',
  other: '其他',
};

const Records = () => {
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recordType, setRecordType] = useState('');
  const [search, setSearch] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [linking, setLinking] = useState(false);

  useEffect(() => {
    loadRecords();
  }, [recordType, search]);

  const loadRecords = async () => {
    try {
      const params = {};
      if (recordType) params.record_type = recordType;
      if (search) params.search = search;
      
      const data = await getRecords(params);
      setRecords(data);
    } catch (error) {
      console.error('加载记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoLink = async () => {
    try {
      await autoLinkRecords();
      alert('自动关联完成！');
      loadRecords();
    } catch (error) {
      console.error('自动关联失败:', error);
      alert('自动关联失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleManualLink = async () => {
    const ids = Array.from(selectedIds);
    if (ids.length < 2) {
      alert('请至少选择 2 条记录进行关联');
      return;
    }
    setLinking(true);
    try {
      await linkRecords(ids);
      alert('关联成功！');
      setSelectedIds(new Set());
      loadRecords();
    } catch (error) {
      console.error('关联失败:', error);
      alert('关联失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLinking(false);
    }
  };

  if (loading) {
    return <div className="text-gray-600">加载中...</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2 tracking-tight">历史记录</h2>
      <p className="text-gray-500 mb-7 text-sm">查看和管理你的跑步记录</p>

      {/* 搜索和筛选 */}
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          placeholder="搜索记录…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        />
        <select
          value={recordType}
          onChange={(e) => setRecordType(e.target.value)}
          className="px-4 py-3 border border-gray-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary min-w-[140px]"
        >
          <option value="">全部类型</option>
          <option value="memo">备忘录分析</option>
          <option value="video">视频分析</option>
        </select>
        <button
          onClick={handleAutoLink}
          className="px-5 py-3 bg-primary text-white text-sm font-medium rounded-xl hover:bg-primary-hover transition-colors"
        >
          自动关联
        </button>
        {selectedIds.size >= 2 && (
          <button
            onClick={handleManualLink}
            disabled={linking}
            className="px-5 py-3 bg-primary text-white text-sm font-medium rounded-xl hover:bg-primary-hover disabled:opacity-50 transition-colors"
          >
            {linking ? '关联中...' : `关联所选 (${selectedIds.size})`}
          </button>
        )}
        {selectedIds.size === 2 && (
          <button
            onClick={() => navigate(`/records/compare?ids=${Array.from(selectedIds).join(',')}`)}
            className="px-5 py-3 bg-green-600 text-white text-sm font-medium rounded-xl hover:bg-green-700 transition-colors"
          >
            对比跑步
          </button>
        )}
      </div>

      <div className="space-y-3">
        {records.length === 0 ? (
          <div className="bg-white p-6 border border-gray-100 rounded-xl text-center text-gray-500 shadow-sm">
            暂无记录
          </div>
        ) : (
          records.map((record) => (
            <div
              key={record.id}
              className={`flex items-start gap-3 bg-white p-5 border rounded-xl transition-all shadow-sm ${
                selectedIds.has(record.id) ? 'border-primary bg-primary-light' : 'border-gray-100 hover:border-primary hover:shadow'
              }`}
            >
              <input
                type="checkbox"
                checked={selectedIds.has(record.id)}
                onChange={() => toggleSelect(record.id)}
                onClick={(e) => e.stopPropagation()}
                className="mt-1"
              />
              <Link
                to={`/records/${record.id}`}
                className="flex-1 min-w-0"
              >
              <div className="text-xs text-gray-600 mb-2">
                {record.run_date || new Date(record.created_at).toLocaleDateString('zh-CN')}
                {record.run_type && RUN_TYPE_LABELS[record.run_type] && (
                  <span className="ml-2 text-gray-500">· {RUN_TYPE_LABELS[record.run_type]}</span>
                )}
                <span className="ml-2 text-gray-400">{new Date(record.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <div className="flex flex-wrap gap-4 text-sm items-center">
                {record.distance && (
                  <div className="text-gray-600">
                    <strong className="text-gray-900">{record.distance} km</strong> | {record.avg_pace ? formatPace(record.avg_pace) : '--'}
                  </div>
                )}
                {record.avg_heart_rate && (
                  <div className="text-gray-600">
                    心率 <strong className="text-gray-900">{record.avg_heart_rate} bpm</strong>
                  </div>
                )}
                {record.avg_cadence && (
                  <div className="text-gray-600">
                    步频 <strong className="text-gray-900">{record.avg_cadence} spm</strong>
                  </div>
                )}
                {record.run_score != null && (
                  <div className="text-primary font-semibold">
                    分数 <strong>{record.run_score}</strong>
                  </div>
                )}
                <div className="ml-auto flex gap-2">
                  <span className="text-xs px-3 py-1 bg-primary-light text-primary font-medium rounded-lg">
                    {record.record_type === 'both' ? '备忘录+视频' : record.record_type === 'memo' ? '备忘录分析' : '视频分析'}
                  </span>
                </div>
              </div>
              </Link>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Records;
