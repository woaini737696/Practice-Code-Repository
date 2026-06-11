import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Descriptions, Table, Tag, Progress, Collapse, message } from 'antd';
import { testApi } from '../../services/api';

const { Panel } = Collapse;

interface TestResult {
  id: number;
  model_name: string;
  user_name: string;
  total_score: number;
  scores: Record<string, { score: number; reason: string }>;
  conversation: Array<{ role: string; content: string }>;
}

interface TestDetail {
  id: number;
  name: string;
  status: string;
  progress: number;
  created_at: string;
  completed_at: string;
  results: TestResult[];
}

const TestDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [test, setTest] = useState<TestDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (id) {
      fetchTestDetail();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchTestDetail = async () => {
    setLoading(true);
    try {
      const response = await testApi.get(Number(id));
      setTest(response.data);
    } catch (error) {
      message.error('获取测试详情失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '待启动' },
      running: { color: 'processing', text: '进行中' },
      scoring: { color: 'warning', text: '评分中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' },
      cancelled: { color: 'default', text: '已取消' },
    };
    const config = statusMap[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const resultColumns = [
    {
      title: '模型',
      dataIndex: 'model_name',
    },
    {
      title: '用户',
      dataIndex: 'user_name',
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      render: (score: number) => (score ? score.toFixed(2) : 'N/A'),
    },
    {
      title: '各维度评分',
      dataIndex: 'scores',
      render: (scores: Record<string, { score: number }>) => {
        if (!scores) return 'N/A';
        return Object.entries(scores).map(([key, value]) => (
          <div key={key}>
            {key}: {value.score}/10
          </div>
        ));
      },
    },
    {
      title: '对话详情',
      key: 'conversation',
      render: (_: any, record: TestResult) => (
        <Collapse ghost>
          <Panel header="查看对话" key="1">
            {record.conversation?.map((msg, idx) => (
              <div key={idx} style={{ marginBottom: 8 }}>
                <Tag color={msg.role === 'user' ? 'blue' : 'green'}>
                  {msg.role === 'user' ? '用户' : 'AI'}
                </Tag>
                <span style={{ marginLeft: 8 }}>{msg.content}</span>
              </div>
            ))}
          </Panel>
        </Collapse>
      ),
    },
  ];

  if (!test) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <h2>测试详情</h2>

      <Card style={{ marginBottom: 24 }}>
        <Descriptions title="基本信息" bordered>
          <Descriptions.Item label="测试名称">{test.name}</Descriptions.Item>
          <Descriptions.Item label="测试ID">{test.id}</Descriptions.Item>
          <Descriptions.Item label="状态">{getStatusTag(test.status)}</Descriptions.Item>
          <Descriptions.Item label="进度">
            <Progress percent={test.progress} size="small" />
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(test.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {test.completed_at ? new Date(test.completed_at).toLocaleString() : '未完成'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="测试结果">
        <Table
          columns={resultColumns}
          dataSource={test.results}
          rowKey="id"
          loading={loading}
        />
      </Card>
    </div>
  );
};

export default TestDetailPage;
