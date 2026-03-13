import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getRecordDetail, deleteRecord, updateRecord, getFileUrl } from '../services/api';
import AnalysisResultDisplay from '../components/AnalysisResultDisplay';
import VideoAnalysisTextDisplay from '../components/VideoAnalysisTextDisplay';
import { formatPace } from '../utils/format';

const RUN_TYPE_OPTIONS = [
  { value: 'recovery', label: '恢复跑' },
  { value: 'aerobic', label: '有氧跑' },
  { value: 'long', label: '长距离' },
  { value: 'pace', label: '节奏跑' },
  { value: 'interval', label: '间歇跑' },
  { value: 'other', label: '其他' },
];

const RecordDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [linkedRecords, setLinkedRecords] = useState([]);
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);

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

  const openEdit = () => {
    const emptyCoros = {
      distance: '', duration: '', avg_pace: '', avg_heart_rate: '', max_heart_rate: '',
      avg_cadence: '', avg_stride_length: '', calories: '', elevation_gain: '', elevation_loss: '',
      avg_power: '', max_power: '', form_power: '', form_power_ratio: '', avg_gct: '', vertical_oscillation: '',
    };
    setEditForm({
      run_date: record.run_date || '',
      run_type: record.run_type || '',
      run_score: record.run_score ?? '',
      memo_text: record.memo_text || '',
      coros_data: record.coros_data ? {
        distance: record.coros_data.distance ?? '',
        duration: record.coros_data.duration || '',
        avg_pace: record.coros_data.avg_pace || '',
        avg_heart_rate: record.coros_data.avg_heart_rate ?? '',
        max_heart_rate: record.coros_data.max_heart_rate ?? '',
        avg_cadence: record.coros_data.avg_cadence ?? '',
        avg_stride_length: record.coros_data.avg_stride_length ?? '',
        calories: record.coros_data.calories ?? '',
        elevation_gain: record.coros_data.elevation_gain ?? '',
        elevation_loss: record.coros_data.elevation_loss ?? '',
        avg_power: record.coros_data.avg_power ?? '',
        max_power: record.coros_data.max_power ?? '',
        form_power: record.coros_data.form_power ?? '',
        form_power_ratio: record.coros_data.form_power_ratio ?? '',
        avg_gct: record.coros_data.avg_gct ?? '',
        vertical_oscillation: record.coros_data.vertical_oscillation ?? '',
      } : emptyCoros,
    });
    setEditOpen(true);
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      const payload = {
        run_date: editForm.run_date || null,
        run_type: editForm.run_type || null,
        run_score: editForm.run_score === '' ? null : parseInt(editForm.run_score, 10),
        memo_text: editForm.memo_text || null,
      };
      if (editForm.coros_data && (record.coros_data || Object.values(editForm.coros_data).some((v) => v !== '' && v != null))) {
        const cd = editForm.coros_data;
        payload.coros_data = {
          distance: cd.distance === '' ? null : parseFloat(cd.distance),
          duration: cd.duration || null,
          avg_pace: cd.avg_pace || null,
          avg_heart_rate: cd.avg_heart_rate === '' ? null : parseInt(cd.avg_heart_rate, 10),
          max_heart_rate: cd.max_heart_rate === '' ? null : parseInt(cd.max_heart_rate, 10),
          avg_cadence: cd.avg_cadence === '' ? null : parseInt(cd.avg_cadence, 10),
          avg_stride_length: cd.avg_stride_length === '' ? null : parseFloat(cd.avg_stride_length),
          calories: cd.calories === '' ? null : parseInt(cd.calories, 10),
          elevation_gain: cd.elevation_gain === '' ? null : parseInt(cd.elevation_gain, 10),
          elevation_loss: cd.elevation_loss === '' ? null : parseInt(cd.elevation_loss, 10),
          avg_power: cd.avg_power === '' ? null : parseInt(cd.avg_power, 10),
          max_power: cd.max_power === '' ? null : parseInt(cd.max_power, 10),
          form_power: cd.form_power === '' ? null : parseInt(cd.form_power, 10),
          form_power_ratio: cd.form_power_ratio === '' ? null : parseInt(cd.form_power_ratio, 10),
          avg_gct: cd.avg_gct === '' ? null : parseInt(cd.avg_gct, 10),
          vertical_oscillation: cd.vertical_oscillation === '' ? null : parseFloat(cd.vertical_oscillation),
        };
      }
      await updateRecord(id, payload);
      setEditOpen(false);
      loadDetail();
    } catch (error) {
      console.error('保存失败:', error);
      alert('保存失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  const updateEditField = (path, value) => {
    if (path.startsWith('coros_data.')) {
      const key = path.replace('coros_data.', '');
      setEditForm((prev) => ({
        ...prev,
        coros_data: { ...(prev.coros_data || {}), [key]: value },
      }));
    } else {
      setEditForm((prev) => ({ ...prev, [path]: value }));
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
        <div className="flex gap-2">
          <button
            onClick={openEdit}
            className="text-sm text-primary hover:bg-primary-light px-3 py-1.5 rounded-lg border border-primary/30 transition-colors"
          >
            编辑
          </button>
          <button
            onClick={handleDelete}
            className="text-sm text-red-600 hover:text-red-700 px-3 py-1.5 rounded-lg border border-red-200 hover:bg-red-50 transition-colors"
          >
            删除记录
          </button>
        </div>
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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
              {record.coros_image_path && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">高驰截图</div>
                  <a
                    href={getFileUrl(record.coros_image_path.split(/[/\\]/).pop())}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-lg overflow-hidden border border-gray-200 hover:border-primary/50 transition-colors"
                  >
                    <img
                      src={getFileUrl(record.coros_image_path.split(/[/\\]/).pop())}
                      alt="高驰截图"
                      className="w-full h-auto object-contain max-h-64"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  </a>
                  <p className="text-xs text-gray-500 mt-1">点击可查看大图</p>
                </div>
              )}
            </div>
          </div>
        )}

        {record.coros_image_path && !record.coros_data && (
          <div className="bg-white p-6 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-3">高驰截图</div>
            <a
              href={getFileUrl(record.coros_image_path.split(/[/\\]/).pop())}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-lg overflow-hidden border border-gray-200 hover:border-primary/50 transition-colors max-w-md"
            >
              <img
                src={getFileUrl(record.coros_image_path.split(/[/\\]/).pop())}
                alt="高驰截图"
                className="w-full h-auto object-contain max-h-64"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            </a>
            <p className="text-xs text-gray-500 mt-1">点击可查看大图</p>
          </div>
        )}

        {record.video_analysis && (
          <div className="bg-white p-6 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-4">跑姿分析</div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {record.video_path && (
                <div className="flex flex-col min-w-0">
                  <div className="text-sm font-medium text-gray-700 mb-2">跑步视频</div>
                  <div className="flex-1 rounded-lg overflow-hidden bg-gray-50 border border-gray-200">
                    <video
                      src={getFileUrl(record.video_path.split(/[/\\]/).pop())}
                      controls
                      className="w-full h-auto object-contain"
                      style={{ maxHeight: '360px' }}
                    />
                  </div>
                </div>
              )}
              {record.video_analysis.visualization_path && (
                <div className="flex flex-col min-w-0">
                  <div className="text-sm font-medium text-gray-700 mb-2">姿态可视化（骨架+角度）</div>
                  <div className="flex-1 rounded-lg overflow-hidden bg-gray-50 border border-gray-200">
                    {/\.(mp4|mov|webm)$/i.test(record.video_analysis.visualization_path) ? (
                      <video
                        src={getFileUrl(record.video_analysis.visualization_path.split(/[/\\]/).pop())}
                        controls
                        className="w-full h-auto object-contain"
                        style={{ maxHeight: '360px' }}
                      />
                    ) : (
                      <img
                        src={getFileUrl(record.video_analysis.visualization_path.split(/[/\\]/).pop())}
                        alt="跑姿分析"
                        className="w-full h-auto object-contain"
                        style={{ maxHeight: '360px' }}
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    )}
                  </div>
                </div>
              )}
            </div>
            {(() => {
              const ad = record.video_analysis?.angles_data || record.video_analysis?.symmetry_data || {};
              const hasAnkle = ad.ankle_stability || ad.ankle_inversion_tendency || ad.ankle_eversion_tendency;
              if (!hasAnkle) return null;
              return (
                <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="text-sm font-medium text-gray-700 mb-3">脚踝稳定性</div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {(ad.ankle_inversion_tendency && ad.ankle_inversion_tendency !== '--') && (
                      <div className="bg-white p-3 rounded border border-gray-200 text-center">
                        <div className="text-xs text-gray-500">内翻倾向</div>
                        <div className="text-base font-semibold text-blue-600">{ad.ankle_inversion_tendency}</div>
                      </div>
                    )}
                    {(ad.ankle_eversion_tendency && ad.ankle_eversion_tendency !== '--') && (
                      <div className="bg-white p-3 rounded border border-gray-200 text-center">
                        <div className="text-xs text-gray-500">外翻倾向</div>
                        <div className="text-base font-semibold text-amber-600">{ad.ankle_eversion_tendency}</div>
                      </div>
                    )}
                    {ad.ankle_stability && ad.ankle_stability !== '--' && (
                      <div className="bg-white p-3 rounded border border-gray-200 text-center">
                        <div className="text-xs text-gray-500">稳定性</div>
                        <div className="text-base font-semibold text-green-600">{ad.ankle_stability}</div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}
            <div className="text-sm text-gray-600 mt-4 pt-4 border-t border-gray-100">
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

      {/* 编辑弹窗 */}
      {editOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setEditOpen(false)}>
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">编辑记录</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">跑步日期</label>
                  <input type="date" value={editForm.run_date || ''} onChange={(e) => updateEditField('run_date', e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">训练类型</label>
                  <select value={editForm.run_type || ''} onChange={(e) => updateEditField('run_type', e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
                    <option value="">--</option>
                    {RUN_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">跑步分数</label>
                  <input type="number" min="0" max="100" value={editForm.run_score ?? ''} onChange={(e) => updateEditField('run_score', e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" placeholder="0-100" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">备忘录</label>
                <textarea value={editForm.memo_text || ''} onChange={(e) => updateEditField('memo_text', e.target.value)} rows={3} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
              </div>
              {editForm.coros_data && (
                <div className="pt-4 border-t border-gray-200">
                  <div className="text-sm font-semibold text-gray-900 mb-3">高驰数据</div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div><label className="block text-xs text-gray-500 mb-0.5">距离(km)</label><input type="number" step="0.01" value={editForm.coros_data.distance ?? ''} onChange={(e) => updateEditField('coros_data.distance', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" /></div>
                    <div><label className="block text-xs text-gray-500 mb-0.5">配速</label><input type="text" value={editForm.coros_data.avg_pace ?? ''} onChange={(e) => updateEditField('coros_data.avg_pace', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" placeholder="4'30&quot;" /></div>
                    <div><label className="block text-xs text-gray-500 mb-0.5">心率(bpm)</label><input type="number" value={editForm.coros_data.avg_heart_rate ?? ''} onChange={(e) => updateEditField('coros_data.avg_heart_rate', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" /></div>
                    <div><label className="block text-xs text-gray-500 mb-0.5">步频(spm)</label><input type="number" value={editForm.coros_data.avg_cadence ?? ''} onChange={(e) => updateEditField('coros_data.avg_cadence', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" /></div>
                    <div><label className="block text-xs text-gray-500 mb-0.5">时长</label><input type="text" value={editForm.coros_data.duration ?? ''} onChange={(e) => updateEditField('coros_data.duration', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" placeholder="0:45:30" /></div>
                    <div><label className="block text-xs text-gray-500 mb-0.5">卡路里</label><input type="number" value={editForm.coros_data.calories ?? ''} onChange={(e) => updateEditField('coros_data.calories', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" /></div>
                    <div><label className="block text-xs text-gray-500 mb-0.5">平均功率(W)</label><input type="number" value={editForm.coros_data.avg_power ?? ''} onChange={(e) => updateEditField('coros_data.avg_power', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" /></div>
                    <div><label className="block text-xs text-gray-500 mb-0.5">触地时间(ms)</label><input type="number" value={editForm.coros_data.avg_gct ?? ''} onChange={(e) => updateEditField('coros_data.avg_gct', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" /></div>
                    <div><label className="block text-xs text-gray-500 mb-0.5">垂直振幅(cm)</label><input type="number" step="0.1" value={editForm.coros_data.vertical_oscillation ?? ''} onChange={(e) => updateEditField('coros_data.vertical_oscillation', e.target.value)} className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm" /></div>
                  </div>
                </div>
              )}
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end gap-2">
              <button onClick={() => setEditOpen(false)} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">取消</button>
              <button onClick={handleSaveEdit} disabled={saving} className="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50">{saving ? '保存中...' : '保存'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecordDetail;
