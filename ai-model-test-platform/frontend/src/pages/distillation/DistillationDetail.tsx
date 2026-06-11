import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Descriptions, Table, Tag, message } from 'antd';
import { distillationApi } from '../../services/api';

interface ChatRecord {
  role: string;
  content: string;
  timestamp: string;
}

interface DistilledUserDetail {
  id: number;
  name: string;
  source_file: string;
  message_count: number;
  status: number;
  created_at: string;
  chat_records: ChatRecord[];
}

const DistillationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [user, setUser] = useState<DistilledUserDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (id) {
      fetchUserDetail();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchUserDetail = async () => {
    setLoading(true);
    try {
      const response = await distillationApi.get(Number(id));
      setUser(response.data);
    } catch (error) {
      message.error('获取用户详情失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '角色',
      dataIndex: 'role',
      width: 100,
      render: (role: string) => (
        <Tag color={role === 'user' ? 'blue' : 'green'}>
          {role === 'user' ? '用户' : '助手'}
        </Tag>
      ),
    },
    {
      title: '内容',
      dataIndex: 'content',
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      width: 180,
      render: (timestamp: string) =>
        timestamp ? new Date(timestamp).toLocaleString() : '-',
    },
  ];

  if (!user) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <h2>蒸馏用户详情</h2>

      <Card style={{ marginBottom: 24 }}>
        <Descriptions title="基本信息" bordered>
          <Descriptions.Item label="用户名称">{user.name}</Descriptions.Item>
          <Descriptions.Item label="用户ID">{user.id}</Descriptions.Item>
          <Descriptions.Item label="源文件">{user.source_file || '手动创建'}</Descriptions.Item>
          <Descriptions.Item label="消息数量">{user.message_count}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={user.status === 1 ? 'success' : 'default'}>
              {user.status === 1 ? '启用' : '禁用'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(user.created_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="聊天记录">
        <Table
          columns={columns}
          dataSource={user.chat_records}
          rowKey={(record, index) => `${record.role}-${index}`}
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default DistillationDetail;
