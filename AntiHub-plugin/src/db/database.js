import pg from 'pg';
import logger from '../utils/logger.js';

const { Pool, types } = pg;

// 配置 pg 库将 TIMESTAMP 类型返回为 ISO 8601 格式的 UTC 时间字符串
// 添加 'Z' 后缀表示 UTC 时区,便于前端识别
types.setTypeParser(types.builtins.TIMESTAMP, (val) => {
  if (!val) return null;
  // PostgreSQL TIMESTAMP 格式可能是:
  // "2025-11-22 10:00:00" 或 "2025-11-22 10:00:00.123456"
  // 转换为 ISO 8601 UTC 格式: "2025-11-22T10:00:00.123Z"
  
  // 替换空格为 T
  let isoString = val.replace(' ', 'T');
  
  // 如果包含微秒,只保留毫秒(前3位)
  if (isoString.includes('.')) {
    const [datetime, microseconds] = isoString.split('.');
    const milliseconds = microseconds.substring(0, 3);
    isoString = `${datetime}.${milliseconds}Z`;
  } else {
    isoString += '.000Z';
  }
  
  return isoString;
});

types.setTypeParser(types.builtins.TIMESTAMPTZ, (val) => {
  if (!val) return null;
  // TIMESTAMPTZ 已包含时区信息,转换为 UTC ISO 8601 格式
  return new Date(val).toISOString();
});

class Database {
  constructor() {
    this.pool = null;
  }

  /**
   * 初始化数据库连接池
   * @param {Object} config - 数据库配置
   * @param {string} config.host - 数据库主机
   * @param {number} config.port - 数据库端口
   * @param {string} config.database - 数据库名称
   * @param {string} config.user - 数据库用户名
   * @param {string} config.password - 数据库密码
   */
  initialize(config) {
    if (this.pool) {
      logger.warn('数据库连接池已存在，将关闭旧连接池');
      this.pool.end();
    }

    this.pool = new Pool({
      host: config.host || 'localhost',
      port: config.port || 5432,
      database: config.database,
      user: config.user,
      password: config.password,
      max: config.max || 20,
      idleTimeoutMillis: config.idleTimeoutMillis || 30000,
      connectionTimeoutMillis: config.connectionTimeoutMillis || 2000,
      // 设置时区为UTC,确保时间格式一致
      options: '-c timezone=UTC',
    });

    this.pool.on('error', (err) => {
      logger.error('数据库连接池错误:', err.message);
    });

    logger.info(`数据库连接池已初始化: ${config.host}:${config.port}/${config.database}`);
  }

  /**
   * 执行SQL查询
   * @param {string} text - SQL查询语句
   * @param {Array} params - 查询参数
   * @returns {Promise<Object>} 查询结果
   */
  async query(text, params) {
    if (!this.pool) {
      throw new Error('数据库未初始化，请先调用 initialize() 方法');
    }

    try {
      const result = await this.pool.query(text, params);
      return result;
    } catch (error) {
      logger.error('SQL执行失败:', text, error.message);
      throw error;
    }
  }

  /**
   * 获取数据库客户端（用于事务）
   * @returns {Promise<Object>} 数据库客户端
   */
  async getClient() {
    if (!this.pool) {
      throw new Error('数据库未初始化，请先调用 initialize() 方法');
    }
    return await this.pool.connect();
  }

  /**
   * 关闭数据库连接池
   */
  async close() {
    if (this.pool) {
      await this.pool.end();
      this.pool = null;
      logger.info('数据库连接池已关闭');
    }
  }

  /**
   * 检查数据库连接
   */
  async ping() {
    try {
      await this.query('SELECT 1');
      return true;
    } catch (error) {
      logger.error('数据库连接检查失败:', error.message);
      return false;
    }
  }
}

// 导出单例
const database = new Database();
export default database;