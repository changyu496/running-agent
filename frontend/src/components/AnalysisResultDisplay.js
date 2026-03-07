/**
 * AI 分析结果美化展示组件
 * 将 data_overview、performance_evaluation、improvement_suggestions 结构化展示
 */
import React from 'react';
import { formatPace } from '../utils/format';

const RUN_TYPE_LABELS = {
  recovery: '恢复跑',
  aerobic: '有氧跑',
  long: '长距离',
  pace: '节奏跑',
  interval: '间歇跑',
  other: '其他',
};

const DATA_OVERVIEW_KEYS = [
  { keys: ['distance', 'distance_km', '距离'], label: '距离', suffix: '', fmt: (v) => v },
  { keys: ['duration', 'duration_hhmmss', '运动时间', '运动时长'], label: '时长', suffix: '', fmt: (v) => v },
  { keys: ['avg_pace', 'average_pace_min_per_km', '平均配速'], label: '平均配速', suffix: '', fmt: formatPace },
  { keys: ['average_speed_km_per_h', '平均速度'], label: '平均速度', suffix: '', fmt: (v) => v },
  { keys: ['avg_heart_rate', 'average_heart_rate_bpm', '平均心率'], label: '平均心率', suffix: '', fmt: (v) => v },
  { keys: ['max_heart_rate', 'max_heart_rate_bpm', '最大心率'], label: '最大心率', suffix: '', fmt: (v) => v },
  { keys: ['avg_cadence', 'average_step_frequency_spd', '平均步频'], label: '平均步频', suffix: '', fmt: (v) => v },
  { keys: ['max_step_frequency_spd', '最大步频'], label: '最大步频', suffix: '', fmt: (v) => v },
  { keys: ['avg_stride_length', 'average_stride_length_cm', '平均步幅'], label: '平均步幅', suffix: '', fmt: (v) => v },
  { keys: ['avg_power', 'average_power_w', '平均功率'], label: '平均功率', suffix: ' W', fmt: (v) => (v != null && v !== '' ? String(v) : v) },
  { keys: ['max_power', 'max_power_w', '最高功率', '最大功率'], label: '最高功率', suffix: ' W', fmt: (v) => (v != null && v !== '' ? String(v) : v) },
  { keys: ['form_power', 'form_power_w', '姿势功率'], label: '姿势功率', suffix: ' W', fmt: (v) => (v != null && v !== '' ? String(v) : v) },
  { keys: ['form_power_ratio', '姿势功率比'], label: '姿势功率比', suffix: '%', fmt: (v) => (v != null && v !== '' ? String(v) : v) },
  { keys: ['avg_gct', 'gct', '触地时间'], label: '触地时间', suffix: ' ms', fmt: (v) => (v != null && v !== '' ? String(v) : v) },
  { keys: ['vertical_oscillation_cm', 'vertical_oscillation', '垂直振幅'], label: '垂直振幅', suffix: ' cm', fmt: (v) => (v != null && v !== '' ? String(v) : v) },
  { keys: ['weather_condition', '天气'], label: '天气', suffix: '', fmt: (v) => v },
];

function getValue(obj, keys, fmt = (v) => v) {
  for (const k of keys) {
    const v = obj?.[k];
    if (v !== undefined && v !== null && v !== '') return fmt(v);
  }
  return null;
}

/** 将可能为对象或字符串的项转为可渲染文本（AI 可能返回 {建议, 理由} 或 {category, description} 等对象） */
function toDisplayText(item) {
  if (item == null) return '';
  if (typeof item === 'string') return item;
  if (typeof item === 'number') return String(item);
  if (typeof item === 'object') {
    const suggest = item.建议 ?? item.suggestion ?? item.text;
    const reason = item.理由 ?? item.reason;
    if (suggest != null && reason != null) return `${suggest}（${reason}）`;
    if (suggest != null) return String(suggest);
    if (reason != null) return String(reason);
    // category + description：直接写内容，不显示英文 key
    const cat = item.category ?? item.类别 ?? item.分类;
    const desc = item.description ?? item.desc ?? item.描述;
    if (cat != null && desc != null) return `${cat}：${desc}`;
    if (desc != null) return String(desc);
    if (cat != null) return String(cat);
    return Object.entries(item)
      .filter(([, v]) => v != null && v !== '')
      .map(([k, v]) => `${v}`)
      .join(' ');
  }
  return String(item);
}

