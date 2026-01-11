import request from "./request";

// 获取任务的所有日志
export const getTaskLogs = (taskId, params = {}) => {
  return request({
    url: "/logs/task/" + taskId,
    method: "get",
    params
  });
};

// 获取单个日志详情
export const getLogDetail = (logId) => {
  return request({
    url: "/logs/" + logId,
    method: "get"
  });
};

// 获取IOSTAT指标数据
export const getIOStatMetrics = (logId, params = {}) => {
  return request({
    url: "/logs/" + logId + "/iostat-metrics",
    method: "get",
    params
  });
};

// 获取性能抖动数据
export const getJitterData = (logId, params = {}) => {
  return request({
    url: "/logs/" + logId + "/jitter",
    method: "get",
    params
  });
};

// 获取IOSTAT指标的抖动计算结果
export const getIOStatJitter = (logId) => {
  return request({
    url: "/logs/" + logId + "/iostat-jitter",
    method: "get"
  });
};

// 获取FIO日志解析结果
export const getFIOResults = (logId) => {
  return request({
    url: "/logs/" + logId + "/fio-results",
    method: "get"
  });
};

// 获取实时FIO日志指标数据（保留旧函数名用于兼容）
export const getRealtimeMetrics = (taskId, params = {}) => {
  return request({
    url: "/logs/task/" + taskId + "/realtime-metrics",
    method: "get",
    params
  });
};

// 从FIO日志文件获取性能指标数据
export const getFioMetricsFromLogs = (taskId, params = {}) => {
  return request({
    url: "/logs/task/" + taskId + "/realtime-metrics",
    method: "get",
    params
  });
};

// 下载日志文件
export const downloadLog = async (logId) => {
  const response = await request({
    url: "/logs/" + logId + "/download",
    method: "get",
    responseType: "blob"
  });

  const contentDisposition = response.headers["content-disposition"];
  let filename = "download";
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/);
    if (filenameMatch) {
      filename = filenameMatch[1];
    }
  }

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
