<template>
  <div class="task-comparison-container">
    <!-- 1. 任务选择与筛选区 -->
    <el-card shadow="hover" class="filter-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><TrendCharts /></el-icon> 多任务性能对比</span>
          <el-button
            type="primary"
            size="small"
            @click="performComparison"
            :loading="loading"
            :disabled="selectedTaskIds.length < 2"
          >
            开始对比
          </el-button>
        </div>
      </template>

      <el-form :inline="true">
        <el-form-item label="搜索任务">
          <el-input
            v-model="taskSearchQuery"
            placeholder="按任务名称或ID搜索"
            clearable
            style="width: 300px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="任务状态">
          <el-select
            v-model="taskStatusFilter"
            placeholder="全部状态"
            style="width: 150px"
            clearable
          >
            <el-option label="全部状态" value="" />
            <el-option label="已完成" value="completed" />
            <el-option label="执行中" value="running" />
            <el-option label="失败" value="failed" />
            <el-option label="待执行" value="pending" />
          </el-select>
        </el-form-item>

        <el-form-item label="聚合模式">
          <el-radio-group v-model="aggregationMode" size="small">
            <el-radio-button label="avg">平均值</el-radio-button>
            <el-radio-button label="max">最大值</el-radio-button>
            <el-radio-button label="min">最小值</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <!-- 任务选择表格 -->
      <div class="task-selection-section">
        <div class="section-header">
          <span>任务列表（已选择 {{ selectedTaskIds.length }} / 10）</span>
          <el-button
            size="small"
            :disabled="selectedTaskIds.length === 0"
            @click="clearSelection"
          >
            清空选择
          </el-button>
        </div>

        <el-table
          :data="paginatedFilteredTasks"
          style="width: 100%"
          max-height="400"
          @selection-change="handleTaskSelectionChange"
          ref="taskTableRef"
        >
          <el-table-column
            type="selection"
            width="55"
            :selectable="isTaskSelectable"
          />
          <el-table-column prop="id" label="任务ID" width="80" />
          <el-table-column prop="name" label="任务名称" min-width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)" size="small">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="节点数" width="80" align="center">
            <template #default="scope">
              {{ scope.row.nodes ? scope.row.nodes.length : 0 }}
            </template>
          </el-table-column>
          <el-table-column label="测试用例数" width="100" align="center">
            <template #default="scope">
              {{ scope.row.io_test_cases ? scope.row.io_test_cases.length : 0 }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <el-pagination
          v-if="filteredTasks.length > taskPageSize"
          :current-page="taskCurrentPage"
          @current-change="(val) => taskCurrentPage = val"
          :page-size="taskPageSize"
          :total="filteredTasks.length"
          layout="total, prev, pager, next"
          style="margin-top: 15px; justify-content: flex-end"
          small
        />
      </div>
    </el-card>

    <!-- 2. 对比结果统计卡片 -->
    <el-card v-if="comparisonData" shadow="hover" class="statistics-card">
      <el-descriptions :column="4" border>
        <el-descriptions-item label="对比任务数">
          {{ comparisonData.tasks.length }}
        </el-descriptions-item>
        <el-descriptions-item label="共同IO模型">
          <el-tag type="success">{{ comparisonData.statistics.common_io_models_count }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="总IO模型数">
          {{ comparisonData.statistics.total_io_models }}
        </el-descriptions-item>
        <el-descriptions-item label="聚合模式">
          {{ aggregationModeLabel }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 提示信息 -->
      <el-alert
        v-if="comparisonData.statistics.common_io_models_count === 0"
        title="未找到共同的IO模型"
        type="warning"
        description="所选任务没有使用相同的IO测试用例，无法进行对比。请选择使用相同测试配置的任务。"
        :closable="false"
        show-icon
        style="margin-top: 15px"
      />
    </el-card>

    <!-- 3. 表格对比区 -->
    <el-card v-if="comparisonData && tableData.length > 0" shadow="hover" class="table-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><Grid /></el-icon> 性能指标对比表</span>
          <div>
            <el-button size="small" @click="exportToCSV">
              <el-icon><Download /></el-icon> 导出CSV
            </el-button>
          </div>
        </div>
      </template>

      <!-- 表格指标选择 -->
      <el-form :inline="true" style="margin-bottom: 15px">
        <el-form-item label="显示指标">
          <el-checkbox-group v-model="selectedTableMetrics" size="small">
            <el-checkbox label="total_iops">总IOPS</el-checkbox>
            <el-checkbox label="read_iops">读IOPS</el-checkbox>
            <el-checkbox label="write_iops">写IOPS</el-checkbox>
            <el-checkbox label="bandwidth">带宽</el-checkbox>
            <el-checkbox label="await_time">平均延迟</el-checkbox>
            <el-checkbox label="lat_p99">P99延迟</el-checkbox>
            <el-checkbox label="lat_p9999">P9999延迟</el-checkbox>
            <el-checkbox label="lat_max">最大延迟</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="对比方式">
          <el-radio-group v-model="comparisonMode" size="small">
            <el-radio-button label="absolute">绝对值</el-radio-button>
            <el-radio-button label="percentage">百分比</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="comparisonMode === 'percentage'" label="基准任务">
          <el-select v-model="baselineTaskId" size="small" style="width: 200px">
            <el-option
              v-for="task in comparisonData.tasks"
              :key="task.id"
              :label="task.name"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table
        :data="paginatedTableData"
        border
        stripe
        max-height="600"
        :row-class-name="tableRowClassName"
      >
        <el-table-column
          prop="io_model_name"
          label="IO模型"
          width="200"
          fixed
        />

        <!-- 动态生成每个任务的列 -->
        <el-table-column
          v-for="task in comparisonData.tasks"
          :key="task.id"
          :label="task.name"
          align="center"
        >
          <el-table-column
            v-if="selectedTableMetrics.includes('total_iops')"
            label="总IOPS"
            width="120"
            align="right"
          >
            <template #default="scope">
              <span :class="getCellClass('total_iops', scope.row, task.id)">
                {{ formatCellValue('total_iops', scope.row, task.id) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            v-if="selectedTableMetrics.includes('read_iops')"
            label="读IOPS"
            width="120"
            align="right"
          >
            <template #default="scope">
              <span :class="getCellClass('read_iops', scope.row, task.id)">
                {{ formatCellValue('read_iops', scope.row, task.id) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            v-if="selectedTableMetrics.includes('write_iops')"
            label="写IOPS"
            width="120"
            align="right"
          >
            <template #default="scope">
              <span :class="getCellClass('write_iops', scope.row, task.id)">
                {{ formatCellValue('write_iops', scope.row, task.id) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            v-if="selectedTableMetrics.includes('bandwidth')"
            label="带宽(MB/s)"
            width="120"
            align="right"
          >
            <template #default="scope">
              <span :class="getCellClass('bandwidth', scope.row, task.id)">
                {{ formatCellValue('bandwidth', scope.row, task.id) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            v-if="selectedTableMetrics.includes('await_time')"
            label="平均延迟(ms)"
            width="120"
            align="right"
          >
            <template #default="scope">
              <span :class="getCellClass('await_time', scope.row, task.id)">
                {{ formatCellValue('await_time', scope.row, task.id) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            v-if="selectedTableMetrics.includes('lat_p99')"
            label="P99延迟(ms)"
            width="120"
            align="right"
          >
            <template #default="scope">
              <span :class="getCellClass('lat_p99', scope.row, task.id)">
                {{ formatCellValue('lat_p99', scope.row, task.id) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            v-if="selectedTableMetrics.includes('lat_p9999')"
            label="P9999延迟(ms)"
            width="120"
            align="right"
          >
            <template #default="scope">
              <span :class="getCellClass('lat_p9999', scope.row, task.id)">
                {{ formatCellValue('lat_p9999', scope.row, task.id) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            v-if="selectedTableMetrics.includes('lat_max')"
            label="最大延迟(ms)"
            width="120"
            align="right"
          >
            <template #default="scope">
              <span :class="getCellClass('lat_max', scope.row, task.id)">
                {{ formatCellValue('lat_max', scope.row, task.id) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="tableData.length > pageSize"
        :current-page="currentPage"
        @current-change="(val) => currentPage = val"
        :page-size="pageSize"
        :total="tableData.length"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>

    <!-- 4. 图表可视化区 -->
    <el-card v-if="comparisonData && tableData.length > 0" shadow="hover" class="chart-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><PieChart /></el-icon> 性能可视化对比</span>
          <div>
            <el-segmented v-model="activeChartType" :options="chartTypes" />
          </div>
        </div>
      </template>

      <!-- 图表指标选择 -->
      <el-form :inline="true" style="margin-bottom: 15px">
        <el-form-item label="对比指标">
          <el-radio-group v-model="chartMetricType" size="small">
            <el-radio-button label="iops">IOPS</el-radio-button>
            <el-radio-button label="bandwidth">带宽</el-radio-button>
            <el-radio-button label="latency">延迟</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <!-- 图表容器 -->
      <div class="chart-container">
        <div v-show="activeChartType === '柱状图'" ref="barChartRef" class="chart" />
        <div v-show="activeChartType === '雷达图'" ref="radarChartRef" class="chart" />
        <div v-show="activeChartType === '折线图'" ref="lineChartRef" class="chart" />
        <div v-show="activeChartType === '热力图'" ref="heatmapChartRef" class="chart" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts, Grid, Download, PieChart, Search } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import tasksApi from '@/api/tasks'

// 数据状态
const selectedTaskIds = ref([])
const aggregationMode = ref('avg')
const loading = ref(false)

const availableTasks = ref([])
const comparisonData = ref(null)

// 任务搜索和筛选
const taskSearchQuery = ref('')
const taskStatusFilter = ref('')
const taskCurrentPage = ref(1)
const taskPageSize = ref(10)
const taskTableRef = ref(null)

// 指标选择
const selectedTableMetrics = ref(['total_iops', 'bandwidth', 'await_time', 'lat_p99'])
const chartMetricType = ref('latency') // iops, bandwidth, latency

// 对比模式
const comparisonMode = ref('absolute') // absolute 或 percentage
const baselineTaskId = ref(null)

const activeChartType = ref('柱状图')
const chartTypes = ['柱状图', '雷达图', '折线图', '热力图']

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 图表实例
const barChartRef = ref(null)
const radarChartRef = ref(null)
const lineChartRef = ref(null)
const heatmapChartRef = ref(null)

let barChart = null
let radarChart = null
let lineChart = null
let heatmapChart = null

// 计算属性
const selectedTasks = computed(() => {
  return availableTasks.value.filter(t => selectedTaskIds.value.includes(t.id))
})

const aggregationModeLabel = computed(() => {
  const labels = { avg: '平均值', max: '最大值', min: '最小值' }
  return labels[aggregationMode.value] || '平均值'
})

// 任务筛选
const filteredTasks = computed(() => {
  let tasks = availableTasks.value

  // 按状态筛选
  if (taskStatusFilter.value) {
    tasks = tasks.filter(t => t.status === taskStatusFilter.value)
  }

  // 按搜索关键词筛选
  if (taskSearchQuery.value) {
    const query = taskSearchQuery.value.toLowerCase()
    tasks = tasks.filter(t =>
      t.name.toLowerCase().includes(query) ||
      String(t.id).includes(query)
    )
  }

  return tasks
})

// 分页后的任务列表
const paginatedFilteredTasks = computed(() => {
  const start = (taskCurrentPage.value - 1) * taskPageSize.value
  const end = start + taskPageSize.value
  return filteredTasks.value.slice(start, end)
})

const tableData = computed(() => {
  if (!comparisonData.value) return []

  return comparisonData.value.comparison_data.map(item => {
    const row = { io_model_name: item.io_model_name }

    // 为每个任务生成列数据
    Object.entries(item.metrics_by_task).forEach(([taskId, metrics]) => {
      row[`task_${taskId}_read_iops`] = metrics.read_iops || 0
      row[`task_${taskId}_write_iops`] = metrics.write_iops || 0
      row[`task_${taskId}_total_iops`] = (metrics.read_iops || 0) + (metrics.write_iops || 0)
      row[`task_${taskId}_bandwidth`] = ((metrics.read_kbps || 0) + (metrics.write_kbps || 0)) / 1024 // 转换为MB/s
      row[`task_${taskId}_await_time`] = metrics.await_time || 0
      row[`task_${taskId}_lat_p99`] = metrics.lat_p99 || 0
      row[`task_${taskId}_lat_p9999`] = metrics.lat_p9999 || 0
      row[`task_${taskId}_lat_max`] = metrics.lat_max || 0
      row[`task_${taskId}_read_kbps`] = metrics.read_kbps || 0
      row[`task_${taskId}_write_kbps`] = metrics.write_kbps || 0
    })

    return row
  })
})

const paginatedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return tableData.value.slice(start, end)
})

// 方法
const getStatusLabel = (status) => {
  const labels = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return labels[status] || status
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    paused: ''
  }
  return types[status] || ''
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const isTaskSelectable = (row) => {
  // 只有已完成的任务可以选择，且不超过10个
  if (row.status !== 'completed') return false
  if (selectedTaskIds.value.includes(row.id)) return true
  return selectedTaskIds.value.length < 10
}

const handleTaskSelectionChange = (selection) => {
  selectedTaskIds.value = selection.map(t => t.id)
}

const clearSelection = () => {
  selectedTaskIds.value = []
  if (taskTableRef.value) {
    taskTableRef.value.clearSelection()
  }
}

const loadTasks = async () => {
  try {
    const response = await tasksApi.getTasks()
    console.log('任务列表完整响应:', response)

    // 响应拦截器已经处理了success字段，直接使用response.data
    if (response && response.data) {
      availableTasks.value = response.data || []
      console.log('加载的任务数量:', availableTasks.value.length)
      console.log('任务列表:', availableTasks.value)

      // 恢复之前的选择状态
      await nextTick()
      if (taskTableRef.value && selectedTaskIds.value.length > 0) {
        availableTasks.value.forEach(task => {
          if (selectedTaskIds.value.includes(task.id)) {
            taskTableRef.value.toggleRowSelection(task, true)
          }
        })
      }
    } else {
      console.error('响应数据为空')
      ElMessage.error('获取任务列表失败: 响应数据为空')
    }
  } catch (error) {
    console.error('加载任务列表错误:', error)
    console.error('错误详情:', error.response)
    ElMessage.error('加载任务列表失败: ' + (error.message || '网络错误'))
  }
}

const performComparison = async () => {
  if (selectedTaskIds.value.length < 2) {
    ElMessage.warning('请至少选择2个任务进行对比')
    return
  }

  if (selectedTaskIds.value.length > 10) {
    ElMessage.warning('最多支持10个任务同时对比')
    return
  }

  loading.value = true

  try {
    const response = await tasksApi.compareTasks({
      task_ids: selectedTaskIds.value,
      aggregation_mode: aggregationMode.value
    })

    console.log('对比API响应:', response)

    // 响应拦截器已经处理了success字段，直接使用response.data
    if (response && response.data) {
      comparisonData.value = response.data
      currentPage.value = 1 // 重置分页

      // 设置默认基准任务为第一个任务
      if (response.data.tasks && response.data.tasks.length > 0) {
        baselineTaskId.value = response.data.tasks[0].id
      }

      ElMessage.success(`对比完成！找到 ${response.data.statistics.common_io_models_count} 个共同的IO模型`)

      // 初始化图表
      await nextTick()
      initCharts()
    } else {
      ElMessage.error('对比失败: 响应数据为空')
    }
  } catch (error) {
    console.error('对比失败:', error)
    console.error('错误详情:', error.response)
    ElMessage.error('对比失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

const tableRowClassName = ({ rowIndex }) => {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}

const formatNumber = (value) => {
  if (value === undefined || value === null) return '-'
  return Number(value).toLocaleString('en-US', { maximumFractionDigits: 2 })
}

const formatCellValue = (metric, row, taskId) => {
  const value = row[`task_${taskId}_${metric}`]

  if (comparisonMode.value === 'absolute') {
    // 绝对值模式
    return formatNumber(value)
  } else {
    // 百分比模式
    if (!baselineTaskId.value) return formatNumber(value)

    const baselineValue = row[`task_${baselineTaskId.value}_${metric}`]
    if (!baselineValue || baselineValue === 0) {
      return formatNumber(value)
    }

    // 如果是基准任务本身，显示绝对值
    if (taskId === baselineTaskId.value) {
      return formatNumber(value) + ' (基准)'
    }

    // 计算百分比差异
    const percentage = ((value - baselineValue) / baselineValue * 100).toFixed(2)
    const sign = percentage > 0 ? '+' : ''
    return `${sign}${percentage}%`
  }
}

const getCellClass = (metric, row, taskId) => {
  if (!comparisonData.value) return ''

  const values = comparisonData.value.tasks.map(task =>
    row[`task_${task.id}_${metric}`]
  ).filter(v => v !== undefined && v !== null && v !== 0)

  if (values.length === 0) return ''

  const currentValue = row[`task_${taskId}_${metric}`]
  if (!currentValue) return ''

  const maxValue = Math.max(...values)
  const minValue = Math.min(...values)

  // 对于延迟类指标，最小值最优
  const isLatencyMetric = metric.includes('lat') || metric.includes('await')

  if (isLatencyMetric) {
    if (currentValue === minValue) return 'best-value'
    if (currentValue === maxValue) return 'worst-value'
  } else {
    if (currentValue === maxValue) return 'best-value'
    if (currentValue === minValue) return 'worst-value'
  }

  return ''
}

const getColor = (index) => {
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#5ec8c6']
  return colors[index % colors.length]
}

const initCharts = () => {
  if (!comparisonData.value || tableData.value.length === 0) return

  // 初始化所有图表
  initBarChart()
  initRadarChart()
  initLineChart()
  initHeatmapChart()
}

const initBarChart = () => {
  if (!barChartRef.value) return

  if (barChart) {
    barChart.dispose()
  }

  barChart = echarts.init(barChartRef.value)

  let title, yAxisName, getData

  if (chartMetricType.value === 'iops') {
    title = 'IOPS性能对比'
    yAxisName = 'IOPS'
    getData = (metrics) => (metrics.read_iops || 0) + (metrics.write_iops || 0)
  } else if (chartMetricType.value === 'bandwidth') {
    title = '带宽性能对比'
    yAxisName = '带宽(MB/s)'
    getData = (metrics) => ((metrics.read_kbps || 0) + (metrics.write_kbps || 0)) / 1024
  } else {
    title = 'P99延迟对比'
    yAxisName = '延迟(ms)'
    getData = (metrics) => metrics.lat_p99 || 0
  }

  const option = {
    title: { text: title, left: 'center' },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: comparisonData.value.tasks.map(t => t.name),
      bottom: 0,
      type: 'scroll'
    },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: comparisonData.value.common_io_models,
      axisLabel: { rotate: 45, interval: 0 }
    },
    yAxis: { type: 'value', name: yAxisName },
    series: comparisonData.value.tasks.map((task, index) => ({
      name: task.name,
      type: 'bar',
      data: comparisonData.value.comparison_data.map(item => {
        const metrics = item.metrics_by_task[task.id]
        return metrics ? getData(metrics) : 0
      }),
      itemStyle: { color: getColor(index) }
    }))
  }

  barChart.setOption(option)
}

const initRadarChart = () => {
  if (!radarChartRef.value) return
  if (!comparisonData.value.comparison_data.length) return

  if (radarChart) {
    radarChart.dispose()
  }

  radarChart = echarts.init(radarChartRef.value)

  // 选择第一个IO模型作为雷达图基准
  const selectedIOModel = comparisonData.value.comparison_data[0]

  const getMaxValue = (metric) => {
    return Math.max(...Object.values(selectedIOModel.metrics_by_task).map(m => m[metric] || 0)) * 1.2
  }

  const option = {
    title: {
      text: `${selectedIOModel.io_model_name} 性能雷达对比`,
      left: 'center'
    },
    tooltip: {},
    legend: {
      data: comparisonData.value.tasks.map(t => t.name),
      bottom: 0,
      type: 'scroll'
    },
    radar: {
      indicator: [
        { name: '读IOPS', max: getMaxValue('read_iops') },
        { name: '写IOPS', max: getMaxValue('write_iops') },
        { name: '读吞吐(MB/s)', max: getMaxValue('read_kbps') / 1024 },
        { name: '写吞吐(MB/s)', max: getMaxValue('write_kbps') / 1024 },
        { name: 'P99延迟(ms)', max: getMaxValue('lat_p99'), inverse: true },
        { name: 'P9999延迟(ms)', max: getMaxValue('lat_p9999'), inverse: true }
      ],
      radius: '60%'
    },
    series: [{
      type: 'radar',
      data: comparisonData.value.tasks.map((task, index) => {
        const metrics = selectedIOModel.metrics_by_task[task.id]
        return {
          name: task.name,
          value: [
            metrics.read_iops,
            metrics.write_iops,
            metrics.read_kbps / 1024,
            metrics.write_kbps / 1024,
            metrics.lat_p99,
            metrics.lat_p9999
          ],
          itemStyle: { color: getColor(index) }
        }
      })
    }]
  }

  radarChart.setOption(option)
}

const initLineChart = () => {
  if (!lineChartRef.value) return

  if (lineChart) {
    lineChart.dispose()
  }

  lineChart = echarts.init(lineChartRef.value)

  let title, yAxisName, getData

  if (chartMetricType.value === 'iops') {
    title = 'IOPS性能趋势对比'
    yAxisName = 'IOPS'
    getData = (metrics) => (metrics.read_iops || 0) + (metrics.write_iops || 0)
  } else if (chartMetricType.value === 'bandwidth') {
    title = '带宽性能趋势对比'
    yAxisName = '带宽(MB/s)'
    getData = (metrics) => ((metrics.read_kbps || 0) + (metrics.write_kbps || 0)) / 1024
  } else {
    title = 'P99延迟趋势对比'
    yAxisName = '延迟(ms)'
    getData = (metrics) => metrics.lat_p99 || 0
  }

  const option = {
    title: { text: title, left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: {
      data: comparisonData.value.tasks.map(t => t.name),
      bottom: 0,
      type: 'scroll'
    },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: comparisonData.value.common_io_models,
      boundaryGap: false
    },
    yAxis: { type: 'value', name: yAxisName },
    series: comparisonData.value.tasks.map((task, index) => ({
      name: task.name,
      type: 'line',
      smooth: true,
      data: comparisonData.value.comparison_data.map(item => {
        const metrics = item.metrics_by_task[task.id]
        return metrics ? getData(metrics) : 0
      }),
      itemStyle: { color: getColor(index) },
      areaStyle: { opacity: 0.3 }
    }))
  }

  lineChart.setOption(option)
}

const initHeatmapChart = () => {
  if (!heatmapChartRef.value) return

  if (heatmapChart) {
    heatmapChart.dispose()
  }

  heatmapChart = echarts.init(heatmapChartRef.value)

  let title, unit, getData

  if (chartMetricType.value === 'iops') {
    title = 'IOPS热力图对比'
    unit = ' IOPS'
    getData = (metrics) => (metrics.read_iops || 0) + (metrics.write_iops || 0)
  } else if (chartMetricType.value === 'bandwidth') {
    title = '带宽热力图对比'
    unit = ' MB/s'
    getData = (metrics) => ((metrics.read_kbps || 0) + (metrics.write_kbps || 0)) / 1024
  } else {
    title = 'P99延迟热力图对比'
    unit = ' ms'
    getData = (metrics) => metrics.lat_p99 || 0
  }

  // 准备热力图数据 [x, y, value]
  const heatmapData = []

  comparisonData.value.comparison_data.forEach((item, ioIndex) => {
    comparisonData.value.tasks.forEach((task, taskIndex) => {
      const metrics = item.metrics_by_task[task.id]
      const value = metrics ? getData(metrics) : 0
      heatmapData.push([ioIndex, taskIndex, value])
    })
  })

  const maxValue = Math.max(...heatmapData.map(d => d[2]))

  const option = {
    title: { text: title, left: 'center' },
    tooltip: {
      position: 'top',
      formatter: (params) => {
        const ioModel = comparisonData.value.common_io_models[params.data[0]]
        const taskName = comparisonData.value.tasks[params.data[1]].name
        return `${taskName}<br/>${ioModel}: ${params.data[2].toFixed(2)}${unit}`
      }
    },
    grid: { height: '60%', top: '15%', left: '15%' },
    xAxis: {
      type: 'category',
      data: comparisonData.value.common_io_models,
      splitArea: { show: true },
      axisLabel: { rotate: 45, interval: 0 }
    },
    yAxis: {
      type: 'category',
      data: comparisonData.value.tasks.map(t => t.name),
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: maxValue,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695']
      }
    },
    series: [{
      type: 'heatmap',
      data: heatmapData,
      label: { show: true, formatter: (params) => params.data[2].toFixed(0) },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
      }
    }]
  }

  heatmapChart.setOption(option)
}

const exportToCSV = () => {
  if (!tableData.value.length) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  // 构建CSV内容
  const headers = ['IO模型']
  comparisonData.value.tasks.forEach(task => {
    headers.push(`${task.name}-总IOPS`, `${task.name}-读IOPS`, `${task.name}-写IOPS`, `${task.name}-P99延迟`)
  })

  const rows = [headers.join(',')]

  tableData.value.forEach(row => {
    const rowData = [row.io_model_name]
    comparisonData.value.tasks.forEach(task => {
      rowData.push(
        row[`task_${task.id}_total_iops`],
        row[`task_${task.id}_read_iops`],
        row[`task_${task.id}_write_iops`],
        row[`task_${task.id}_lat_p99`]
      )
    })
    rows.push(rowData.join(','))
  })

  const csvContent = '\ufeff' + rows.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `任务对比_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()

  ElMessage.success('CSV文件导出成功')
}

// 监听图表类型切换，调整大小
watch(activeChartType, () => {
  nextTick(() => {
    if (activeChartType.value === '柱状图' && barChart) {
      barChart.resize()
    } else if (activeChartType.value === '雷达图' && radarChart) {
      radarChart.resize()
    } else if (activeChartType.value === '折线图' && lineChart) {
      lineChart.resize()
    } else if (activeChartType.value === '热力图' && heatmapChart) {
      heatmapChart.resize()
    }
  })
})

// 监听图表指标类型变化，重新初始化图表
watch(chartMetricType, () => {
  nextTick(() => {
    if (comparisonData.value && tableData.value.length > 0) {
      initBarChart()
      initLineChart()
      initHeatmapChart()
    }
  })
})

// 监听搜索和筛选条件变化，重置分页
watch([taskSearchQuery, taskStatusFilter], () => {
  taskCurrentPage.value = 1
})

// 生命周期
onMounted(() => {
  loadTasks()

  // 窗口大小变化时调整图表
  window.addEventListener('resize', () => {
    barChart?.resize()
    radarChart?.resize()
    lineChart?.resize()
    heatmapChart?.resize()
  })
})
</script>

<style scoped>
.task-comparison-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.filter-card,
.statistics-card,
.table-card,
.chart-card {
  margin-bottom: 20px;
}

.task-selection-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-weight: bold;
  color: #303133;
}

.chart-container {
  width: 100%;
  height: 600px;
}

.chart {
  width: 100%;
  height: 100%;
}

/* 表格样式 */
:deep(.best-value) {
  color: #67c23a;
  font-weight: bold;
}

:deep(.worst-value) {
  color: #f56c6c;
  font-weight: bold;
}

:deep(.even-row) {
  background-color: #fafafa;
}

:deep(.odd-row) {
  background-color: #ffffff;
}
</style>
