import fs from 'fs';
import log from '../utils/logger.js';

// API端点列表（按优先级排序）
const API_ENDPOINTS = [
  {
    baseUrl: 'https://daily-cloudcode-pa.sandbox.googleapis.com',
    host: 'daily-cloudcode-pa.sandbox.googleapis.com'
  },
  {
    baseUrl: 'https://cloudcode-pa.googleapis.com',
    host: 'cloudcode-pa.googleapis.com'
  },
  {
    baseUrl: 'https://autopush-cloudcode-pa.sandbox.googleapis.com',
    host: 'autopush-cloudcode-pa.sandbox.googleapis.com'
  }
];

const defaultConfig = {
  server: { port: 8045, host: '127.0.0.1' },
  api: {
    url: 'https://daily-cloudcode-pa.sandbox.googleapis.com/v1internal:streamGenerateContent?alt=sse',
    modelsUrl: 'https://daily-cloudcode-pa.sandbox.googleapis.com/v1internal:fetchAvailableModels',
    host: 'daily-cloudcode-pa.sandbox.googleapis.com',
    userAgent: 'antigravity/ windows/amd64',
    endpoints: API_ENDPOINTS
  },
  defaults: { temperature: 1, top_p: 0.85, top_k: 50, max_tokens: 8096 },
  security: { maxRequestSize: '50mb', apiKey: null },
  systemInstruction: ''
};

let config;
try {
  config = JSON.parse(fs.readFileSync('./config.json', 'utf8'));
  // 确保 api.endpoints 存在
  if (!config.api) {
    config.api = defaultConfig.api;
  } else if (!config.api.endpoints) {
    config.api.endpoints = API_ENDPOINTS;
  }
  log.info('✓ 配置文件加载成功');
} catch {
  config = defaultConfig;
  log.warn('⚠ 配置文件未找到，使用默认配置');
}

/**
 * 获取指定索引的API端点URL
 * @param {number} endpointIndex - 端点索引
 * @returns {Object} 包含url, imageUrl, modelsUrl, host的对象
 */
export function getApiEndpoint(endpointIndex = 0) {
  const endpoints = config.api.endpoints || API_ENDPOINTS;
  const index = Math.min(endpointIndex, endpoints.length - 1);
  const endpoint = endpoints[index];
  
  return {
    url: `${endpoint.baseUrl}/v1internal:streamGenerateContent?alt=sse`,
    imageUrl: `${endpoint.baseUrl}/v1internal:generateContent`,
    modelsUrl: `${endpoint.baseUrl}/v1internal:fetchAvailableModels`,
    host: endpoint.host
  };
}

/**
 * 获取所有API端点数量
 * @returns {number} 端点数量
 */
export function getEndpointCount() {
  return (config.api.endpoints || API_ENDPOINTS).length;
}

export default config;
