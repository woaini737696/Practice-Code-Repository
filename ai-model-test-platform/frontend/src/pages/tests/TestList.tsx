import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Button, Space, Tag, Progress, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined, PlayCircleOutlined, EyeOutlined, DeleteOutlined, DownloadOutlined } from '@ant-design/icons';
import { testApi, distillationApi, modelApi } from '../../services/api';
import { wsService } from '../../services/websocket';

const { Option } = Select;

interface Test {
  id: number;
  name: string;
  status: string;
  progress: number;
  user_ids: number[];
  model_ids: number[];
  created_at: string;
}

const TestList: React.FC = () => {
  const navigate = useNavigate();
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchTests();
    fetchUsersAndModels();
    wsService.connect();

    // 订阅测试进度
    const unsubscribe = wsService.onTestProgress((data) => {
      setTests((prev) =>
        prev.map((test) =>
          test.id === data.test_id
            ? { ...test, progress: data.progress, status: data.status }
            : test
        )
      );
    });

    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, []);

  const fetchTests = async () => {
    setLoading(true);
    try {
      const response = await testApi.list();
      setTests(response.data);
    } catch (error) {
      message.error('获取测试列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsersAndModels = async () => {
    try {
      const [usersRes, modelsRes] = await Promise.all([
        distillationApi.list(),
        modelApi.list(),
      ]);
      setUsers(usersRes.data);
      setModels(modelsRes.data.filter((m: any) => m.is_enabled === 1));
    } catch (error) {
      message.error('获取数据失败');
    }
  };

  const handleCreate = async (values: any) => {
    try {
      await testApi.create({
        name: values.name,
        user_ids: values.user_ids,
        model_ids: values.model_ids,
        config: {},
      });
      message.success('创建成功');
      setIsModalVisible(false);
      form.resetFields();
      fetchTests();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const handleStart = async (id: number) => {
    try {
      await testApi.start(id);
      message.success('测试已启动');
      fetchTests();
    } catch (error) {
      message.error('启动失败');
    }
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，是否确认？',
      onOk: async () => {
        try {
          await testApi.delete(id);
          message.success('删除成功');
          fetchTests();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleDownloadReport = async (id: number, format: string) => {
    try {
      const response = await testApi.report(id, format);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `test_report_${id}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      message.error('下载失败');
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

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '测试名称',
      dataIndex: 'name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      render: (progress: number, record: Test) =>
        record.status === 'running' ? (
          <Progress percent={progress} size="small" status="active" />
        ) : (
          <Progress percent={progress} size="small" />
        ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Test) => (
        <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            size="small"
            disabled={record.status !== 'pending' && record.status !== 'failed'}
            onClick={() => handleStart(record.id)}
          >
            启动
          </Button>
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={() => navigate(`/tests/${record.id}`)}
          >
            详情
          </Button>
          <Button
            icon={<DownloadOutlined />}
            size="small"
            disabled={record.status !== 'completed'}
            onClick={() => handleDownloadReport(record.id, 'pdf')}
          >
            PDF
          </Button>
          <Button
            icon={<DownloadOutlined />}
            size="small"
            disabled={record.status !== 'completed'}
            onClick={() => handleDownloadReport(record.id, 'excel')}
          >
            Excel
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            size="small"
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>测试管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
          创建测试
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={tests}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="创建测试"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item
            name="name"
            label="测试名称"
            rules={[{ required: true, message: '请输入测试名称' }]}
          >
            <Input placeholder="请输入测试名称" />
          </Form.Item>

          <Form.Item
            name="user_ids"
            label="选择蒸馏用户"
            rules={[{ required: true, message: '请选择至少一个用户' }]}
          >
            <Select mode="multiple" placeholder="请选择用户">
              {users.map((user) => (
                <Option key={user.id} value={user.id}>
                  {user.name} ({user.message_count}条记录)
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="model_ids"
            label="选择对比模型"
            rules={[{ required: true, message: '请选择至少一个模型' }]}
          >
            <Select mode="multiple" placeholder="请选择模型">
              {models.map((model) => (
                <Option key={model.id} value={model.id}>
                  {model.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TestList;
