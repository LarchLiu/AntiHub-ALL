#!/usr/bin/env node

/**
 * Kiro账号信息更新脚本
 * 
 * 功能：
 * 1. 遍历所有启用的Kiro账号
 * 2. 刷新token（如果过期）
 * 3. 从上游API获取最新的使用量信息
 * 4. 更新数据库中的账号信息（包括bonus）
 * 
 * 使用方法：
 *   node scripts/update-kiro-accounts.js
 *   node scripts/update-kiro-accounts.js --account-id <account_id>  # 只更新指定账号
 *   node scripts/update-kiro-accounts.js --user-id <user_id>        # 只更新指定用户的账号
 */

import database from '../src/db/database.js';
import kiroService from '../src/services/kiro.service.js';
import kiroAccountService from '../src/services/kiro_account.service.js';
import logger from '../src/utils/logger.js';

// 解析命令行参数
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    accountId: null,
    userId: null
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--account-id' && args[i + 1]) {
      options.accountId = args[i + 1];
      i++;
    } else if (args[i] === '--user-id' && args[i + 1]) {
      options.userId = args[i + 1];
      i++;
    }
  }

  return options;
}

/**
 * 更新单个账号信息
 * @param {Object} account - 账号对象
 * @returns {Promise<Object>} 更新结果
 */
async function updateAccount(account) {
  const result = {
    account_id: account.account_id,
    email: account.email,
    success: false,
    error: null,
    old_balance: null,
    new_balance: null
  };

  try {
    // 计算旧的余额
    const oldBalance = kiroAccountService.calculateAvailableBalance(account);
    result.old_balance = {
      available: oldBalance.available,
      base_available: oldBalance.base_available,
      bonus_available: oldBalance.bonus_available
    };

    // 检查token是否过期，如果过期则刷新
    let accessToken = account.access_token;
    if (kiroAccountService.isTokenExpired(account)) {
      logger.info(`[${account.account_id}] Token已过期，正在刷新...`);
      
      try {
        const tokenData = await kiroService.refreshToken({
          machineid: account.machineid,
          auth: account.auth_method,
          refreshToken: account.refresh_token,
          clientId: account.client_id,
          clientSecret: account.client_secret
        });
        
        const expires_at = Date.now() + (tokenData.expires_in * 1000);
        await kiroAccountService.updateAccountToken(
          account.account_id,
          tokenData.access_token,
          expires_at,
          tokenData.profile_arn
        );
        
        accessToken = tokenData.access_token;
        logger.info(`[${account.account_id}] Token刷新成功`);
      } catch (refreshError) {
        // 刷新token失败，标记账号需要重新授权
        logger.error(`[${account.account_id}] Token刷新失败: ${refreshError.message}`);
        await kiroAccountService.markAccountNeedRefresh(account.account_id);
        result.error = `Token刷新失败: ${refreshError.message}`;
        return result;
      }
    }

    // 获取最新的使用量信息
    logger.info(`[${account.account_id}] 获取使用量信息...`);
    const usageLimitsData = await kiroService.getUsageLimits(
      accessToken,
      account.profile_arn,
      account.machineid
    );

    // 更新数据库
    const updatedAccount = await kiroAccountService.updateAccountUsage(account.account_id, {
      email: usageLimitsData.email,
      userid: usageLimitsData.userid,
      subscription: usageLimitsData.subscription,
      current_usage: usageLimitsData.current_usage,
      reset_date: usageLimitsData.reset_date,
      usage_limit: usageLimitsData.usage_limit,
      bonus_usage: usageLimitsData.bonus_usage,
      bonus_limit: usageLimitsData.bonus_limit,
      bonus_available: usageLimitsData.bonus_available,
      bonus_details: usageLimitsData.bonus_details
    });

    // 计算新的余额
    const newBalance = kiroAccountService.calculateAvailableBalance(updatedAccount);
    result.new_balance = {
      available: newBalance.available,
      base_available: newBalance.base_available,
      bonus_available: newBalance.bonus_available
    };

    result.success = true;
    logger.info(`[${account.account_id}] 更新成功: 可用额度 ${result.old_balance.available.toFixed(2)} -> ${result.new_balance.available.toFixed(2)}`);

  } catch (error) {
    result.error = error.message;
    logger.error(`[${account.account_id}] 更新失败: ${error.message}`);
  }

  return result;
}

