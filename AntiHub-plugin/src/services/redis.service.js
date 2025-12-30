import Redis from 'ioredis';
import config from '../config/config.js';
import logger from '../utils/logger.js';

/**
 * Redis服务
 * 用于存储Kiro OAuth状态等临时数据
 */
class RedisService {
  constructor() {
    this.client = null;
    this.connected = false;
  }

  /**
   * 初始化Redis连接
   */
  async init() {
    if (this.client) {
      return;
    }

    const redisConfig = config.redis || {};
    
    try {
      this.client = new Redis({
        host: redisConfig.host || 'localhost',
        port: redisConfig.port || 6379,
        password: redisConfig.password || undefined,
        db: redisConfig.db || 0,
        retryStrategy: (times) => {
          if (times > 3) {
            logger.error('Redis连接失败，已重试3次');
            return null;
          }
          return Math.min(times * 200, 2000);
        }
      });

      this.client.on('connect', () => {
        this.connected = true;
        logger.info('Redis连接成功');
      });

      this.client.on('error', (err) => {
        this.connected = false;
        logger.error('Redis错误:', err.message);
      });

      this.client.on('close', () => {
        this.connected = false;
        logger.warn('Redis连接已关闭');
      });

      // 等待连接
      await new Promise((resolve, reject) => {
        this.client.once('ready', resolve);
        this.client.once('error', reject);
      });

    } catch (error) {
      logger.error('Redis初始化失败:', error.message);
      throw error;
    }
  }

  /**
   * 检查Redis是否可用
   */
  isAvailable() {
    return this.connected && this.client;
  }

  /**
   * 设置键值（带过期时间）
   * @param {string} key - 键
   * @param {any} value - 值（会被JSON序列化）
   * @param {number} ttl - 过期时间（秒）
   */
  async set(key, value, ttl = 600) {
    if (!this.isAvailable()) {
      throw new Error('Redis不可用');
    }
    const serialized = JSON.stringify(value);
    await this.client.setex(key, ttl, serialized);
  }

  /**
   * 获取键值
   * @param {string} key - 键
   * @returns {any} 值（已反序列化）
   */
  async get(key) {
    if (!this.isAvailable()) {
      throw new Error('Redis不可用');
    }
    const value = await this.client.get(key);
    if (value === null) {
      return null;
    }
    return JSON.parse(value);
  }

  /**
   * 删除键
   * @param {string} key - 键
   */
  async del(key) {
    if (!this.isAvailable()) {
      throw new Error('Redis不可用');
    }
    await this.client.del(key);
  }

  /**
   * 关闭连接
   */
  async close() {
    if (this.client) {
      await this.client.quit();
      this.client = null;
      this.connected = false;
    }
  }
}

const redisService = new RedisService();
export default redisService;