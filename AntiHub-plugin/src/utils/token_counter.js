/**
 * Token计数工具
 * 移植自tokencost项目，仅保留token计数功能
 */

import { encoding_for_model, get_encoding } from 'tiktoken';
import anthropicTokenizer from '@anthropic-ai/tokenizer';

const { countTokens } = anthropicTokenizer;

/**
 * 去除微调模型名称前缀
 * @param {string} model - 模型名称
 * @returns {string} 处理后的模型名称
 */
function stripFtModelName(model) {
  if (model.startsWith('ft:gpt-3.5-turbo')) {
    return 'ft:gpt-3.5-turbo';
  }
  return model;
}

/**
 * 计算Anthropic Claude模型的token数量
 * @param {Array<{role: string, content: string}>} messages - 消息数组
 * @param {string} model - 模型名称
 * @returns {number} token数量
 */
function getAnthropicTokenCount(messages, model) {
  const supportedModels = [
    'claude-opus-4',
    'claude-sonnet-4',
    'claude-3-7-sonnet',
    'claude-3-5-sonnet',
    'claude-3-5-haiku',
    'claude-3-haiku',
    'claude-3-opus',
  ];

  if (!supportedModels.some(supported => model.includes(supported))) {
    throw new Error(
      `${model} is not supported in token counting. Use the usage property in the response for exact counts.`
    );
  }

  try {
    // 将消息转换为文本进行计数
    const text = messages.map(msg => msg.content).join('\n');
    return countTokens(text);
  } catch (error) {
    throw new Error(`Failed to count Anthropic tokens: ${error.message}`);
  }
}

/**
 * 计算消息数组的token总数
 * @param {Array<{role: string, content: string, name?: string}>} messages - 消息数组
 * @param {string} model - 模型名称
 * @returns {number} token总数
 */
export function countMessageTokens(messages, model) {
  let normalizedModel = model.toLowerCase();
  normalizedModel = stripFtModelName(normalizedModel);

  // 处理Anthropic Claude模型
  if (normalizedModel.includes('claude-') && !normalizedModel.startsWith('anthropic.')) {
    console.warn('Warning: Anthropic token counting may have differences!');
    return getAnthropicTokenCount(messages, normalizedModel);
  }

  // 使用tiktoken处理OpenAI模型
  let encoding;
  try {
    encoding = encoding_for_model(normalizedModel);
  } catch (error) {
    console.warn('Model not found. Using cl100k_base encoding.');
    encoding = get_encoding('cl100k_base');
  }

  let tokensPerMessage = 3;
  let tokensPerName = 1;

  // 根据不同模型设置token计数规则
  const gpt35TurboModels = new Set([
    'gpt-3.5-turbo-0613',
    'gpt-3.5-turbo-16k-0613',
  ]);

  const gpt4Models = new Set([
    'gpt-4-0314',
    'gpt-4-32k-0314',
    'gpt-4-0613',
    'gpt-4-32k-0613',
    'gpt-4-turbo',
    'gpt-4-turbo-2024-04-09',
    'gpt-4o',
    'gpt-4o-2024-05-13',
  ]);

  if (gpt35TurboModels.has(normalizedModel) || gpt4Models.has(normalizedModel) || normalizedModel.startsWith('o')) {
    tokensPerMessage = 3;
    tokensPerName = 1;
  } else if (normalizedModel === 'gpt-3.5-turbo-0301') {
    tokensPerMessage = 4;
    tokensPerName = -1;
  } else if (normalizedModel.includes('gpt-3.5-turbo')) {
    console.warn('gpt-3.5-turbo may update over time. Using gpt-3.5-turbo-0613 for counting.');
    return countMessageTokens(messages, 'gpt-3.5-turbo-0613');
  } else if (normalizedModel.includes('gpt-4o')) {
    console.warn('gpt-4o may update over time. Using gpt-4o-2024-05-13 for counting.');
    return countMessageTokens(messages, 'gpt-4o-2024-05-13');
  } else if (normalizedModel.includes('gpt-4')) {
    console.warn('gpt-4 may update over time. Using gpt-4-0613 for counting.');
    return countMessageTokens(messages, 'gpt-4-0613');
  } else {
    throw new Error(
      `countMessageTokens() is not implemented for model ${model}. ` +
      'See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.'
    );
  }

  let numTokens = 0;
  for (const message of messages) {
    numTokens += tokensPerMessage;
    for (const [key, value] of Object.entries(message)) {
      if (typeof value === 'string') {
        numTokens += encoding.encode(value).length;
        if (key === 'name') {
          numTokens += tokensPerName;
        }
      }
    }
  }
  numTokens += 3; // 每个回复都以 <|start|>assistant<|message|> 开始

  encoding.free();
  return numTokens;
}

