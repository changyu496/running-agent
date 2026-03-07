import React, { useEffect, useState } from 'react';
import { getStats, getStatsTrends } from '../services/api';
import { formatPace } from '../utils/format';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const Stats = () => {
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const overviewData = await getStats();
      setOverview(overviewData);
      
      // 加载趋势数据
      try {
        const trendsData = await getStatsTrends('heart_rate', 30);
        setTrends(trendsData);
      } catch (error) {
        console.warn('加载趋势数据失败:', error);
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-gray-600">加载中...</div>;
  }

  const chartData = trends ? {
    labels: trends.trends.map(t => new Date(t.date).toLocaleDateString('zh-CN')),
    datasets: [
      {
        label: '平均心率',
        data: trends.trends.map(t => t.value),
        borderColor: '#0d9488',
        backgroundColor: 'rgba(13, 148, 136, 0.15)',
      },
    ],
  } : null;

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2 tracking-tight">数据统计</h2>
      <p className="text-gray-500 mb-7 text-sm">基于历史数据的趋势分析</p>

      {overview && (
        <>
          <div className="grid grid-cols-4 gap-5 mb-8">
            <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm hover:border-gray-200 hover:shadow transition-all">
              <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">总跑步次数</div>
              <div className="text-2xl font-bold text-gray-900 tracking-tight">{overview.total_count}<span className="text-sm font-medium text-gray-400 ml-1">次</span></div>
            </div>
            <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm hover:border-gray-200 hover:shadow transition-all">
              <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">总距离</div>
              <div className="text-2xl font-bold text-gray-900 tracking-tight">{overview.total_distance}<span className="text-sm font-medium text-gray-400 ml-1">km</span></div>
            </div>
            <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm hover:border-gray-200 hover:shadow transition-all">
              <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">平均配速</div>
              <div className="text-2xl font-bold text-gray-900 tracking-tight">{overview.avg_pace ? formatPace(overview.avg_pace) : '--'}</div>
            </div>
            <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm hover:border-gray-200 hover:shadow transition-all">
              <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">平均心率</div>
              <div className="text-2xl font-bold text-primary tracking-tight">{overview.avg_heart_rate}<span className="text-sm font-medium text-gray-400 ml-1">bpm</span></div>
            </div>
          </div>

          {chartData && (
            <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm mb-6">
              <h3 className="text-base font-semibold text-gray-900 mb-4">心率趋势</h3>
              <div style={{ height: '300px' }}>
                <Line data={chartData} options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: true,
                    },
                  },
                }} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Stats;