/**
 * 主函数
 */
async function main() {
  const options = parseArgs();
  
  console.log('========================================');
  console.log('Kiro账号信息更新脚本');
  console.log('========================================');
  console.log(`开始时间: ${new Date().toISOString()}`);
  
  if (options.accountId) {
    console.log(`模式: 更新指定账号 (account_id=${options.accountId})`);
  } else if (options.userId) {
    console.log(`模式: 更新指定用户的账号 (user_id=${options.userId})`);
  } else {
    console.log('模式: 更新所有启用的账号');
  }
  console.log('----------------------------------------');

  try {
    // 获取要更新的账号列表
    let accounts = [];
    
    if (options.accountId) {
      // 只更新指定账号
      const account = await kiroAccountService.getAccountById(options.accountId);
      if (account) {
        accounts = [account];
      } else {
        console.error(`错误: 账号不存在 (account_id=${options.accountId})`);
        process.exit(1);
      }
    } else if (options.userId) {
      // 更新指定用户的账号
      accounts = await kiroAccountService.getAccountsByUserId(options.userId);
      // 只更新启用的账号
      accounts = accounts.filter(acc => acc.status === 1);
    } else {
      // 更新所有启用的账号
      const result = await database.query(
        'SELECT * FROM kiro_accounts WHERE status = 1 ORDER BY created_at ASC'
      );
      accounts = result.rows;
    }

    console.log(`找到 ${accounts.length} 个账号需要更新`);
    console.log('----------------------------------------');

    // 统计
    const stats = {
      total: accounts.length,
      success: 0,
      failed: 0,
      results: []
    };

    // 逐个更新账号
    for (let i = 0; i < accounts.length; i++) {
      const account = accounts[i];
      console.log(`\n[${i + 1}/${accounts.length}] 更新账号: ${account.email || account.account_id}`);
      
      const result = await updateAccount(account);
      stats.results.push(result);
      
      if (result.success) {
        stats.success++;
      } else {
        stats.failed++;
      }

      // 添加延迟，避免请求过快
      if (i < accounts.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    // 输出统计结果
    console.log('\n========================================');
    console.log('更新完成');
    console.log('========================================');
    console.log(`总计: ${stats.total} 个账号`);
    console.log(`成功: ${stats.success} 个`);
    console.log(`失败: ${stats.failed} 个`);
    console.log(`结束时间: ${new Date().toISOString()}`);

    // 输出详细结果
    if (stats.failed > 0) {
      console.log('\n失败的账号:');
      stats.results
        .filter(r => !r.success)
        .forEach(r => {
          console.log(`  - ${r.account_id}: ${r.error}`);
        });
    }

    // 输出余额变化
    console.log('\n余额变化:');
    stats.results
      .filter(r => r.success)
      .forEach(r => {
        const change = r.new_balance.available - r.old_balance.available;
        const changeStr = change >= 0 ? `+${change.toFixed(2)}` : change.toFixed(2);
        console.log(`  - ${r.email || r.account_id}: ${r.old_balance.available.toFixed(2)} -> ${r.new_balance.available.toFixed(2)} (${changeStr})`);
      });

  } catch (error) {
    console.error('脚本执行失败:', error.message);
    process.exit(1);
  } finally {
    // 关闭数据库连接
    await database.close();
  }
}

// 运行主函数
main().catch(error => {
  console.error('未捕获的错误:', error);
  process.exit(1);
});