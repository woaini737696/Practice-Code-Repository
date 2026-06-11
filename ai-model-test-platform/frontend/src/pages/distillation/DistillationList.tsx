import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Button, Space, Modal, Form, Input, Upload, message } from 'antd';
import { PlusOutlined, UploadOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons';
import { distillationApi } from '../../services/api';

interface DistilledUser {
  id: number;
  name: string;
  source_file: string;
  message_count: number;
  status: number;
  created_at: string;
}

const DistillationList: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<DistilledUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isUploadModalVisible, setIsUploadModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [uploadForm] = Form.useForm();
  const [fileList, setFileList] = useState<any[]>([]);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await distillationApi.list();
      setUsers(response.data);
    } catch (error) {
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      await distillationApi.create({
        name: values.name,
        chat_records: [],
      });
      message.success('创建成功');
      setIsModalVisible(false);
      form.resetFields();
      fetchUsers();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const handleUpload = async (values: any) => {
    if (fileList.length === 0) {
      message.error('请选择文件');
      return;
    }

    try {
      const file = fileList[0].originFileObj;
      await distillationApi.upload(file, values.user_name);
      message.success('上传成功');
      setIsUploadModalVisible(false);
      uploadForm.resetFields();
      setFileList([]);
      fetchUsers();
    } catch (error) {
      message.error('上传失败');
    }
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，是否确认？',
      onOk: async () => {
        try {
          await distillationApi.delete(id);
          message.success('删除成功');
          fetchUsers();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '用户名称',
      dataIndex: 'name',
    },
    {
      title: '源文件',
      dataIndex: 'source_file',
      render: (file: string) => file || '手动创建',
    },
    {
      title: '消息数量',
      dataIndex: 'message_count',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: DistilledUser) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={() => navigate(`/distillation/${record.id}`)}
          >
            详情
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
        <h2>蒸馏管理</h2>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
            手动创建
          </Button>
          <Button icon={<UploadOutlined />} onClick={() => setIsUploadModalVisible(true)}>
            上传记录
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
      />

      {/* 手动创建模态框 */}
      <Modal
        title="创建蒸馏用户"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item
            name="name"
            label="用户名称"
            rules={[{ required: true, message: '请输入用户名称' }]}
          >
            <Input placeholder="请输入用户名称" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 上传模态框 */}
      <Modal
        title="上传聊天记录"
        visible={isUploadModalVisible}
        onCancel={() => setIsUploadModalVisible(false)}
        onOk={() => uploadForm.submit()}
      >
        <Form form={uploadForm} onFinish={handleUpload} layout="vertical">
          <Form.Item
            name="user_name"
            label="用户名称（可选）"
          >
            <Input placeholder="留空将使用文件名" />
          </Form.Item>
          <Form.Item label="聊天记录文件">
            <Upload
              fileList={fileList}
              onChange={({ fileList }) => setFileList(fileList)}
              beforeUpload={() => false}
              accept=".xlsx,.xls,.csv"
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DistillationList;
