import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, message } from 'antd';
import {
  ExperimentOutlined,
  UserOutlined,
  RobotOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined
} from '@ant-design/icons';
import TestList from './pages/tests/TestList';
import TestDetail from './pages/tests/TestDetail';
import DistillationList from './pages/distillation/DistillationList';
import DistillationDetail from './pages/distillation/DistillationDetail';
import ModelList from './pages/models/ModelList';
import ModelDetail from './pages/models/ModelDetail';
import ScoringList from './pages/scoring/ScoringList';
import SettingsPage from './pages/settings/SettingsPage';
import LoginPage from './pages/auth/LoginPage';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: 'tests', icon: <ExperimentOutlined />, label: <Link to="/tests">测试管理</Link> },
  { key: 'distillation', icon: <UserOutlined />, label: <Link to="/distillation">蒸馏管理</Link> },
  { key: 'models', icon: <RobotOutlined />, label: <Link to="/models">模型管理</Link> },
  { key: 'scoring', icon: <BarChartOutlined />, label: <Link to="/scoring">评分管理</Link> },
  { key: 'settings', icon: <SettingOutlined />, label: <Link to="/settings">系统配置</Link> },
];

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    message.success('已退出登录');
    navigate('/login');
  };

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  }

  const currentKey = location.pathname.split('/')[1] || 'tests';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" width={200}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 18, fontWeight: 'bold' }}>
          AI测试平台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[currentKey]}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 20, fontWeight: 'bold' }}>AI聊天模型测试平台</span>
          <Button icon={<LogoutOutlined />} onClick={handleLogout}>
            退出登录
          </Button>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', minHeight: 280 }}>
          <Routes>
            <Route path="/tests" element={<TestList />} />
            <Route path="/tests/:id" element={<TestDetail />} />
            <Route path="/distillation" element={<DistillationList />} />
            <Route path="/distillation/:id" element={<DistillationDetail />} />
            <Route path="/models" element={<ModelList />} />
            <Route path="/models/:id" element={<ModelDetail />} />
            <Route path="/scoring" element={<ScoringList />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/" element={<TestList />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={() => {}} />} />
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </Router>
  );
};

export default App;
