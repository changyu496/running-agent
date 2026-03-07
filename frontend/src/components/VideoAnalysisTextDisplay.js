/**
 * 视频跑姿 AI 分析结果展示
 * 解析 JSON（含 markdown 代码块）并结构化展示，避免直接显示原始 JSON
 */
import React from 'react';

/** 从文本中提取并解析 JSON（支持：纯 JSON、```json 代码块、前置说明文字+JSON） */
function parseIfJson(val) {
  if (typeof val !== 'string') return val;
  let s = val.trim();
  // 1. 提取 ```json ... ``` 或 ``` ... ``` 代码块
  const codeBlockMatch = s.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlockMatch) {
    s = codeBlockMatch[1].trim();
  } else {
    // 2. 查找第一个 { 或 [，尝试解析
    const objStart = s.indexOf('{');
    const arrStart = s.indexOf('[');
    let start = -1;
    let openChar = '';
    let closeChar = '';
    if (objStart >= 0 && (arrStart < 0 || objStart < arrStart)) {
      start = objStart;
      openChar = '{';
      closeChar = '}';
    } else if (arrStart >= 0) {
      start = arrStart;
      openChar = '[';
      closeChar = ']';
    }
    if (start >= 0) {
      let depth = 0;
      let end = -1;
      for (let i = start; i < s.length; i++) {
        if (s[i] === openChar) depth++;
        else if (s[i] === closeChar) {
          depth--;
          if (depth === 0) {
            end = i + 1;
            break;
          }
        }
      }
      if (end > start) s = s.slice(start, end);
    }
  }
  if ((s.startsWith('{') || s.startsWith('[')) && s.length > 2) {
    try {
      return JSON.parse(s);
    } catch {
      return null;
    }
  }
  return null;
}

const LABELS = {
  shoulder_balance: '肩部平衡',
  hip_tilt: '骨盆倾斜',
  center_alignment: '中心对齐',
  center_alignment_angle: '中心线对齐',
  body_center_line: '身体中心线对齐',
  foot_balance: '脚落地平衡',
  knee_alignment: '膝盖对齐',
};

const ISSUE_KEY_LABELS = {
  issues: '问题',
  improvement_areas: '改进建议',
};

function getLabel(key) {
  return LABELS[key] ?? ISSUE_KEY_LABELS[key] ?? (typeof key === 'string' ? key.replace(/_/g, ' ') : String(key));
}

/** 将可能为对象的值转为可渲染字符串 */
function toText(v) {
  if (v == null || v === '') return '';
  if (typeof v === 'string') return v;
  if (typeof v === 'number') return String(v);
  if (Array.isArray(v)) return v.map(toText).join('；');
  if (typeof v === 'object') {
    const d = v.description ?? v.desc ?? v.描述 ?? v.改进区域 ?? v.improvement_area ?? v.improvement_areas;
    if (d != null) return toText(d);
    // 避免直接渲染 {score, description, improvement_areas} 等对象
    const score = v.score;
    const parts = [];
    if (score != null && typeof score !== 'object') parts.push(`${score}分`);
    const arr = Array.isArray(v.improvement_areas) ? v.improvement_areas : v.improvement_area;
    if (arr && arr.length) parts.push(toText(arr));
    if (parts.length) return parts.join('；');
    return Object.entries(v).filter(([, x]) => x != null && x !== '').map(([, x]) => toText(x)).join(' ');
  }
  return String(v);
}

function formatSection(obj, title) {
  if (!obj || typeof obj !== 'object') return null;
  const items = [];
  for (const [key, val] of Object.entries(obj)) {
    if (val == null || val === '') continue;
    const label = getLabel(key);
    if (typeof val === 'object' && !Array.isArray(val)) {
      const scoreVal = val.score;
      const score = scoreVal != null ? ` (${toText(scoreVal)}分)` : '';
      const desc = toText(val.description ?? val.desc ?? val.描述 ?? val.改进区域 ?? val.improvement_area ?? val.improvement_areas ?? '');
      if (desc) items.push({ label, score, text: desc });
    } else if (typeof val === 'string') {
      items.push({ label, score: '', text: val });
    }
  }
  if (items.length === 0) return null;
  return { title, items };
}

export default function VideoAnalysisTextDisplay({ analysisText }) {
  if (!analysisText) return null;

  const parsed = parseIfJson(analysisText);
  if (parsed && typeof parsed === 'object') {
    const sections = [];
    const sym = parsed.symmetry_evaluation ?? parsed.对称性评估;
    const align = parsed.alignment_analysis ?? parsed.对齐分析;
    const overall = parsed.overall_score ?? parsed.总分 ?? parsed.整体评分;
    const issues = parsed.symmetry_issues_and_improvement_areas ?? parsed.对称性问题和改进区域 ?? parsed.需要改进;
    const training = parsed.training_recommendations ?? parsed.针对性训练建议 ?? parsed.suggestions;

    if (sym) sections.push(formatSection(sym, '对称性评估'));
    if (align) sections.push(formatSection(align, '对齐度分析'));
    if (issues && typeof issues === 'object') {
      const issueItems = [];
      for (const [k, v] of Object.entries(issues)) {
        if (v == null) continue;
        const label = getLabel(k);
        const issue = toText(v.issue ?? v.问题 ?? v.issues ?? v);
        const area = toText(v.improvement_area ?? v.improvement_areas ?? v.改进区域 ?? v.desc ?? '');
        const text = area || issue;
        if (text) issueItems.push({ label: label !== k ? label : '', text });
      }
      if (issueItems.length) sections.push({ title: '对称性问题和改进', items: issueItems });
    }
    if (Array.isArray(training) && training.length) {
      const trainingItems = training
        .map((t) => ({ label: '', score: '', text: toText(typeof t === 'string' ? t : (t.text ?? t.建议 ?? t)) }))
        .filter((it) => toText(it.text).trim());
      if (trainingItems.length) sections.push({ title: '针对性训练建议', items: trainingItems });
    }

    const hasContent = overall != null || sections.some(Boolean);
    if (!hasContent) return <div className="text-sm text-gray-600 whitespace-pre-wrap">{analysisText}</div>;

    return (
      <div className="space-y-4">
        {overall != null && (
          <div className="bg-green-50 p-4 border border-green-200">
            <div className="text-xs text-gray-600 uppercase">整体评分</div>
            <div className="text-2xl font-bold text-green-700">{toText(overall)} 分</div>
          </div>
        )}
        {sections
          .filter((sec) => sec && sec.items?.length > 0 && sec.items.some((it) => toText(it.text).trim()))
          .map((sec, i) => (
            <div key={i} className="bg-white p-4 border border-gray-200">
              <div className="font-semibold text-gray-900 mb-3">{sec.title}</div>
              <div className="space-y-2 text-sm text-gray-700">
                {sec.items.filter((item) => toText(item.text).trim()).map((item, j) => (
                  <div key={j}>
                    {item.label && (
                      <span className="font-medium text-gray-800">{toText(item.label)}{toText(item.score)}：</span>
                    )}
                    {toText(item.text)}
                  </div>
                ))}
              </div>
            </div>
          ))}
      </div>
    );
  }

  // 非 JSON 或解析失败，直接显示原文
  return <div className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{analysisText}</div>;
}
