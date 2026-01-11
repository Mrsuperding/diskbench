// 本地数据管理工具
// 用于处理日志文件的存储、读取和解压

/**
 * 本地数据管理器
 */
class LocalDataManager {
  constructor() {
    this.storageKeyPrefix = "io_test_";
  }

  /**
   * 解压zip文件
   * @param {Blob} zipBlob - zip文件Blob对象
   * @returns {Promise<object>} - 解压后的文件对象
   */
  async extractZipFile(zipBlob) {
    try {
      // 使用JSZip库解压文件
      const JSZip = require('jszip');
      const zip = new JSZip();
      const result = await zip.loadAsync(zipBlob);
      const files = {};
      for (const [name, file] of Object.entries(result.files)) {
        if (!file.dir) {
          files[name] = await file.async('text');
        }
      }
      return files;
    } catch (error) {
      console.error("解压文件失败:", error);
      throw error;
    }
  }

  /**
   * 从本地文件系统读取文件
   * @param {File} file - 文件对象
   * @returns {Promise<string>} - 文件内容
   */
  async readLocalFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        resolve(e.target.result);
      };
      reader.onerror = (e) => {
        reject(e);
      };
      reader.readAsText(file);
    });
  }

  /**
   * 处理上传的日志文件
   * @param {File} file - 上传的文件对象
   * @param {string} taskId - 任务ID
   * @returns {Promise<boolean>} - 是否处理成功
   */
  async processUploadedFile(file, taskId) {
    try {
      let logContent = "";
      let logType = "";

      // 根据文件扩展名判断文件类型
      if (file.name.endsWith(".zip")) {
        // 解压zip文件
        const extractedFiles = await this.extractZipFile(file);

        // 处理解压后的文件
        for (const [filename, content] of Object.entries(extractedFiles)) {
          if (filename.includes("iostat")) {
            logType = "iostat";
            logContent = content;
            break;
          } else if (filename.includes("fio")) {
            logType = "fio";
            logContent = content;
            break;
          }
        }
      } else {
        // 直接读取文本文件
        logContent = await this.readLocalFile(file);
        if (file.name.includes("iostat")) {
          logType = "iostat";
        } else if (file.name.includes("fio")) {
          logType = "fio";
        }
      }

      if (!logContent || !logType) {
        throw new Error("无法识别的日志文件格式");
      }

      // 解析日志内容
      let parsedData = {};
      if (logType === "iostat") {
        parsedData = this.parseIostatLog(logContent);
      } else if (logType === "fio") {
        parsedData = this.parseFioLog(logContent);
      }

      // 生成唯一日志ID
      const logId = `local_${Date.now()}`;

      // 保存到本地存储
      const logData = {
        id: logId,
        log_type: logType,
        log_filename: file.name,
        collection_time: new Date().toISOString(),
        file_size: file.size,
        metrics: parsedData,
        raw_content: logContent,
      };

      // 保存日志文件
      this.saveLogFile(taskId, logId, logData);

      // 更新任务数据
      const taskData = this.getTaskData(taskId) || {};
      taskData.logs = taskData.logs || [];
      taskData.logs.push(logData);
      this.saveTaskData(taskId, taskData);

      return true;
    } catch (error) {
      console.error("处理上传文件失败:", error);
      return false;
    }
  }

  /**
   * 保存任务数据到本地存储
   * @param {string} taskId - 任务ID
   * @param {object} data - 要保存的数据
   */
  saveTaskData(taskId, data) {
    try {
      const key = `${this.storageKeyPrefix}${taskId}_data`;
      localStorage.setItem(key, JSON.stringify(data));
      return true;
    } catch (error) {
      console.error("保存任务数据失败:", error);
      return false;
    }
  }

  /**
   * 从本地存储获取任务数据
   * @param {string} taskId - 任务ID
   * @returns {object|null} - 任务数据或null
   */
  getTaskData(taskId) {
    try {
      const key = `${this.storageKeyPrefix}${taskId}_data`;
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error("获取任务数据失败:", error);
      return null;
    }
  }

  /**
   * 保存日志文件到本地
   * @param {string} taskId - 任务ID
   * @param {string} logId - 日志ID
   * @param {object} logData - 日志数据
   */
  saveLogFile(taskId, logId, logData) {
    try {
      const key = `${this.storageKeyPrefix}${taskId}_log_${logId}`;
      localStorage.setItem(key, JSON.stringify(logData));
      return true;
    } catch (error) {
      console.error("保存日志文件失败:", error);
      return false;
    }
  }

  /**
   * 获取日志文件
   * @param {string} taskId - 任务ID
   * @param {string} logId - 日志ID
   * @returns {object|null} - 日志数据或null
   */
  getLogFile(taskId, logId) {
    try {
      const key = `${this.storageKeyPrefix}${taskId}_log_${logId}`;
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error("获取日志文件失败:", error);
      return null;
    }
  }

  /**
   * 删除任务的所有本地数据
   * @param {string} taskId - 任务ID
   */
  deleteTaskData(taskId) {
    try {
      // 删除任务数据
      localStorage.removeItem(`${this.storageKeyPrefix}${taskId}_data`);

      // 删除所有相关日志
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith(`${this.storageKeyPrefix}${taskId}_log_`)) {
          localStorage.removeItem(key);
          i--; // 调整索引
        }
      }
      return true;
    } catch (error) {
      console.error("删除任务数据失败:", error);
      return false;
    }
  }

  /**
   * 检查是否有本地数据
   * @param {string} taskId - 任务ID
   * @returns {boolean} - 是否有本地数据
   */
  hasLocalData(taskId) {
    try {
      const dataKey = `${this.storageKeyPrefix}${taskId}_data`;
      return localStorage.getItem(dataKey) !== null;
    } catch (error) {
      console.error("检查本地数据失败:", error);
      return false;
    }
  }

  /**
   * 解析iostat日志
   * @param {string} logContent - 日志内容
   * @returns {array} - 解析后的指标数据
   */
  parseIostatLog(logContent) {
    try {
      const metrics = [];
      const lines = logContent.split("\n");

      lines.forEach((line) => {
        // 跳过标题行和空行
        if (!line || line.startsWith("Device:")) {
          return;
        }

        // 使用正则表达式解析设备数据行
        const parts = line.trim().split(/\s+/);
        if (parts.length < 14) {
          return;
        }

        const device = parts[0];
        const readKbps = parseFloat(parts[5]) * 1024; // rMB/s 转换为 KB/s
        const writeKbps = parseFloat(parts[6]) * 1024; // wMB/s 转换为 KB/s
        const readIOPS = parseFloat(parts[2]);
        const writeIOPS = parseFloat(parts[3]);
        const awaitTime = parseFloat(parts[9]);
        const svctm = parseFloat(parts[12]);
        const util = parseFloat(parts[13]);

        // 检查是否为有效数字
        if (
          isNaN(readKbps) ||
          isNaN(writeKbps) ||
          isNaN(readIOPS) ||
          isNaN(writeIOPS)
        ) {
          return;
        }

        metrics.push({
          timestamp: new Date().toISOString(),
          device: device,
          read_kbps: readKbps,
          write_kbps: writeKbps,
          total_kbps: readKbps + writeKbps,
          read_iops: readIOPS,
          write_iops: writeIOPS,
          total_iops: readIOPS + writeIOPS,
          await_time: awaitTime,
          svctm: svctm,
          util: util,
        });
      });

      return metrics;
    } catch (error) {
      console.error("解析iostat日志失败:", error);
      return [];
    }
  }

  /**
   * 解析fio日志
   * @param {string} logContent - 日志内容
   * @returns {object} - 解析后的fio结果
   */
  parseFioLog(logContent) {
    try {
      // 简单实现，实际解析需要更复杂的逻辑
      const result = {
        job_name: "unknown",
        read: {},
        write: {},
        total: {},
      };

      // 尝试解析JSON格式的fio输出
      if (logContent.trim().startsWith("{")) {
        return JSON.parse(logContent);
      }

      // 解析文本格式的fio输出
      const lines = logContent.split("\n");
      let currentSection = null;

      lines.forEach((line) => {
        line = line.trim();

        // 识别不同部分
        if (line.startsWith("[read]")) {
          currentSection = "read";
        } else if (line.startsWith("[write]")) {
          currentSection = "write";
        } else if (line.startsWith("[total]")) {
          currentSection = "total";
        } else if (currentSection && line.includes("=")) {
          // 解析键值对
          const [key, value] = line.split("=").map((item) => item.trim());
          if (key && value) {
            // 尝试转换数值
            const numValue = parseFloat(value);
            result[currentSection][key] = isNaN(numValue) ? value : numValue;
          }
        }
      });

      return result;
    } catch (error) {
      console.error("解析fio日志失败:", error);
      return {};
    }
  }

  /**
   * 计算性能抖动
   * @param {array} metrics - 指标数据数组
   * @param {string} metricName - 要计算抖动的指标名称
   * @returns {object} - 抖动统计结果
   */
  calculateJitter(metrics, metricName = "total_iops") {
    try {
      if (!metrics || metrics.length < 2) {
        return {
          mean: 0,
          stdDev: 0,
          jitterPercent: 0,
          min: 0,
          max: 0,
          p50: 0,
          p90: 0,
          p95: 0,
          p99: 0,
        };
      }

      // 提取指标值
      const values = metrics
        .map((item) => item[metricName])
        .filter((value) => !isNaN(value));
      if (values.length < 2) {
        return {
          mean: 0,
          stdDev: 0,
          jitterPercent: 0,
          min: 0,
          max: 0,
          p50: 0,
          p90: 0,
          p95: 0,
          p99: 0,
        };
      }

      // 计算平均值
      const sum = values.reduce((acc, val) => acc + val, 0);
      const mean = sum / values.length;

      // 计算标准差
      const squaredDiffs = values.map((val) => Math.pow(val - mean, 2));
      const variance =
        squaredDiffs.reduce((acc, val) => acc + val, 0) / values.length;
      const stdDev = Math.sqrt(variance);

      // 计算抖动百分比
      const jitterPercent = mean !== 0 ? (stdDev / mean) * 100 : 0;

      // 计算分位数
      const sortedValues = [...values].sort((a, b) => a - b);
      const min = sortedValues[0];
      const max = sortedValues[sortedValues.length - 1];

      const p50 = sortedValues[Math.floor(sortedValues.length * 0.5)];
      const p90 = sortedValues[Math.floor(sortedValues.length * 0.9)];
      const p95 = sortedValues[Math.floor(sortedValues.length * 0.95)];
      const p99 = sortedValues[Math.floor(sortedValues.length * 0.99)];

      return {
        mean: mean.toFixed(2),
        stdDev: stdDev.toFixed(2),
        jitterPercent: jitterPercent.toFixed(2),
        min: min.toFixed(2),
        max: max.toFixed(2),
        p50: p50.toFixed(2),
        p90: p90.toFixed(2),
        p95: p95.toFixed(2),
        p99: p99.toFixed(2),
      };
    } catch (error) {
      console.error("计算性能抖动失败:", error);
      return {
        mean: 0,
        stdDev: 0,
        jitterPercent: 0,
        min: 0,
        max: 0,
        p50: 0,
        p90: 0,
        p95: 0,
        p99: 0,
      };
    }
  }
}

export default new LocalDataManager();
