import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getRecordDetail, deleteRecord, getApiBaseUrl } from '../services/api';
import AnalysisResultDisplay from '../components/AnalysisResultDisplay';
import VideoAnalysisTextDisplay from '../components/VideoAnalysisTextDisplay';
import { formatPace } from '../utils/format';

const RecordDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [linkedRecords, setLinkedRecords] = useState([]);

  useEffect(() => {
    loadDetail();
  }, [id]);

  const loadDetail = async () => {
    try {
      const data = await getRecordDetail(id);
      setRecord(data);
      
      // 加载关联记录
      if (data.linked_records && data.linked_records.length > 0) {
        const linked = await Promise.all(
          data.linked_records
            .filter(rid => rid !== parseInt(id))
            .map(rid => getRecordDetail(rid).catch(() => null))
        );
        setLinkedRecords(linked.filter(r => r !== null));
      }
    } catch (error) {
      console.error('加载详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('确定要删除这条记录吗？')) {
      return;
    }

    try {
      await deleteRecord(id);
      navigate('/records');
    } catch (error) {
      console.error('删除失败:', error);
      alert('删除失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return <div className="text-gray-600">加载中...</div>;
  }

  if (!record) {
    return <div className="text-gray-600">记录不存在</div>;
  }

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <Link to="/records" className="text-sm text-gray-500 hover:text-primary transition-colors">
          ← 返回列表
        </Link>
        <button
          onClick={handleDelete}
          className="text-sm text-red-600 hover:text-red-700 px-3 py-1.5 rounded-lg border border-red-200 hover:bg-red-50 transition-colors"
        >
          删除记录
        </button>
      </div>

      <h2 className="text-2xl font-semibold text-gray-900 mb-6 tracking-tight">记录详情</h2>

      <div className="space-y-4">
        {/* 关联记录 */}
        {linkedRecords.length > 0 && (
          <div className="bg-white p-6 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-3">关联记录</div>
            <div className="space-y-2">
              {linkedRecords.map((linked) => (
                <Link
                  key={linked.id}
                  to={`/records/${linked.id}`}
                  className="block p-3 bg-gray-50 border border-gray-200 hover:bg-gray-100 text-sm"
                >
                  {new Date(linked.created_at).toLocaleString('zh-CN')} - 
                  {linked.record_type === 'memo' ? '备忘录分析' : '视频分析'}
                </Link>
              ))}
            </div>
          </div>
        )}

        {record.memo_text && (
          <div className="bg-white p-6 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-3">备忘录</div>
            <div className="text-sm text-gray-600 whitespace-pre-wrap">{record.memo_text}</div>
          </div>
        )}

        {record.coros_data && (
          <div className="bg-white p-6 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-3">高驰数据{record.coros_data.avg_power != null ? '（含 Stryd）' : ''}</div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><strong>距离:</strong> {record.coros_data.distance} km</div>
              <div><strong>配速:</strong> {formatPace(record.coros_data.avg_pace)}</div>
              <div><strong>平均心率:</strong> {record.coros_data.avg_heart_rate} bpm</div>
              <div><strong>步频:</strong> {record.coros_data.avg_cadence} spm</div>
              {record.coros_data.avg_power != null && <div><strong>平均功率:</strong> {record.coros_data.avg_power} W</div>}
              {record.coros_data.max_power != null && <div><strong>最高功率:</strong> {record.coros_data.max_power} W</div>}
              {record.coros_data.form_power != null && <div><strong>姿势功率:</strong> {record.coros_data.form_power} W</div>}
              {record.coros_data.form_power_ratio != null && <div><strong>姿势功率比:</strong> {record.coros_data.form_power_ratio}%</div>}
              {record.coros_data.avg_gct != null && <div><strong>触地时间:</strong> {record.coros_data.avg_gct} ms</div>}
              {record.coros_data.vertical_oscillation != null && <div><strong>垂直振幅:</strong> {record.coros_data.vertical_oscillation} cm</div>}
            </div>
          </div>
        )}

        {record.video_analysis && (
          <div className="bg-white p-6 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-3">跑姿分析</div>
            {record.video_path && (
              <div className="mb-4">
                <div className="text-xs text-gray-500 mb-2">跑步视频</div>
                <video
                  src={`${getApiBaseUrl()}/api/files/${record.video_path.split(/[/\\]/).pop()}`}
                  controls
                  className="max-w-full mx-auto object-contain border border-gray-200"
                  style={{ maxHeight: '400px' }}
                />
              </div>
            )}
            {record.video_analysis.visualization_path && (
              <div className="mb-4">
                <div className="text-xs text-gray-500 mb-2">姿态可视化（骨架+角度）</div>
                {/\.(mp4|mov|webm)$/i.test(record.video_analysis.visualization_path) ? (
                  <video
                    src={`${getApiBaseUrl()}/api/files/${record.video_analysis.visualization_path.split(/[/\\]/).pop()}`}
                    controls
                    className="max-w-full border border-gray-200 object-contain"
                    style={{ maxHeight: '500px' }}
                  />
                ) : (
                  <img
                    src={`${getApiBaseUrl()}/api/files/${record.video_analysis.visualization_path.split(/[/\\]/).pop()}`}
                    alt="跑姿分析"
                    className="max-w-full border border-gray-200 object-contain"
                    style={{ maxHeight: '500px' }}
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                )}
              </div>
            )}
            <div className="text-sm text-gray-600">
              <div><strong>整体评分:</strong> {record.video_analysis.overall_score}/100</div>
              {record.video_analysis.analysis_text && (
                <div className="mt-3">
                  <VideoAnalysisTextDisplay analysisText={record.video_analysis.analysis_text} />
                </div>
              )}
            </div>
          </div>
        )}

        {record.analysis_result && (
          <div className="bg-white p-6 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-4">AI分析结果</div>
            <AnalysisResultDisplay
              analysis={(() => {
                const a = record.analysis_result;
                if (!a) return {};
                if (typeof a === 'object') return a;
                try { return JSON.parse(a); } catch { return { raw_text: a }; }
              })()}
              runDate={record.run_date}
              runType={record.run_type}
              runScore={record.run_score}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default RecordDetail;
