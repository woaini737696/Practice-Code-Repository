import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  ExperimentOutlined,
  UserOutlined,
  RobotOutlined,
  BarChartOutlined,
  SettingOutlined
} from '@ant-design/icons';
import TestList from './pages/tests/TestList';
import TestDetail from './pages/tests/TestDetail';
import DistillationList from './pages/distillation/DistillationList';
import DistillationDetail from './pages/distillation/DistillationDetail';
import ModelList from './pages/models/ModelList';
import ModelDetail from './pages/models/ModelDetail';
import ScoringList from './pages/scoring/ScoringList';
import SettingsPage from './pages/settings/SettingsPage';

const { Header, Sider, Content } = Layout;

const App: React.FC = () => {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider theme="dark" width={200}>
          <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 18, fontWeight: 'bold' }}>
            AI测试平台
          </div>
          <Menu theme="dark" mode="inline" defaultSelectedKeys={['tests']}>
            <Menu.Item key="tests" icon={<ExperimentOutlined />}>
              <Link to="/tests">测试管理</Link>
            </Menu.Item>
            <Menu.Item key="distillation" icon={<UserOutlined />}>
              <Link to="/distillation">蒸馏管理</Link>
            </Menu.Item>
            <Menu.Item key="models" icon={<RobotOutlined />}>
              <Link to="/models">模型管理</Link>
            </Menu.Item>
            <Menu.Item key="scoring" icon={<BarChartOutlined />}>
              <Link to="/scoring">评分管理</Link>
            </Menu.Item>
            <Menu.Item key="settings" icon={<SettingOutlined />}>
              <Link to="/settings">系统配置</Link>
            </Menu.Item>
          </Menu>
        </Sider>
        <Layout>
          <Header style={{ background: '#fff', padding: '0 24px', fontSize: 20, fontWeight: 'bold' }}>
            AI聊天模型测试平台
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
    </Router>
  );
};

export default App;
