import request from "./request";

export default {
  // 检测节点连通性
  checkConnectivity(nodeIds) {
    return request.post("/node-operations/check-connectivity", {
      node_ids: nodeIds,
    });
  },

  // 执行Shell命令
  executeCommand(nodeIds, command) {
    return request.post("/node-operations/execute-command", {
      node_ids: nodeIds,
      command: command,
    });
  },

  // 上传文件
  uploadFile(nodeIds, remotePath, file) {
    const formData = new FormData();
    nodeIds.forEach((id) => {
      formData.append("node_ids[]", id);
    });
    formData.append("remote_path", remotePath);
    formData.append("file", file);

    return request.post("/node-operations/upload-file", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  // 替换文件
  replaceFile(nodeIds, remotePath, file, backup = true) {
    const formData = new FormData();
    nodeIds.forEach((id) => {
      formData.append("node_ids[]", id);
    });
    formData.append("remote_path", remotePath);
    formData.append("file", file);
    formData.append("backup", backup ? "true" : "false");

    return request.post("/node-operations/replace-file", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  // 下载文件
  downloadFile(nodeId, remotePath) {
    return request.post("/node-operations/download-file", {
      node_id: nodeId,
      remote_path: remotePath,
    });
  },
};
