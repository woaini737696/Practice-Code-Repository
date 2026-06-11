import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || `http://${window.location.hostname}:8000`;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器，自动添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器，处理401错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 测试管理API
export const testApi = {
  list: (params?: any) => api.get('/api/tests', { params }),
  create: (data: any) => api.post('/api/tests', data),
  get: (id: number) => api.get(`/api/tests/${id}`),
  start: (id: number) => api.post(`/api/tests/${id}/start`),
  cancel: (id: number) => api.post(`/api/tests/${id}/cancel`),
  delete: (id: number) => api.delete(`/api/tests/${id}`),
  report: (id: number, format: string) => api.get(`/api/tests/${id}/report?format=${format}`, { responseType: 'blob' }),
};

// 蒸馏管理API
export const distillationApi = {
  list: () => api.get('/api/distillation/users'),
  create: (data: any) => api.post('/api/distillation/users', data),
  get: (id: number) => api.get(`/api/distillation/users/${id}`),
  delete: (id: number) => api.delete(`/api/distillation/users/${id}`),
  upload: (file: File, userName?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (userName) formData.append('user_name', userName);
    return api.post('/api/distillation/users/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// 模型管理API
export const modelApi = {
  list: () => api.get('/api/models'),
  create: (data: any) => api.post('/api/models', data),
  get: (id: number) => api.get(`/api/models/${id}`),
  update: (id: number, data: any) => api.put(`/api/models/${id}`, data),
  delete: (id: number) => api.delete(`/api/models/${id}`),
  toggle: (id: number) => api.post(`/api/models/${id}/toggle`),
};

// 评分管理API
export const scoringApi = {
  listDimensions: () => api.get('/api/scoring/dimensions'),
  createDimension: (data: any) => api.post('/api/scoring/dimensions', data),
  updateDimension: (id: number, data: any) => api.put(`/api/scoring/dimensions/${id}`, data),
  deleteDimension: (id: number) => api.delete(`/api/scoring/dimensions/${id}`),
  listAnnotations: (resultId?: number) => api.get('/api/scoring/annotations', { params: { result_id: resultId } }),
  createAnnotation: (data: any) => api.post('/api/scoring/annotations', data),
};

// 系统配置API
export const settingsApi = {
  list: () => api.get('/api/settings'),
  get: (key: string) => api.get(`/api/settings/${key}`),
  save: (data: any) => api.post('/api/settings', data),
  delete: (key: string) => api.delete(`/api/settings/${key}`),
  getEmailConfig: () => api.get('/api/settings/email/config'),
  testEmail: (toEmail: string) => api.post(`/api/settings/email/test?to_email=${toEmail}`),
};

export default api;
