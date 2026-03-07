/**
 * 配速格式化为 4'31" /km
 * 支持：4.51、4.8、"4'31""、"4:31" 等输入
 */
export function formatPace(v) {
  if (v == null || v === '') return v;
  const s = String(v).trim();
  // 已是 4'31" 或 4'31"/km 格式
  if (/^\d+[''′]\d+["″]?\s*(\/km)?$/i.test(s)) return s.includes('/km') ? s : `${s} /km`;
  // 4:31 格式
  const colon = s.match(/^(\d+):(\d+)$/);
  if (colon) return `${colon[1]}'${colon[2].padStart(2, '0')}" /km`;
  // 小数分钟 4.51 -> 4'31"
  const num = parseFloat(s);
  if (!Number.isNaN(num) && num >= 0) {
    const min = Math.floor(num);
    const sec = Math.round((num - min) * 60);
    return `${min}'${String(sec).padStart(2, '0')}" /km`;
  }
  return v;
}
