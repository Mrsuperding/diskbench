import dayjs from "dayjs";
import "dayjs/locale/zh-cn";

// 设置中文本地化
dayjs.locale("zh-cn");

/**
 * 格式化时间
 * @param {string|number|Date} time - 时间
 * @param {string} format - 格式
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(time, format = "YYYY-MM-DD HH:mm:ss") {
  if (!time) return "";
  return dayjs(time).format(format);
}

/**
 * 格式化日期
 * @param {string|number|Date} date - 日期
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date) {
  if (!date) return "";
  return dayjs(date).format("YYYY-MM-DD");
}

/**
 * 获取相对时间
 * @param {string|number|Date} time - 时间
 * @returns {string} 相对时间字符串
 */
export function formatRelativeTime(time) {
  if (!time) return "";
  return dayjs(time).fromNow();
}

/**
 * 获取时间差
 * @param {string|number|Date} start - 开始时间
 * @param {string|number|Date} end - 结束时间
 * @param {string} unit - 时间单位
 * @returns {number} 时间差
 */
export function getTimeDiff(start, end, unit = "second") {
  return dayjs(end).diff(dayjs(start), unit);
}

/**
 * 格式化文件大小
 * @param {number} size - 文件大小（字节）
 * @returns {string} 格式化后的文件大小字符串
 */
export function formatFileSize(size) {
  if (!size || size === 0) return "0 B";

  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let index = 0;
  let fileSize = size;

  while (fileSize >= 1024 && index < units.length - 1) {
    fileSize /= 1024;
    index++;
  }

  return `${fileSize.toFixed(2)} ${units[index]}`;
}

/**
 * 格式化带宽
 * @param {number} bandwidth - 带宽（Bps）
 * @returns {string} 格式化后的带宽字符串
 */
export function formatBandwidth(bandwidth) {
  if (!bandwidth || bandwidth === 0) return "0 B/s";

  const units = ["B/s", "KB/s", "MB/s", "GB/s", "TB/s"];
  let index = 0;
  let value = bandwidth;

  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index++;
  }

  return `${value.toFixed(2)} ${units[index]}`;
}

/**
 * 格式化IOPS
 * @param {number} iops - IOPS
 * @returns {string} 格式化后的IOPS字符串
 */
export function formatIOPS(iops) {
  if (!iops || iops === 0) return "0";

  if (iops >= 1000000) {
    return `${(iops / 1000000).toFixed(2)}M`;
  } else if (iops >= 1000) {
    return `${(iops / 1000).toFixed(2)}K`;
  }

  return iops.toString();
}

/**
 * 格式化延迟
 * @param {number} latency - 延迟（毫秒）
 * @returns {string} 格式化后的延迟字符串
 */
export function formatLatency(latency) {
  if (!latency || latency === 0) return "0 ms";

  if (latency < 1) {
    return `${(latency * 1000).toFixed(2)} μs`;
  } else if (latency < 1000) {
    return `${latency.toFixed(2)} ms`;
  } else {
    return `${(latency / 1000).toFixed(2)} s`;
  }
}

/**
 * 格式化百分比
 * @param {number} value - 数值
 * @param {number} total - 总数
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的百分比字符串
 */
export function formatPercentage(value, total, decimals = 2) {
  if (!value || !total) return "0%";

  const percentage = (value / total) * 100;
  return `${percentage.toFixed(decimals)}%`;
}

/**
 * 格式化数字
 * @param {number} num - 数字
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的数字字符串
 */
export function formatNumber(num, decimals = 0) {
  if (!num) return "0";

  return num.toLocaleString("zh-CN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * 格式化状态文本
 * @param {string} status - 状态
 * @returns {string} 格式化后的状态文本
 */
export function formatStatus(status) {
  const statusMap = {
    pending: "待执行",
    running: "运行中",
    completed: "已完成",
    failed: "失败",
    stopped: "已停止",
    cancelled: "已取消",
    online: "在线",
    offline: "离线",
    maintenance: "维护中",
    active: "激活",
    inactive: "未激活",
    locked: "已锁定",
  };

  return statusMap[status] || status;
}

/**
 * 获取状态类型
 * @param {string} status - 状态
 * @returns {string} Element Plus 状态类型
 */
export function getStatusType(status) {
  const typeMap = {
    pending: "warning",
    running: "primary",
    completed: "success",
    failed: "danger",
    stopped: "info",
    cancelled: "info",
    online: "success",
    offline: "danger",
    maintenance: "warning",
    active: "success",
    inactive: "info",
    locked: "danger",
  };

  return typeMap[status] || "info";
}

/**
 * 截断字符串
 * @param {string} str - 字符串
 * @param {number} length - 最大长度
 * @returns {string} 截断后的字符串
 */
export function truncateString(str, length = 50) {
  if (!str) return "";

  if (str.length <= length) return str;

  return str.substring(0, length) + "...";
}

/**
 * 首字母大写
 * @param {string} str - 字符串
 * @returns {string} 首字母大写的字符串
 */
export function capitalize(str) {
  if (!str) return "";

  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * 生成UUID
 * @returns {string} UUID字符串
 */
export function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * 深拷贝对象
 * @param {Object} obj - 要拷贝的对象
 * @returns {Object} 拷贝后的对象
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== "object") return obj;

  if (obj instanceof Date) return new Date(obj.getTime());

  if (obj instanceof Array) return obj.map((item) => deepClone(item));

  if (typeof obj === "object") {
    const clonedObj = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 限制时间
 * @returns {Function} 节流后的函数
 */
export function throttle(func, limit) {
  let inThrottle;
  return function () {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * 验证邮箱格式
 * @param {string} email - 邮箱地址
 * @returns {boolean} 验证结果
 */
export function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 验证手机号格式
 * @param {string} phone - 手机号
 * @returns {boolean} 验证结果
 */
export function isValidPhone(phone) {
  const phoneRegex = /^1[3-9]\d{9}$/;
  return phoneRegex.test(phone);
}

/**
 * 验证IP地址格式
 * @param {string} ip - IP地址
 * @returns {boolean} 验证结果
 */
export function isValidIP(ip) {
  const ipRegex =
    /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  return ipRegex.test(ip);
}

/**
 * 下载文件
 * @param {string} content - 文件内容
 * @param {string} filename - 文件名
 * @param {string} contentType - 内容类型
 */
export function downloadFile(content, filename, contentType = "text/plain") {
  const blob = new Blob([content], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  window.URL.revokeObjectURL(url);
}

/**
 * 复制到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise} Promise对象
 */
export function copyToClipboard(text) {
  if (navigator.clipboard) {
    return navigator.clipboard.writeText(text);
  } else {
    // 降级方案
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      document.execCommand("copy");
      document.body.removeChild(textArea);
      return Promise.resolve();
    } catch (err) {
      document.body.removeChild(textArea);
      return Promise.reject(err);
    }
  }
}

/**
 * 解析JSON字符串
 * @param {string} str - JSON字符串
 * @param {any} defaultValue - 默认值
 * @returns {any} 解析后的对象或默认值
 */
export function safeJSONParse(str, defaultValue = null) {
  try {
    return JSON.parse(str);
  } catch (error) {
    console.error("JSON parse error:", error);
    return defaultValue;
  }
}

/**
 * 安全的JSON字符串化
 * @param {any} obj - 要字符串化的对象
 * @returns {string} JSON字符串
 */
export function safeJSONStringify(obj) {
  try {
    return JSON.stringify(obj, null, 2);
  } catch (error) {
    console.error("JSON stringify error:", error);
    return String(obj);
  }
}
