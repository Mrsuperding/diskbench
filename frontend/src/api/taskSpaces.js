import request from "./request";

// 获取任务空间列表
export const getTaskSpaces = (params) => {
  return request({
    url: "/task-spaces",
    method: "get",
    params,
  });
};

// 获取任务空间详情
export const getTaskSpace = (id) => {
  return request({
    url: `/task-spaces/${id}`,
    method: "get",
  });
};

// 创建任务空间
export const createTaskSpace = (data) => {
  return request({
    url: "/task-spaces",
    method: "post",
    data,
  });
};

// 更新任务空间
export const updateTaskSpace = (id, data) => {
  return request({
    url: `/task-spaces/${id}`,
    method: "put",
    data,
  });
};

// 删除任务空间
export const deleteTaskSpace = (id) => {
  return request({
    url: `/task-spaces/${id}`,
    method: "delete",
  });
};

// 获取任务空间成员列表
export const getTaskSpaceMembers = (spaceId) => {
  return request({
    url: `/task-spaces/${spaceId}/members`,
    method: "get",
  });
};

// 添加任务空间成员
export const addTaskSpaceMember = (spaceId, data) => {
  return request({
    url: `/task-spaces/${spaceId}/members`,
    method: "post",
    data,
  });
};

// 更新任务空间成员角色
export const updateTaskSpaceMember = (spaceId, memberId, data) => {
  return request({
    url: `/task-spaces/${spaceId}/members/${memberId}`,
    method: "put",
    data,
  });
};

// 移除任务空间成员
export const removeTaskSpaceMember = (spaceId, memberId) => {
  return request({
    url: `/task-spaces/${spaceId}/members/${memberId}`,
    method: "delete",
  });
};
