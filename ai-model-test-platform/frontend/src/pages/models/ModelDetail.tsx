import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Descriptions, Tag, message } from 'antd';
import { modelApi } from '../../services/api';

interface AIModelDetail {
  id: number;
  name: string;
  base_url: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
  timeout: number;
  is_enabled: number;
  created_at: string;
}

const ModelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [model, setModel] = useState<AIModelDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (id) {
      fetchModelDetail();
    }
  }, [id]);

  const fetchModelDetail = async () => {
    setLoading(true);
    try {
      const response = await modelApi.get(Number(id));
      setModel(response.data);
    } catch (error) {
      message.error('获取模型详情失败');
    } finally {
      setLoading(false);
    }
  };

  if (!model) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <h2>模型详情</h2>

      <Card loading={loading}>
        <Descriptions title="基本信息" bordered column={2}>
          <Descriptions.Item label="模型名称">{model.name}</Descriptions.Item>
          <Descriptions.Item label="模型ID">{model.id}</Descriptions.Item>
          <Descriptions.Item label="Base URL">{model.base_url}</Descriptions.Item>
          <Descriptions.Item label="模型名称">{model.model_name}</Descriptions.Item>
          <Descriptions.Item label="Temperature">{model.temperature}</Descriptions.Item>
          <Descriptions.Item label="Max Tokens">{model.max_tokens}</Descriptions.Item>
          <Descriptions.Item label="超时时间">{model.timeout}秒</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={model.is_enabled === 1 ? 'success' : 'default'}>
              {model.is_enabled === 1 ? '启用' : '禁用'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间" span={2}>
            {new Date(model.created_at).toLocaleString()}
          </Descriptions.Item>
          {model.system_prompt && (
            <Descriptions.Item label="System Prompt" span={2}>
              <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                {model.system_prompt}
              </pre>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>
    </div>
  );
};

export default ModelDetail;
