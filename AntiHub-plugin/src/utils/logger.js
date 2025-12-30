const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m'
};

// 日志级别优先级
const LOG_LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3
};

// 当前日志级别，默认为 info，可通过环境变量 LOG_LEVEL 设置
let currentLogLevel = process.env.LOG_LEVEL || 'info';

function setLogLevel(level) {
  if (LOG_LEVELS[level] !== undefined) {
    currentLogLevel = level;
  }
}

function shouldLog(level) {
  return LOG_LEVELS[level] >= LOG_LEVELS[currentLogLevel];
}

function logMessage(level, ...args) {
  if (!shouldLog(level)) return;
  
  const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  const color = { info: colors.green, warn: colors.yellow, error: colors.red, debug: colors.cyan }[level];
  console.log(`${colors.gray}${timestamp}${colors.reset} ${color}[${level}]${colors.reset}`, ...args);
}

function logRequest(method, path, status, duration) {
  const statusColor = status >= 500 ? colors.red : status >= 400 ? colors.yellow : colors.green;
  console.log(`${colors.cyan}[${method}]${colors.reset} - ${path} ${statusColor}${status}${colors.reset} ${colors.gray}${duration}ms${colors.reset}`);
}

function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export const log = {
  info: (...args) => logMessage('info', ...args),
  warn: (...args) => logMessage('warn', ...args),
  error: (...args) => logMessage('error', ...args),
  debug: (...args) => logMessage('debug', ...args),
  request: logRequest,
  generateRequestId,
  setLogLevel
};

export default log;
