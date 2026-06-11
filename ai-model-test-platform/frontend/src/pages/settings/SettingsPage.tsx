import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, message, Switch, Tabs, Space } from 'antd';
import { SaveOutlined, MailOutlined, ExperimentOutlined, SettingOutlined } from '@ant-design/icons';
import { settingsApi } from '../../services/api';

const SettingsPage: React.FC = () => {
  const [emailForm] = Form.useForm();
  const [generalForm] = Form.useForm();
  const [emailConfigured, setEmailConfigured] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchEmailConfig();
    fetchGeneralSettings();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchEmailConfig = async () => {
    try {
      const response = await settingsApi.getEmailConfig();
      const config = response.data;
      setEmailConfigured(config.configured);
      emailForm.setFieldsValue({
        smtp_host: config.smtp_host,
        smtp_port: config.smtp_port,
        smtp_user: config.smtp_user,
        smtp_tls: config.smtp_tls,
      });
    } catch (error) {
      message.error('获取邮箱配置失败');
    }
  };

  const fetchGeneralSettings = async () => {
    try {
      const response = await settingsApi.list();
      const configs = response.data;
      const generalConfig: Record<string, string> = {};
      configs.forEach((config: any) => {
        generalConfig[config.config_key] = config.config_value;
      });
      generalForm.setFieldsValue(generalConfig);
    } catch (error) {
      message.error('获取通用配置失败');
    }
  };

  const handleSaveEmail = async (values: any) => {
    setLoading(true);
    try {
      await Promise.all([
        settingsApi.save({
          config_key: 'smtp_host',
          config_value: values.smtp_host,
          description: 'SMTP服务器地址',
        }),
        settingsApi.save({
          config_key: 'smtp_port',
          config_value: values.smtp_port.toString(),
          description: 'SMTP端口',
        }),
        settingsApi.save({
          config_key: 'smtp_user',
          config_value: values.smtp_user,
          description: 'SMTP用户名',
        }),
        settingsApi.save({
          config_key: 'smtp_password',
          config_value: values.smtp_password,
          description: 'SMTP密码',
        }),
        settingsApi.save({
          config_key: 'smtp_tls',
          config_value: values.smtp_tls ? 'true' : 'false',
          description: '是否启用TLS',
        }),
      ]);
      message.success('邮箱配置保存成功');
      setEmailConfigured(true);
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTestEmail = async () => {
    const values = emailForm.getFieldsValue();
    if (!values.smtp_user) {
      message.error('请先配置邮箱');
      return;
    }

    try {
      await settingsApi.testEmail(values.smtp_user);
      message.success('测试邮件已发送，请查收');
    } catch (error) {
      message.error('测试邮件发送失败');
    }
  };

  const handleSaveGeneral = async (values: any) => {
    setLoading(true);
    try {
      const promises = Object.entries(values).map(([key, value]) =>
        settingsApi.save({
          config_key: key,
          config_value: value as string,
        })
      );
      await Promise.all(promises);
      message.success('通用配置保存成功');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const tabItems = [
    {
      key: 'email',
      label: (
        <span>
          <MailOutlined />
          邮箱配置
        </span>
      ),
      children: (
        <Card>
          <Form form={emailForm} onFinish={handleSaveEmail} layout="vertical">
            <Form.Item
              name="smtp_host"
              label="SMTP服务器"
              rules={[{ required: true, message: '请输入SMTP服务器地址' }]}
            >
              <Input placeholder="例如：smtp.gmail.com" />
            </Form.Item>

            <Form.Item
              name="smtp_port"
              label="SMTP端口"
              rules={[{ required: true, message: '请输入SMTP端口' }]}
              initialValue={587}
            >
              <Input type="number" placeholder="例如：587" />
            </Form.Item>

            <Form.Item
              name="smtp_user"
              label="邮箱账号"
              rules={[{ required: true, message: '请输入邮箱账号' }]}
            >
              <Input placeholder="例如：your-email@gmail.com" />
            </Form.Item>

            <Form.Item
              name="smtp_password"
              label="邮箱密码/授权码"
              rules={[{ required: true, message: '请输入邮箱密码或授权码' }]}
            >
              <Input.Password placeholder="请输入密码或授权码" />
            </Form.Item>

            <Form.Item
              name="smtp_tls"
              label="启用TLS"
              valuePropName="checked"
              initialValue={true}
            >
              <Switch />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
                  保存配置
                </Button>
                <Button icon={<ExperimentOutlined />} onClick={handleTestEmail} disabled={!emailConfigured}>
                  发送测试邮件
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      ),
    },
    {
      key: 'general',
      label: (
        <span>
          <SettingOutlined />
          通用配置
        </span>
      ),
      children: (
        <Card>
          <Form form={generalForm} onFinish={handleSaveGeneral} layout="vertical">
            <Form.Item
              name="app_name"
              label="应用名称"
            >
              <Input placeholder="AI模型测试平台" />
            </Form.Item>

            <Form.Item
              name="default_llm_timeout"
              label="默认LLM超时时间（秒）"
            >
              <Input type="number" placeholder="30" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
                保存配置
              </Button>
            </Form.Item>
          </Form>
        </Card>
      ),
    },
  ];

  return (
    <div>
      <h2>系统配置</h2>
      <Tabs defaultActiveKey="email" items={tabItems} />
    </div>
  );
};

export default SettingsPage;
