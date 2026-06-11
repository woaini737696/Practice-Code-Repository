import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, InputNumber, message, Card, Tabs } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { scoringApi } from '../../services/api';

const { TabPane } = Tabs;
const { TextArea } = Input;

interface ScoreDimension {
  id: number;
  name: string;
  weight: number;
  description: string;
  scoring_criteria: string;
  sort_order: number;
  is_enabled: number;
}

interface Annotation {
  id: number;
  result_id: number;
  dimension_id: number;
  ai_score: number;
  human_score: number;
  comment: string;
}

const ScoringList: React.FC = () => {
  const [dimensions, setDimensions] = useState<ScoreDimension[]>([]);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(false);
  const [isDimModalVisible, setIsDimModalVisible] = useState(false);
  const [editingDimension, setEditingDimension] = useState<ScoreDimension | null>(null);
  const [dimForm] = Form.useForm();

  useEffect(() => {
    fetchDimensions();
    fetchAnnotations();
  }, []);

  const fetchDimensions = async () => {
    setLoading(true);
    try {
      const response = await scoringApi.listDimensions();
      setDimensions(response.data);
    } catch (error) {
      message.error('获取评分维度失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnnotations = async () => {
    try {
      const response = await scoringApi.listAnnotations();
      setAnnotations(response.data);
    } catch (error) {
      message.error('获取标注数据失败');
    }
  };

  const handleCreateDimension = async (values: any) => {
    try {
      if (editingDimension) {
        await scoringApi.updateDimension(editingDimension.id, values);
        message.success('更新成功');
      } else {
        await scoringApi.createDimension(values);
        message.success('创建成功');
      }
      setIsDimModalVisible(false);
      dimForm.resetFields();
      setEditingDimension(null);
      fetchDimensions();
    } catch (error) {
      message.error(editingDimension ? '更新失败' : '创建失败');
    }
  };

  const handleDeleteDimension = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，是否确认？',
      onOk: async () => {
        try {
          await scoringApi.deleteDimension(id);
          message.success('删除成功');
          fetchDimensions();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleEditDimension = (dimension: ScoreDimension) => {
    setEditingDimension(dimension);
    dimForm.setFieldsValue({
      name: dimension.name,
      weight: dimension.weight,
      description: dimension.description,
      scoring_criteria: dimension.scoring_criteria,
      sort_order: dimension.sort_order,
    });
    setIsDimModalVisible(true);
  };

  const dimensionColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '维度名称',
      dataIndex: 'name',
    },
    {
      title: '权重',
      dataIndex: 'weight',
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ScoreDimension) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEditDimension(record)}
          >
            编辑
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            size="small"
            onClick={() => handleDeleteDimension(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const annotationColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '结果ID',
      dataIndex: 'result_id',
    },
    {
      title: '维度ID',
      dataIndex: 'dimension_id',
    },
    {
      title: 'AI评分',
      dataIndex: 'ai_score',
    },
    {
      title: '人工评分',
      dataIndex: 'human_score',
    },
    {
      title: '备注',
      dataIndex: 'comment',
      ellipsis: true,
    },
  ];

  return (
    <div>
      <h2>评分管理</h2>

      <Tabs defaultActiveKey="dimensions">
        <TabPane tab="评分维度" key="dimensions">
          <div style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingDimension(null);
                dimForm.resetFields();
                setIsDimModalVisible(true);
              }}
            >
              添加维度
            </Button>
          </div>

          <Table
            columns={dimensionColumns}
            dataSource={dimensions}
            rowKey="id"
            loading={loading}
          />
        </TabPane>

        <TabPane tab="数据标注" key="annotations">
          <Card title="人工标注记录">
            <Table
              columns={annotationColumns}
              dataSource={annotations}
              rowKey="id"
              loading={loading}
            />
          </Card>
        </TabPane>
      </Tabs>

      <Modal
        title={editingDimension ? '编辑评分维度' : '添加评分维度'}
        visible={isDimModalVisible}
        onCancel={() => {
          setIsDimModalVisible(false);
          setEditingDimension(null);
          dimForm.resetFields();
        }}
        onOk={() => dimForm.submit()}
        width={600}
      >
        <Form form={dimForm} onFinish={handleCreateDimension} layout="vertical">
          <Form.Item
            name="name"
            label="维度名称"
            rules={[{ required: true, message: '请输入维度名称' }]}
          >
            <Input placeholder="例如：语言风格匹配度" />
          </Form.Item>

          <Form.Item
            name="weight"
            label="权重"
            rules={[{ required: true, message: '请输入权重' }]}
            initialValue={1.0}
          >
            <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={2} placeholder="维度描述" />
          </Form.Item>

          <Form.Item
            name="scoring_criteria"
            label="评分标准"
          >
            <TextArea rows={3} placeholder="评分标准说明" />
          </Form.Item>

          <Form.Item
            name="sort_order"
            label="排序"
            initialValue={0}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ScoringList;
