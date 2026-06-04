export function errorHandler(err, req, res, next) {
  console.error('错误:', err);

  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ error: '无效的JSON格式' });
  }

  if (err.code === 'SQLITE_CONSTRAINT') {
    return res.status(400).json({ error: '数据已存在或违反约束' });
  }

  res.status(err.status || 500).json({
    error: err.message || '服务器内部错误',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
}