/**
 * 将自定义模型名称映射到tiktoken支持的模型
 * @param {string} model - 模型名称
 * @returns {string} tiktoken支持的模型名称
 */
function mapModelForTiktoken(model) {
  const normalizedModel = model.toLowerCase();
  
  // GPT-OSS 和 Gemini 模型使用 cl100k_base 编码（与 GPT-4 相同）
  if (normalizedModel.includes('gpt-oss') ||
      normalizedModel.includes('gemini') ||
      normalizedModel.includes('gpt-4o')) {
    return 'gpt-4o';
  }
  
  // GPT-4 系列
  if (normalizedModel.includes('gpt-4')) {
    return 'gpt-4';
  }
  
  // GPT-3.5 系列
  if (normalizedModel.includes('gpt-3.5')) {
    return 'gpt-3.5-turbo';
  }
  
  // o1/o3 系列模型
  if (normalizedModel.startsWith('o1') || normalizedModel.startsWith('o3')) {
    return 'gpt-4o';
  }
  
  return model;
}

/**
 * 计算字符串的token数量
 * @param {string} text - 文本字符串
 * @param {string} model - 模型名称
 * @returns {number} token数量
 */
export function countStringTokens(text, model) {
  let normalizedModel = model.toLowerCase();

  // 处理带provider前缀的模型名
  if (normalizedModel.includes('/')) {
    normalizedModel = normalizedModel.split('/').pop();
  }

  // Claude模型使用Anthropic tokenizer
  if (normalizedModel.includes('claude-')) {
    return countTokens(text);
  }

  // 映射自定义模型名称到tiktoken支持的模型
  const mappedModel = mapModelForTiktoken(normalizedModel);

  let encoding;
  try {
    encoding = encoding_for_model(mappedModel);
  } catch (error) {
    // 如果映射后的模型仍然不支持，使用 cl100k_base
    encoding = get_encoding('cl100k_base');
  }

  // 文本中可能包含 <|endoftext|> 等特殊 token（来自 stopSequences 配置）
  // tiktoken 默认不允许这些特殊 token，需要显式设置 allowedSpecial
  const tokens = encoding.encode(text, 'all');  // 'all' 允许所有特殊 token
  const count = tokens.length;
  encoding.free();
  
  return count;
}

/**
 * 计算prompt的token数量
 * @param {Array<{role: string, content: string}>|string} prompt - 消息数组或字符串
 * @param {string} model - 模型名称
 * @returns {number} token数量
 */
export function countPromptTokens(prompt, model) {
  const normalizedModel = model.toLowerCase();
  const strippedModel = stripFtModelName(normalizedModel);

  if (!Array.isArray(prompt) && typeof prompt !== 'string') {
    throw new TypeError(
      `Prompt must be either a string or array of message objects but found ${typeof prompt} instead.`
    );
  }

  if (typeof prompt === 'string' && !strippedModel.includes('claude-')) {
    return countStringTokens(prompt, model);
  } else {
    return countMessageTokens(prompt, model);
  }
}

/**
 * 计算completion的token数量
 * @param {string} completion - 完成文本
 * @param {string} model - 模型名称
 * @returns {number} token数量
 */
export function countCompletionTokens(completion, model) {
  const strippedModel = stripFtModelName(model);

  if (typeof completion !== 'string') {
    throw new TypeError(
      `Completion must be a string but found ${typeof completion} instead.`
    );
  }

  if (strippedModel.includes('claude-')) {
    const completionList = [{ role: 'assistant', content: completion }];
    // Anthropic在实际completion tokens上附加约13个额外tokens
    return countMessageTokens(completionList, model) - 13;
  } else {
    return countStringTokens(completion, model);
  }
}

/**
 * 计算所有tokens（prompt + completion）
 * @param {Array<{role: string, content: string}>|string} prompt - 消息数组或字符串
 * @param {string} completion - 完成文本
 * @param {string} model - 模型名称
 * @returns {{promptTokens: number, completionTokens: number, totalTokens: number}}
 */
export function countAllTokens(prompt, completion, model) {
  const promptTokens = countPromptTokens(prompt, model);
  const completionTokens = countCompletionTokens(completion, model);

  return {
    promptTokens,
    completionTokens,
    totalTokens: promptTokens + completionTokens,
  };
}

export default {
  countMessageTokens,
  countStringTokens,
  countPromptTokens,
  countCompletionTokens,
  countAllTokens,
};