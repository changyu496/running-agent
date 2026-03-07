import React, { useEffect, useState } from 'react';
import { getGuidance } from '../services/api';

const Guidance = () => {
  const [guidance, setGuidance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGuidance();
  }, []);

  const loadGuidance = async () => {
    try {
      const data = await getGuidance();
      setGuidance(data);
    } catch (error) {
      console.error('加载智能指导失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-gray-600">加载中...</div>;
  }

  if (!guidance) {
    return <div className="text-gray-600">暂无数据</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2 tracking-tight">智能指导</h2>
      <p className="text-gray-500 mb-7 text-sm">基于你的数据生成个性化训练建议</p>

      <div className="space-y-4">
        {/* 本周训练总结 */}
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm">
          <div className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-3">
            <span className="w-1 h-5 bg-primary rounded"></span>
            本周训练总结
          </div>
          <div className="text-sm text-gray-600 leading-relaxed">
            {guidance.week_summary}
          </div>
        </div>

        {/* 趋势分析 */}
        {guidance.trend_analysis && guidance.trend_analysis.length > 0 && (
          <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm">
            <div className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-3">
              <span className="w-1 h-5 bg-primary rounded"></span>
              趋势分析
            </div>
            <div className="text-sm text-gray-600 leading-relaxed">
              <ul className="list-disc list-inside space-y-1">
                {guidance.trend_analysis.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* 下周训练建议 */}
        {guidance.next_week_suggestions && (
          <div className="bg-white p-6 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-3">下周训练建议</div>
            <div className="text-sm text-gray-600 leading-relaxed">
              <ol className="list-decimal list-inside space-y-2">
                {guidance.next_week_suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ol>
            </div>
          </div>
        )}

        {/* 注意事项 */}
        {guidance.health_reminders && (
          <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm">
            <div className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-3">
              <span className="w-1 h-5 bg-primary rounded"></span>
              注意事项
            </div>
            <div className="text-sm text-gray-600 leading-relaxed">
              <ul className="list-disc list-inside space-y-1">
                {guidance.health_reminders.map((reminder, index) => (
                  <li key={index}>{reminder}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Guidance;
