import database from '../src/db/database.js';
import logger from '../src/utils/logger.js';
import fs from 'fs';

// 读取配置文件
let dbConfig;
try {
  const configFile = fs.readFileSync('./config.json', 'utf8');
  const configData = JSON.parse(configFile);
  dbConfig = configData.database;
} catch (error) {
  logger.error('读取配置文件失败:', error.message);
  process.exit(1);
}

/**
 * 修复缺失的共享配额记录
 */
async function fixMissingSharedQuotas() {
  try {
    // 初始化数据库连接
    database.initialize(dbConfig);
    logger.info('数据库连接已初始化');
    
    logger.info('开始检查缺失的共享配额记录...\n');
    
    // 查找有 claude-sonnet-4-5 但没有 claude-opus-4-5-thinking 的用户
    const query = `
      SELECT t1.user_id, t1.quota, t1.max_quota, t1.last_updated_at
      FROM user_shared_quota_pool t1
      LEFT JOIN user_shared_quota_pool t2 
        ON t1.user_id = t2.user_id AND t2.model_name = 'claude-opus-4-5-thinking'
      WHERE t1.model_name = 'claude-sonnet-4-5'
        AND t2.user_id IS NULL
    `;
    
    const result = await database.query(query);
    const usersToFix = result.rows;
    
    logger.info(`找到 ${usersToFix.length} 个需要修复的用户\n`);
    
    let fixedCount = 0;
    
    for (const user of usersToFix) {
      try {
        logger.info(`正在修复用户: ${user.user_id}`);
        
        // 插入缺失的记录
        await database.query(
          `INSERT INTO user_shared_quota_pool 
             (user_id, model_name, quota, max_quota, last_updated_at, last_recovered_at)
           VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)`,
          [user.user_id, 'claude-opus-4-5-thinking', user.quota, user.max_quota]
        );
        
        logger.info(`  ✓ 已添加 claude-opus-4-5-thinking 记录 (quota=${user.quota}, max=${user.max_quota})`);
        fixedCount++;
      } catch (error) {
        logger.error(`  ✗ 修复失败: ${error.message}`);
      }
    }
    
    logger.info('\n========== 修复完成 ==========');
    logger.info(`成功修复: ${fixedCount} 个用户`);
    logger.info('==============================\n');
    
  } catch (error) {
    logger.error('修复过程发生错误:', error.message);
    throw error;
  } finally {
    // 关闭数据库连接
    await database.close();
  }
}

// 运行脚本
fixMissingSharedQuotas()
  .then(() => {
    logger.info('\n脚本执行成功');
    process.exit(0);
  })
  .catch((error) => {
    logger.error('\n脚本执行失败:', error);
    process.exit(1);
  });