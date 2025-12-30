import crypto from 'crypto';
import database from '../db/database.js';
import logger from '../utils/logger.js';

class UserService {
  /**
   * 生成API Key（sk-xxx格式）
   * @returns {string} API Key
   */
  generateApiKey() {
    const randomBytes = crypto.randomBytes(36);
    const key = randomBytes.toString('base64')
      .replace(/[+/=]/g, '')
      .substring(0, 48);
    return `sk-${key}`;
  }

  /**
   * 创建用户并生成API Key
   * @param {Object} userData - 用户数据
   * @param {string} userData.user_id - 用户ID（可选，不传则自动生成）
   * @param {string} userData.name - 用户名称（可选）
   * @returns {Promise<Object>} 创建的用户信息（包含api_key）
   */
  async createUser(userData = {}) {
    const user_id = userData.user_id || crypto.randomUUID();
    const api_key = this.generateApiKey();
    const name = userData.name || null;
    const prefer_shared = userData.prefer_shared || 0;

    try {
      const result = await database.query(
        `INSERT INTO users (user_id, api_key, name, prefer_shared, status)
         VALUES ($1, $2, $3, $4, 1)
         RETURNING *`,
        [user_id, api_key, name, prefer_shared]
      );

      logger.info(`用户创建成功: user_id=${user_id}, prefer_shared=${prefer_shared}`);
      return result.rows[0];
    } catch (error) {
      logger.error('创建用户失败:', error.message);
      throw error;
    }
  }

  /**
   * 更新用户Cookie优先级
   * @param {string} user_id - 用户ID
   * @param {number} prefer_shared - Cookie优先级（0=专属优先，1=共享优先）
   * @returns {Promise<Object>} 更新后的用户信息
   */
  async updateUserPreference(user_id, prefer_shared) {
    try {
      const result = await database.query(
        `UPDATE users
         SET prefer_shared = $1, updated_at = CURRENT_TIMESTAMP
         WHERE user_id = $2
         RETURNING *`,
        [prefer_shared, user_id]
      );

      if (result.rows.length === 0) {
        throw new Error(`用户不存在: user_id=${user_id}`);
      }

      logger.info(`用户优先级已更新: user_id=${user_id}, prefer_shared=${prefer_shared}`);
      return result.rows[0];
    } catch (error) {
      logger.error('更新用户优先级失败:', error.message);
      throw error;
    }
  }

  /**
   * 根据API Key获取用户
   * @param {string} api_key - API Key
   * @returns {Promise<Object|null>} 用户信息
   */
  async getUserByApiKey(api_key) {
    try {
      const result = await database.query(
        'SELECT * FROM users WHERE api_key = $1 AND status = 1',
        [api_key]
      );
      return result.rows[0] || null;
    } catch (error) {
      logger.error('根据API Key查询用户失败:', error.message);
      throw error;
    }
  }

  /**
   * 根据用户ID获取用户
   * @param {string} user_id - 用户ID
   * @returns {Promise<Object|null>} 用户信息
   */
  async getUserById(user_id) {
    try {
      const result = await database.query(
        'SELECT * FROM users WHERE user_id = $1',
        [user_id]
      );
      return result.rows[0] || null;
    } catch (error) {
      logger.error('根据ID查询用户失败:', error.message);
      throw error;
    }
  }

  /**
   * 验证API Key
   * @param {string} api_key - API Key
   * @returns {Promise<Object|null>} 用户信息（如果验证成功）或null
   */
  async validateApiKey(api_key) {
    if (!api_key || !api_key.startsWith('sk-')) {
      return null;
    }
    return await this.getUserByApiKey(api_key);
  }

  /**
   * 重新生成API Key
   * @param {string} user_id - 用户ID
   * @returns {Promise<Object>} 更新后的用户信息（包含新api_key）
   */
  async regenerateApiKey(user_id) {
    const new_api_key = this.generateApiKey();

    try {
      const result = await database.query(
        `UPDATE users 
         SET api_key = $1, updated_at = CURRENT_TIMESTAMP
         WHERE user_id = $2
         RETURNING *`,
        [new_api_key, user_id]
      );

      if (result.rows.length === 0) {
        throw new Error(`用户不存在: user_id=${user_id}`);
      }

      logger.info(`API Key已重新生成: user_id=${user_id}`);
      return result.rows[0];
    } catch (error) {
      logger.error('重新生成API Key失败:', error.message);
      throw error;
    }
  }

  /**
   * 更新用户状态
   * @param {string} user_id - 用户ID
   * @param {number} status - 状态 (0=禁用, 1=启用)
   * @returns {Promise<Object>} 更新后的用户信息
   */
  async updateUserStatus(user_id, status) {
    try {
      const result = await database.query(
        `UPDATE users 
         SET status = $1, updated_at = CURRENT_TIMESTAMP
         WHERE user_id = $2
         RETURNING *`,
        [status, user_id]
      );

      if (result.rows.length === 0) {
        throw new Error(`用户不存在: user_id=${user_id}`);
      }

      logger.info(`用户状态已更新: user_id=${user_id}, status=${status}`);
      return result.rows[0];
    } catch (error) {
      logger.error('更新用户状态失败:', error.message);
      throw error;
    }
  }

  /**
   * 删除用户
   * @param {string} user_id - 用户ID
   * @returns {Promise<boolean>} 是否删除成功
   */
  async deleteUser(user_id) {
    try {
      const result = await database.query(
        'DELETE FROM users WHERE user_id = $1',
        [user_id]
      );

      const deleted = result.rowCount > 0;
      if (deleted) {
        logger.info(`用户已删除: user_id=${user_id}`);
      } else {
        logger.warn(`用户不存在，无法删除: user_id=${user_id}`);
      }
      return deleted;
    } catch (error) {
      logger.error('删除用户失败:', error.message);
      throw error;
    }
  }

  /**
   * 获取所有用户列表
   * @returns {Promise<Array>} 用户列表
   */
  async getAllUsers() {
    try {
      const result = await database.query(
        'SELECT user_id, name, status, created_at, updated_at FROM users ORDER BY created_at DESC'
      );
      return result.rows;
    } catch (error) {
      logger.error('获取用户列表失败:', error.message);
      throw error;
    }
  }
}

const userService = new UserService();
export default userService;