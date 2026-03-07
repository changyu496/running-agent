import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { clearToken } from '../services/api';

const Layout = ({ children, onLogout }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: '首页', icon: '🏠' },
    { path: '/memo', label: '新建分析', icon: '📝' },
    { path: '/video', label: '视频分析', icon: '🎬' },
    { path: '/records', label: '历史记录', icon: '📊' },
    { path: '/stats', label: '数据统计', icon: '📈' },
    { path: '/guidance', label: '智能指导', icon: '💡' },
  ];

  return (
    <div className="flex h-screen bg-white">
      {/* 侧边栏 */}
      <div className="w-[260px] bg-white border-r border-gray-100 flex flex-col">
        <div className="p-6 pb-8 border-b border-gray-100">
          <h1 className="text-xl font-bold text-primary tracking-tight">步知</h1>
          <p className="text-[11px] text-gray-400 mt-0.5">Bùzhī · 步态可知</p>
        </div>
        <nav className="p-3 pt-5 flex-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 mb-1 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-primary-light text-primary font-semibold'
                    : 'text-gray-500 hover:bg-primary-light hover:text-gray-900'
                }`}
              >
                <span className="text-base opacity-90">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        {onLogout && (
          <div className="p-3 border-t border-gray-100">
            <button
              onClick={() => { clearToken(); onLogout(); }}
              className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-900 transition-all"
            >
              <span>🚪</span> 退出登录
            </button>
          </div>
        )}
      </div>

      {/* 主内容区 */}
      <div className="flex-1 overflow-auto bg-[#fafbfc]">
        <div className="p-8">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Layout;
