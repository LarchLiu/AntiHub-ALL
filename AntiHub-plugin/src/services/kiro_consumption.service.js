import database from '../db/database.js';
import logger from '../utils/logger.js';

/**
 * Kiro消费日志服务
 */
class KiroConsumptionService {
  /**
   * 记录消费日志
   * @param {Object} params - 参数对象
   * @param {string} params.user_id - 用户ID
   * @param {string} params.account_id - 账号ID
   * @param {string} params.model_id - 模型ID
   * @param {number} params.credit_used - 消耗的credit
   * @param {number} params.is_shared - 是否共享账号 (0/1)
   */
  async logConsumption({ user_id, account_id, model_id, credit_used, is_shared }) {
    try {
      // 保留4位小数
      const roundedCredit = parseFloat(credit_used.toFixed(4));

      const query = `
        INSERT INTO kiro_consumption_log (user_id, account_id, model_id, credit_used, is_shared)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING log_id, consumed_at
      `;

      const result = await database.query(query, [
        user_id,
        account_id,
        model_id,
        roundedCredit,
        is_shared
      ]);

      logger.info(`Kiro消费日志已记录: user_id=${user_id}, account_id=${account_id}, model=${model_id}, credit=${roundedCredit}`);
      return result.rows[0];
    } catch (error) {
      logger.error('记录Kiro消费日志失败:', error.message);
      throw error;
    }
  }

  /**
   * 获取用户消费历史
   * @param {string} user_id - 用户ID
   * @param {Object} options - 查询选项
   * @param {number} options.limit - 限制数量
   * @param {number} options.offset - 偏移量
   */
  async getUserConsumption(user_id, { limit = 100, offset = 0 } = {}) {
    try {
      const query = `
        SELECT 
          l.log_id,
          l.account_id,
          l.model_id,
          l.credit_used,
          l.is_shared,
          l.consumed_at,
          a.account_name
        FROM kiro_consumption_log l
        LEFT JOIN kiro_accounts a ON l.account_id = a.account_id
        WHERE l.user_id = $1
        ORDER BY l.consumed_at DESC
        LIMIT $2 OFFSET $3
      `;

      const result = await database.query(query, [user_id, limit, offset]);
      return result.rows;
    } catch (error) {
      logger.error('获取用户消费历史失败:', error.message);
      throw error;
    }
  }

  /**
   * 获取账号消费统计
   * @param {string} account_id - 账号ID
   * @param {Object} options - 查询选项
   * @param {string} options.start_date - 开始日期
   * @param {string} options.end_date - 结束日期
   */
  async getAccountStats(account_id, { start_date, end_date } = {}) {
    try {
      let query = `
        SELECT 
          model_id,
          COUNT(*) as request_count,
          SUM(credit_used) as total_credit,
          AVG(credit_used) as avg_credit,
          MIN(credit_used) as min_credit,
          MAX(credit_used) as max_credit
        FROM kiro_consumption_log
        WHERE account_id = $1
      `;

      const params = [account_id];
      
      if (start_date) {
        params.push(start_date);query += ` AND consumed_at >= $${params.length}`;
      }
      
      if (end_date) {
        params.push(end_date);
        query += ` AND consumed_at <= $${params.length}`;
      }

      query += ` GROUP BY model_id ORDER BY total_credit DESC`;

      const result = await database.query(query, params);
      return result.rows;
    } catch (error) {
      logger.error('获取账号消费统计失败:', error.message);
      throw error;
    }
  }

  /**
   * 获取用户总消费统计
   * @param {string} user_id - 用户ID
   * @param {Object} options - 查询选项
   */
  async getUserTotalStats(user_id, { start_date, end_date } = {}) {
    try {
      let query = `
        SELECT 
          COUNT(*) as total_requests,
          SUM(credit_used) as total_credit,
          AVG(credit_used) as avg_credit,
          SUM(CASE WHEN is_shared = 1 THEN credit_used ELSE 0 END) as shared_credit,
          SUM(CASE WHEN is_shared = 0 THEN credit_used ELSE 0 END) as private_credit
        FROM kiro_consumption_log
        WHERE user_id = $1
      `;

      const params = [user_id];
      
      if (start_date) {
        params.push(start_date);
        query += ` AND consumed_at >= $${params.length}`;
      }
      
      if (end_date) {
        params.push(end_date);
        query += ` AND consumed_at <= $${params.length}`;
      }

      const result = await database.query(query, params);
      return result.rows[0];
    } catch (error) {
      logger.error('获取用户总消费统计失败:', error.message);
      throw error;
    }
  }
}

const kiroConsumptionService = new KiroConsumptionService();
export default kiroConsumptionService;