function parseIfJson(val) {
  if (typeof val !== 'string') return val;
  let s = val.trim();
  // 去除 markdown 代码块 ```json ... ```
  if (s.startsWith('```')) {
    const lines = s.split('\n');
    if (lines[0].startsWith('```')) lines.shift();
    if (lines.length && lines[lines.length - 1].trim() === '```') lines.pop();
    s = lines.join('\n').trim();
  }
  if ((s.startsWith('{') || s.startsWith('[')) && s.length > 2) {
    try {
      return JSON.parse(s);
    } catch {
      return val;
    }
  }
  return val;
}

export default function AnalysisResultDisplay({ analysis, runDate, runType, runScore }) {
  if (!analysis) return null;

  // 若 analysis 整体是 JSON 字符串，先解析
  let a = typeof analysis === 'string' ? parseIfJson(analysis) : analysis;
  if (typeof a !== 'object' || a === null) return null;

  let dataOverview = a.data_overview || {};
  let perfEval = a.performance_evaluation || {};
  let suggestions = a.improvement_suggestions || [];

  // 若 performance_evaluation 是 JSON 字符串，解析它（可能是完整 analysis 或仅 performance 部分）
  if (typeof perfEval === 'string') {
    const parsed = parseIfJson(perfEval);
    if (typeof parsed === 'object' && parsed !== null) {
      if (parsed.data_overview && !Object.keys(dataOverview).length) dataOverview = parsed.data_overview;
      if (parsed.performance_evaluation) perfEval = parsed.performance_evaluation;
      else perfEval = parsed;
      if (Array.isArray(parsed.improvement_suggestions) && suggestions.length === 0) suggestions = parsed.improvement_suggestions;
    }
  }

  // 若 data_overview 是字符串（如 JSON），解析
  if (typeof dataOverview === 'string') {
    const parsed = parseIfJson(dataOverview);
    if (typeof parsed === 'object' && parsed !== null) dataOverview = parsed;
  }

  const overallText = typeof perfEval === 'string' ? perfEval : perfEval.overall_assessment || perfEval.整体评价 || perfEval.text;
  const strengths = Array.isArray(perfEval.strengths) ? perfEval.strengths : (Array.isArray(perfEval.优点) ? perfEval.优点 : []);
  const areasForImprovement = Array.isArray(perfEval.areas_for_improvement) ? perfEval.areas_for_improvement : (Array.isArray(perfEval.需改进) ? perfEval.需改进 : (Array.isArray(perfEval['需要改进的地方']) ? perfEval['需要改进的地方'] : []));
  const suggestionsFromPerf = Array.isArray(perfEval.improvement_suggestions) ? perfEval.improvement_suggestions : (Array.isArray(perfEval.改进建议) ? perfEval.改进建议 : []);
  if (suggestionsFromPerf.length > 0 && suggestions.length === 0) suggestions = suggestionsFromPerf;

  // 若 overallText 是 JSON 字符串或 markdown 代码块包裹的 JSON，不当作正文显示
  const rawOverall = typeof overallText === 'string' ? overallText.trim() : '';
  const isJsonOrCodeBlock =
    rawOverall.startsWith('{') ||
    rawOverall.startsWith('[') ||
    rawOverall.startsWith('```');
  const displayOverallText = isJsonOrCodeBlock ? null : overallText;

  let metrics = DATA_OVERVIEW_KEYS.map(({ keys, label, suffix, fmt }) => {
    const v = getValue(dataOverview, keys, fmt);
    return v !== null ? { label, value: `${v}${suffix}` } : null;
  }).filter(Boolean);

  // 若标准 keys 未匹配到，用 data_overview 所有键值对（AI 可能用任意中文 key）
  if (metrics.length === 0 && typeof dataOverview === 'object' && Object.keys(dataOverview).length > 0) {
    const paceKeys = ['avg_pace', 'average_pace_min_per_km', '平均配速', '最大配速'];
    metrics = Object.entries(dataOverview)
      .filter(([, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => {
        const val = typeof v === 'object' ? JSON.stringify(v) : (paceKeys.includes(k) ? formatPace(v) : String(v));
        return { label: k, value: val };
      });
  }

  const runTypeLabel = runType ? (RUN_TYPE_LABELS[runType] || runType) : null;

  return (
    <div className="space-y-4">
      {/* 跑步日期、训练类型、跑步分数 */}
      {(runDate || runTypeLabel || runScore != null) && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {runDate && (
            <div className="bg-white p-4 border border-gray-100 rounded-xl shadow-sm">
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">跑步日期</div>
              <div className="font-semibold text-gray-900">{runDate}</div>
            </div>
          )}
          {runTypeLabel && (
            <div className="bg-white p-4 border border-gray-100 rounded-xl shadow-sm">
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">训练类型</div>
              <div className="font-semibold text-gray-900">{runTypeLabel}</div>
            </div>
          )}
          {runScore != null && (
            <div className="bg-primary-light p-4 border-2 border-primary rounded-xl">
              <div className="text-xs text-gray-600 uppercase tracking-wider mb-1">跑步分数</div>
              <div className="font-bold text-primary text-2xl">{runScore}</div>
              <div className="text-xs text-gray-500 mt-1">参考 RQ 跑力，0-100 分</div>
            </div>
          )}
        </div>
      )}

      {/* 数据概览 */}
      {metrics.length > 0 && (
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm">
          <div className="text-sm font-semibold text-gray-900 mb-4 pb-3 border-b border-gray-100">数据概览</div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {metrics.map(({ label, value }) => (
              <div key={label} className="bg-gray-50 p-4 border border-gray-100 rounded-lg">
                <div className="text-xs text-gray-400 mb-1">{label}</div>
                <div className="font-semibold text-gray-900">{value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 表现评价 */}
      {(displayOverallText || strengths.length > 0 || areasForImprovement.length > 0) && (
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm">
          <div className="text-sm font-semibold text-gray-900 mb-4 pb-3 border-b border-gray-100">表现评价</div>
          <div className="text-sm text-gray-700 space-y-4">
            {displayOverallText && (
              <div>
                <div className="font-medium text-gray-900 mb-1">整体评估</div>
                <p className="leading-relaxed">{displayOverallText}</p>
              </div>
            )}
            {strengths.length > 0 && (
              <div>
                <div className="font-medium text-gray-900 mb-2">优点</div>
                <ul className="list-disc list-inside space-y-1">
                  {strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="inline-block px-2 py-0.5 bg-primary-light text-primary text-xs font-medium rounded-lg">优</span>
                      <span>{toDisplayText(s)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {areasForImprovement.length > 0 && (
              <div>
                <div className="font-medium text-gray-900 mb-2">需改进</div>
                <ul className="list-disc list-inside space-y-1">
                  {areasForImprovement.map((a, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="inline-block px-2 py-0.5 bg-accent-light text-accent text-xs font-medium rounded-lg">改</span>
                      <span>{toDisplayText(a)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 改进建议 */}
      {suggestions.length > 0 && (
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm">
          <div className="text-sm font-semibold text-gray-900 mb-4 pb-3 border-b border-gray-100">改进建议</div>
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
            {suggestions.map((s, i) => (
              <li key={i} className="leading-relaxed">{toDisplayText(s)}</li>
            ))}
          </ol>
        </div>
      )}

      {/* 若无结构化数据，显示原始文本（排除 JSON 字符串） */}
      {!displayOverallText && metrics.length === 0 && suggestions.length === 0 && strengths.length === 0 && areasForImprovement.length === 0 && a.raw_text && !String(a.raw_text).trim().startsWith('{') && (
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm">
          <div className="text-sm font-semibold text-gray-900 mb-3">AI分析结果</div>
          <div className="text-sm text-gray-600 whitespace-pre-wrap">{a.raw_text}</div>
        </div>
      )}
    </div>
  );
}
