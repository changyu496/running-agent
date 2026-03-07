import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getRecords } from '../services/api';
import { formatPace } from '../utils/format';

const Home = () => {
  const [stats, setStats] = useState({
    weeklyCount: 0,
    weeklyDistance: 0,
    avgPace: '--',
    avgHeartRate: 0,
  });

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const records = await getRecords({ limit: 100 });
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      
      const weeklyRecords = records.filter(r => new Date(r.created_at) >= weekAgo);
      
      const totalDistance = weeklyRecords.reduce((sum, r) => sum + (r.distance || 0), 0);
      const totalHeartRate = weeklyRecords.reduce((sum, r) => sum + (r.avg_heart_rate || 0), 0);
      const avgHR = weeklyRecords.length > 0 ? Math.round(totalHeartRate / weeklyRecords.length) : 0;
      
      setStats({
        weeklyCount: weeklyRecords.length,
        weeklyDistance: totalDistance.toFixed(1),
        avgPace: '--',
        avgHeartRate: avgHR,
      });
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2 tracking-tight">欢迎回来</h2>
      <p className="text-gray-500 mb-7 text-sm">本周跑步概览</p>

      <div className="grid grid-cols-4 gap-5 mb-8">
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm hover:border-gray-200 hover:shadow transition-all">
          <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">本周跑步</div>
          <div className="text-2xl font-bold text-gray-900 tracking-tight">{stats.weeklyCount}<span className="text-sm font-medium text-gray-400 ml-1">次</span></div>
        </div>
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm hover:border-gray-200 hover:shadow transition-all">
          <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">总距离</div>
          <div className="text-2xl font-bold text-gray-900 tracking-tight">{stats.weeklyDistance}<span className="text-sm font-medium text-gray-400 ml-1">km</span></div>
        </div>
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm hover:border-gray-200 hover:shadow transition-all">
          <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">平均配速</div>
          <div className="text-2xl font-bold text-gray-900 tracking-tight">{formatPace(stats.avgPace)}</div>
        </div>
        <div className="bg-white p-6 border border-gray-100 rounded-xl shadow-sm hover:border-gray-200 hover:shadow transition-all">
          <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider font-medium">平均心率</div>
          <div className="text-2xl font-bold text-primary tracking-tight">{stats.avgHeartRate}<span className="text-sm font-medium text-gray-400 ml-1">bpm</span></div>
        </div>
      </div>

      <h3 className="text-base font-semibold text-gray-900 mb-4">快速操作</h3>
      <div className="flex gap-3">
        <Link
          to="/memo"
          className="px-6 py-3 bg-primary text-white text-sm font-semibold rounded-xl hover:bg-primary-hover transition-colors"
        >
          数据分析
        </Link>
        <Link
          to="/video"
          className="px-6 py-3 bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-xl hover:bg-primary-light hover:border-primary hover:text-primary transition-colors"
        >
          视频分析
        </Link>
      </div>
    </div>
  );
};

export default Home;
