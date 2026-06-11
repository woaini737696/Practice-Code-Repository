import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Button, Space, Modal, Form, Input, InputNumber, Switch, message } from 'antd';
import { PlusOutlined, EyeOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { modelApi } from '../../services/api';

interface AIModel {
  id: number;
  name: string;
  base_url: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
  is_enabled: number;
  created_at: string;
}

const ModelList: React.FC = () => {
  const navigate = useNavigate();
  const [models, setModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingModel, setEditingModel] = useState<AIModel | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    setLoading(true);
    try {
      const response = await modelApi.list();
      setModels(response.data);
    } catch (error) {
      message.error('获取模型列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      if (editingModel) {
        await modelApi.update(editingModel.id, values);
        message.success('更新成功');
      } else {
        await modelApi.create(values);
        message.success('创建成功');
      }
      setIsModalVisible(false);
      form.resetFields();
      setEditingModel(null);
      fetchModels();
    } catch (error) {
      message.error(editingModel ? '更新失败' : '创建失败');
    }
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，是否确认？',
      onOk: async () => {
        try {
          await modelApi.delete(id);
          message.success('删除成功');
          fetchModels();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleEdit = (model: AIModel) => {
    setEditingModel(model);
    form.setFieldsValue({
      name: model.name,
      base_url: model.base_url,
      api_key: '',
      model_name: model.model_name,
      temperature: model.temperature,
      max_tokens: model.max_tokens,
      system_prompt: model.system_prompt,
      timeout: model.timeout,
    });
    setIsModalVisible(true);
  };

  const handleToggle = async (id: number) => {
    try {
      await modelApi.toggle(id);
      message.success('状态更新成功');
      fetchModels();
    } catch (error) {
      message.error('状态更新失败');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '模型名称',
      dataIndex: 'name',
    },
    {
      title: 'Base URL',
      dataIndex: 'base_url',
      ellipsis: true,
    },
    {
      title: '模型ID',
      dataIndex: 'model_name',
    },
    {
      title: 'Temperature',
      dataIndex: 'temperature',
    },
    {
      title: 'Max Tokens',
      dataIndex: 'max_tokens',
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      render: (is_enabled: number, record: AIModel) => (
        <Switch
          checked={is_enabled === 1}
          onChange={() => handleToggle(record.id)}
        />
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
      render: (_: any, record: AIModel) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={() => navigate(`/models/${record.id}`)}
          >
            详情
          </Button>
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEdit(record)}
          >
            编辑
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
        <h2>模型管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingModel(null);
            form.resetFields();
            setIsModalVisible(true);
          }}
        >
          添加模型
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={models}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingModel ? '编辑模型' : '添加模型'}
        visible={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingModel(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item
            name="name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="例如：GPT-4" />
          </Form.Item>

          <Form.Item
            name="base_url"
            label="Base URL"
            rules={[{ required: true, message: '请输入Base URL' }]}
          >
            <Input placeholder="例如：https://api.openai.com/v1" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: !editingModel, message: '请输入API Key' }]}
          >
            <Input.Password placeholder="sk-..." />
          </Form.Item>

          <Form.Item
            name="model_name"
            label="模型ID"
            rules={[{ required: true, message: '请输入模型ID' }]}
          >
            <Input placeholder="例如：gpt-4" />
          </Form.Item>

          <Form.Item
            name="temperature"
            label="Temperature"
            initialValue={0.7}
          >
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="max_tokens"
            label="Max Tokens"
            initialValue={2048}
          >
            <InputNumber min={1} max={32768} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="system_prompt"
            label="System Prompt"
          >
            <Input.TextArea rows={3} placeholder="可选：自定义系统提示词" />
          </Form.Item>

          <Form.Item
            name="timeout"
            label="超时时间（秒）"
            initialValue={30}
          >
            <InputNumber min={1} max={300} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ModelList;
