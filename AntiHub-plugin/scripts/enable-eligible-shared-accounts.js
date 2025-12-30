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
 * 启用符合资格的共享账号
 * 条件：is_shared = 1 且 (paid_tier = true 或 project_id_0 不为空)
 */
async function enableEligibleSharedAccounts() {
  try {
    // 初始化数据库连接
    database.initialize(dbConfig);
    logger.info('数据库连接已初始化');
    
    logger.info('开始检查符合资格的共享账号...\n');
    
    // 查询所有共享账号（包括禁用的）
    const allSharedResult = await database.query(
      `SELECT cookie_id, user_id, name, status, paid_tier, project_id_0, is_restricted, ineligible
       FROM accounts 
       WHERE is_shared = 1 
       ORDER BY created_at ASC`
    );
    
    const allSharedAccounts = allSharedResult.rows;
    logger.info(`找到 ${allSharedAccounts.length} 个共享账号\n`);
    
    // 查询符合资格但当前禁用的共享账号
    const eligibleDisabledResult = await database.query(
      `SELECT cookie_id, user_id, name, status, paid_tier, project_id_0, is_restricted, ineligible
       FROM accounts 
       WHERE is_shared = 1 
         AND status = 0
         AND (paid_tier = true OR (project_id_0 IS NOT NULL AND project_id_0 != ''))
       ORDER BY created_at ASC`
    );
    
    const eligibleDisabledAccounts = eligibleDisabledResult.rows;
    
    // 显示所有共享账号状态
    logger.info('========== 所有共享账号状态 ==========');
    for (const account of allSharedAccounts) {
      const statusText = account.status === 1 ? '✓ 启用' : '✗ 禁用';
      const paidText = account.paid_tier ? '付费' : '免费';
      const projectText = account.project_id_0 ? `有(${account.project_id_0.substring(0, 20)}...)` : '无';
      const restrictedText = account.is_restricted ? '受限' : '不受限';
      const ineligibleText = account.ineligible ? '不合格' : '合格';
      const eligible = account.paid_tier || (account.project_id_0 && account.project_id_0 !== '');
      const eligibleText = eligible ? '符合资格' : '不符合资格';
      
      logger.info(`  ${account.cookie_id.substring(0, 20)}...`);
      logger.info(`    名称: ${account.name || '(未设置)'}`);
      logger.info(`    状态: ${statusText} | ${paidText} | project_id: ${projectText}`);
      logger.info(`    地区: ${restrictedText} | 账号: ${ineligibleText} | ${eligibleText}`);
      logger.info('');
    }
    
    if (eligibleDisabledAccounts.length === 0) {
      logger.info('没有需要启用的符合资格的共享账号');
      return;
    }
    
    logger.info(`\n========== 将要启用的账号 (${eligibleDisabledAccounts.length} 个) ==========`);
    for (const account of eligibleDisabledAccounts) {
      const paidText = account.paid_tier ? '付费' : '免费';
      const projectText = account.project_id_0 ? `有` : '无';
      logger.info(`  - ${account.cookie_id.substring(0, 30)}... (${account.name || '未命名'}) [${paidText}, project_id: ${projectText}]`);
    }
    
    // 执行启用操作
    logger.info('\n正在启用账号...');
    
    const updateResult = await database.query(
      `UPDATE accounts 
       SET status = 1, updated_at = CURRENT_TIMESTAMP
       WHERE is_shared = 1 
         AND status = 0
         AND (paid_tier = true OR (project_id_0 IS NOT NULL AND project_id_0 != ''))
       RETURNING cookie_id, name`
    );
    
    const enabledAccounts = updateResult.rows;
    
    logger.info('\n========== 启用完成 ==========');
    logger.info(`成功启用 ${enabledAccounts.length} 个共享账号:`);
    for (const account of enabledAccounts) {
      logger.info(`  ✓ ${account.cookie_id.substring(0, 30)}... (${account.name || '未命名'})`);
    }
    logger.info('==============================\n');
    
  } catch (error) {
    logger.error('启用账号失败:', error.message);
    throw error;
  } finally {
    // 关闭数据库连接
    await database.close();
  }
}

// 运行脚本
enableEligibleSharedAccounts()
  .then(() => {
    logger.info('脚本执行成功');
    process.exit(0);
  })
  .catch((error) => {
    logger.error('脚本执行失败:', error);
    process.exit(1);
  });