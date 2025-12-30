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

const MODEL_NAME = 'gemini-2.5-flash-image';

/**
 * 移除 gemini-2.5-flash-image 相关的所有数据
 */
async function removeGeminiFlashImageData() {
  try {
    // 初始化数据库连接
    database.initialize(dbConfig);
    logger.info('数据库连接已初始化');
    
    logger.info(`开始移除 ${MODEL_NAME} 相关数据...\n`);
    
    // 1. 查询并删除 model_quotas 表中的数据
    logger.info('1. 处理 model_quotas 表...');
    const quotasCountResult = await database.query(
      'SELECT COUNT(*) as count FROM model_quotas WHERE model_name = $1',
      [MODEL_NAME]
    );
    const quotasCount = parseInt(quotasCountResult.rows[0].count);
    logger.info(`   找到 ${quotasCount} 条记录`);
    
    if (quotasCount > 0) {
      const deleteQuotasResult = await database.query(
        'DELETE FROM model_quotas WHERE model_name = $1',
        [MODEL_NAME]
      );
      logger.info(`   ✓ 已删除 ${deleteQuotasResult.rowCount} 条记录`);
    } else {
      logger.info('   无需删除');
    }
    
    // 2. 查询并删除 user_shared_quota_pool 表中的数据
    logger.info('\n2. 处理 user_shared_quota_pool 表...');
    const poolCountResult = await database.query(
      'SELECT COUNT(*) as count FROM user_shared_quota_pool WHERE model_name = $1',
      [MODEL_NAME]
    );
    const poolCount = parseInt(poolCountResult.rows[0].count);
    logger.info(`   找到 ${poolCount} 条记录`);
    
    if (poolCount > 0) {
      const deletePoolResult = await database.query(
        'DELETE FROM user_shared_quota_pool WHERE model_name = $1',
        [MODEL_NAME]
      );
      logger.info(`   ✓ 已删除 ${deletePoolResult.rowCount} 条记录`);
    } else {
      logger.info('   无需删除');
    }
    
    // 汇总
    logger.info('\n========== 清理完成 ==========');
    logger.info(`model_quotas: 删除 ${quotasCount} 条`);
    logger.info(`user_shared_quota_pool: 删除 ${poolCount} 条`);
    logger.info(`总计: ${quotasCount + poolCount} 条记录`);
    logger.info('==============================\n');
    
  } catch (error) {
    logger.error('清理数据失败:', error.message);
    throw error;
  } finally {
    // 关闭数据库连接
    await database.close();
  }
}

// 运行脚本
removeGeminiFlashImageData()
  .then(() => {
    logger.info('脚本执行成功');
    process.exit(0);
  })
  .catch((error) => {
    logger.error('脚本执行失败:', error);
    process.exit(1);
  });