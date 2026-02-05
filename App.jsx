import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis, PieChart, Pie, Cell
} from 'recharts'
import './App.css'

/**
 * Unified Color Palette
 * These values match the CSS variables defined in index.css
 * Keeping them in sync ensures visual consistency across all charts and UI elements
 */
const CHART_COLORS = {
  // Primary chart colors - used for pie charts and multi-series data
  palette: [
    '#3b82f6', // --chart-color-1: Blue 500
    '#22d3ee', // --chart-color-2: Cyan 400
    '#a78bfa', // --chart-color-3: Violet 400
    '#f472b6', // --chart-color-4: Pink 400
    '#fbbf24'  // --chart-color-5: Amber 400
  ],
  // Primary accent for single-color charts (bar charts, scatter plots)
  primary: '#3b82f6',    // --accent-primary
  secondary: '#60a5fa',  // --accent-secondary
  // Axis and grid colors
  axis: '#94a3b8',       // --text-muted
  grid: '#334155'        // --bg-tertiary
};

// Legacy exports for backward compatibility
const COLORS = CHART_COLORS.palette;
const ACCENT_PRIMARY = CHART_COLORS.primary;
const ACCENT_SECONDARY = CHART_COLORS.secondary;

function App() {
  // Tab state: 'vvss' or 'b1' - detect from URL path
  const getInitialTab = () => {
    const path = window.location.pathname
    if (path === '/b1' || path === '/b1/') {
      return 'b1'
    }
    return 'vvss'
  }
  
  const [activeTab, setActiveTab] = useState(getInitialTab)
  
  // VVSS state
  const [roles, setRoles] = useState([])
  const [selectedRoleIndex, setSelectedRoleIndex] = useState(0)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [overallStats, setOverallStats] = useState(null)

  // B1 state
  const [b1Blocks, setB1Blocks] = useState([])
  const [selectedBlockIndex, setSelectedBlockIndex] = useState(null)
  const [selectedBlock, setSelectedBlock] = useState(null)
  const [b1Loading, setB1Loading] = useState(false)
  const [b1Error, setB1Error] = useState(null)

  useEffect(() => {
    // Fetch roles
    axios.get('/api/roles')
      .then(res => {
        setRoles(res.data)
        if (res.data.length > 0) {
          fetchStats(0)
        }
      })
      .catch(err => setError("Failed to load roles"))
    
    // Fetch overall statistics for ALL vacancies
    axios.get('/api/overall-stats')
      .then(res => {
        setOverallStats(res.data)
      })
      .catch(err => console.error("Failed to load overall stats"))
  }, [])

  // Fetch B1 blocks when tab changes to 'b1'
  useEffect(() => {
    if (activeTab === 'b1' && b1Blocks.length === 0) {
      setB1Loading(true)
      axios.get('/api/b1/blocks')
        .then(res => {
          setB1Blocks(res.data)
          setB1Loading(false)
          // Auto-select first block
          if (res.data.length > 0) {
            handleBlockSelect(0)
          }
        })
        .catch(err => {
          setB1Error("Ошибка загрузки данных Б1")
          setB1Loading(false)
        })
    }
  }, [activeTab])

  const fetchStats = (index) => {
    setLoading(true)
    setError(null)
    axios.get(`/api/stats/${index}`)
      .then(res => {
        if (res.data.error) {
          setError(res.data.error)
          setStats(null)
        } else {
          setStats(res.data)
        }
        setLoading(false)
      })
      .catch(err => {
        setError("Failed to load stats")
        setLoading(false)
      })
  }

  const handleRoleChange = (e) => {
    const idx = parseInt(e.target.value)
    setSelectedRoleIndex(idx)
    fetchStats(idx)
  }

  const handleBlockSelect = (index) => {
    setSelectedBlockIndex(index)
    setB1Loading(true)
    axios.get(`/api/b1/blocks/${index}`)
      .then(res => {
        setSelectedBlock(res.data)
        setB1Loading(false)
      })
      .catch(err => {
        setB1Error("Ошибка загрузки блока")
        setB1Loading(false)
      })
  }

  const handleBlockChange = (e) => {
    const idx = parseInt(e.target.value)
    handleBlockSelect(idx)
  }

  const formatSalary = (value) => {
    if (value === null || value === undefined) return '—'
    return Math.round(value).toLocaleString('ru-RU') + ' ₽'
  }

  // Render VVSS content
  const renderVVSSContent = () => (
    <>
      <div className="header">
        <h1>Барометр вакансий ВВСС</h1>
        <div className="controls">
          <select value={selectedRoleIndex} onChange={handleRoleChange}>
            {roles.map((role, idx) => (
              <option key={idx} value={idx}>{role.name}</option>
            ))}
          </select>
          {stats && stats.metrics && (
            <div className="vacancy-count">
              Всего вакансий по профессии: <span>{stats.metrics.count}</span>
            </div>
          )}
        </div>
      </div>

      {!loading && stats && stats.metrics && stats.comparison && (
        <div className="market-card">
          <h3>Сравнение с рынком по заработной плате</h3>
          <div className="market-card-header">
            <button className="team-project-btn">
              С проектом "Мы команда"
            </button>
          </div>
          <div className="market-labels">
            <div className="label-below">Ниже рынка</div>
            <div className="label-in">В рынке</div>
            <div className="label-above">Выше рынка</div>
          </div>
          <div className="market-scale">
            <div 
              className="band-below" 
              style={{ width: '25%' }}
            ></div>
            <div 
              className="band-in" 
              style={{ left: '25%', width: '50%' }}
            ></div>
            <div 
              className="band-above" 
              style={{ left: '75%', width: '25%' }}
            ></div>
            {stats.comparison.pulkovo > 0 && (
              <>
                <div 
                  className="marker-pulkovo-line" 
                  style={{ left: `${Math.min(Math.max(((stats.comparison.pulkovo - stats.metrics.min) / (stats.metrics.max - stats.metrics.min)) * 100, 2), 98)}%` }}
                  title="Пулково зарплата"
                ></div>
                <div 
                  className="marker-pulkovo-label" 
                  style={{ left: `${Math.min(Math.max(((stats.comparison.pulkovo - stats.metrics.min) / (stats.metrics.max - stats.metrics.min)) * 100, 2), 98)}%` }}
                >
                  {Math.round(stats.comparison.pulkovo).toLocaleString()} ₽
                </div>
              </>
            )}
          </div>
          <div className="market-ticks">
            <div className="val-p25">{Math.round(stats.metrics.min + (stats.metrics.max - stats.metrics.min) * 0.25).toLocaleString()} ₽</div>
            <div className="val-p50">{Math.round(stats.metrics.median).toLocaleString()} ₽</div>
            <div className="val-p75">{Math.round(stats.metrics.min + (stats.metrics.max - stats.metrics.min) * 0.75).toLocaleString()} ₽</div>
            <div className="val-max">{Math.round(stats.metrics.max).toLocaleString()} ₽</div>
          </div>
        </div>
      )}

      {loading && <div className="loading">Loading...</div>}
      
      {error && <div className="error">{error}</div>}

      {!loading && stats && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Среднее</h3>
              <div className="value">{Math.round(stats.metrics.avg).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Медиана</h3>
              <div className="value">{Math.round(stats.metrics.median).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Минимум</h3>
              <div className="value">{Math.round(stats.metrics.min).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Максимум</h3>
              <div className="value">{Math.round(stats.metrics.max).toLocaleString()}</div>
            </div>
          </div>

          <div className="charts-grid">
            <div className="chart-card">
              <h3>Зарплата vs Опыт</h3>
              <ResponsiveContainer width="100%" height="65%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis type="number" dataKey="salary" name="Зарплата" unit="₽" stroke={CHART_COLORS.axis} />
                  <YAxis 
                    type="number" 
                    dataKey="experience" 
                    name="Опыт" 
                    stroke={CHART_COLORS.axis}
                    domain={[0, 8]}
                    ticks={[0, 2, 4.5, 8]}
                    tickFormatter={(value) => {
                      const labels = {
                        0: 'Нет опыта',
                        2: 'От 1 года до 3 лет',
                        4.5: 'От 3 до 6 лет',
                        8: 'Более 6 лет'
                      };
                      return labels[value] || value;
                    }}
                    width={75}
                  />
                  <ZAxis type="number" dataKey="count" range={[60, 400]} name="Вакансии" />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    formatter={(value, name) => {
                      if (name === 'Опыт') {
                        const labels = {
                          0: 'Нет опыта',
                          2: 'От 1 года до 3 лет',
                          4.5: 'От 3 до 6 лет',
                          8: 'Более 6 лет'
                        };
                        return labels[value] || value;
                      }
                      return value;
                    }}
                  />
                  <Scatter name="Vacancies" data={stats.bubble_data} fill={CHART_COLORS.primary} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Распределение опыта</h3>
              <ResponsiveContainer width="100%" height="65%">
                <PieChart>
                  <Pie
                    data={stats.experience_dist.filter(item => item.value > 0)}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius="70%"
                    fill={CHART_COLORS.primary}
                    dataKey="value"
                    animationBegin={200}
                    animationDuration={800}
                  >
                    {stats.experience_dist.filter(item => item.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS.palette[index % CHART_COLORS.palette.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card chart-card-fullscreen">
              <h3>Распределение зарплат</h3>
              <ResponsiveContainer width="100%" height="65%">
                <BarChart
                  data={stats.salary_dist}
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis interval="0" dataKey="range" stroke={CHART_COLORS.axis} />
                  <YAxis stroke={CHART_COLORS.axis} />
                  <Tooltip />
                  <Bar dataKey="count" fill={CHART_COLORS.primary} name="Количество" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Распределение по типу занятости</h3>
              <ResponsiveContainer width="100%" height="65%">
                <BarChart
                  data={stats.employment_dist}
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis interval="0" dataKey="name" stroke={CHART_COLORS.axis} />
                  <YAxis stroke={CHART_COLORS.axis} />
                  <Tooltip />
                  <Bar dataKey="count" fill={CHART_COLORS.primary} name="Количество" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Распределение по графику работы</h3>
              <ResponsiveContainer width="100%" height="65%">
                <BarChart
                  data={stats.schedule_dist}
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis interval="0" dataKey="name" stroke={CHART_COLORS.axis} />
                  <YAxis stroke={CHART_COLORS.axis} />
                  <Tooltip />
                  <Bar dataKey="count" fill={CHART_COLORS.primary} name="Количество" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      <div className="header">
        <h1>Общая статистика</h1>
        <div className="controls">
          {overallStats && (
            <div className="vacancy-count">
              Всего вакансий: <span>{overallStats.total_count}</span>
            </div>
          )}
        </div>
      </div>

      {overallStats && overallStats.metrics && (
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Среднее</h3>
            <div className="value">{Math.round(overallStats.metrics.avg).toLocaleString()}</div>
          </div>
          <div className="metric-card">
            <h3>Медиана</h3>
            <div className="value">{Math.round(overallStats.metrics.median).toLocaleString()}</div>
          </div>
          <div className="metric-card">
            <h3>Минимум</h3>
            <div className="value">{Math.round(overallStats.metrics.min).toLocaleString()}</div>
          </div>
          <div className="metric-card">
            <h3>Максимум</h3>
            <div className="value">{Math.round(overallStats.metrics.max).toLocaleString()}</div>
          </div>
        </div>
      )}
    </>
  )

  // Render B1 content with dropdown
  const renderB1Content = () => {
    // Calculate statistics if block is selected
    let blockAvg = null, blockMedian = null, blockMin = null, blockMax = null
    if (selectedBlock) {
      const positions = selectedBlock.positions
      const monthlySalaries = positions
        .map(p => p.monthly_salary.avg || p.monthly_salary.median)
        .filter(v => v !== null && v !== undefined)
      
      blockAvg = monthlySalaries.length > 0 
        ? monthlySalaries.reduce((a, b) => a + b, 0) / monthlySalaries.length 
        : null
      
      const sortedSalaries = [...monthlySalaries].sort((a, b) => a - b)
      blockMedian = sortedSalaries.length > 0 
        ? sortedSalaries[Math.floor(sortedSalaries.length / 2)] 
        : null
      
      blockMin = sortedSalaries.length > 0 ? sortedSalaries[0] : null
      blockMax = sortedSalaries.length > 0 ? sortedSalaries[sortedSalaries.length - 1] : null
    }

    return (
      <>
        <div className="header">
          <h1>Обзор зарплат Б1</h1>
          <p className="b1-subtitle">Региональный обзор Санкт-Петербург 2024</p>
          <div className="controls">
            <select 
              value={selectedBlockIndex !== null ? selectedBlockIndex : ''} 
              onChange={handleBlockChange}
              disabled={b1Blocks.length === 0}
            >
              {b1Blocks.length === 0 && <option value="">Загрузка...</option>}
              {b1Blocks.map((block, idx) => (
                <option key={idx} value={idx}>{block.name}</option>
              ))}
            </select>
            {selectedBlock && (
              <div className="vacancy-count">
                Должностей в блоке: <span>{selectedBlock.positions.length}</span>
              </div>
            )}
          </div>
        </div>

        {b1Loading && <div className="loading">Загрузка...</div>}
        {b1Error && <div className="error">{b1Error}</div>}

        {!b1Loading && selectedBlock && (
          <>
            {/* Block-level statistics */}
            <div className="metrics-grid">
              <div className="metric-card">
                <h3>Среднее</h3>
                <div className="value">{blockAvg ? Math.round(blockAvg).toLocaleString() : '—'}</div>
              </div>
              <div className="metric-card">
                <h3>Медиана</h3>
                <div className="value">{blockMedian ? Math.round(blockMedian).toLocaleString() : '—'}</div>
              </div>
              <div className="metric-card">
                <h3>Минимум</h3>
                <div className="value">{blockMin ? Math.round(blockMin).toLocaleString() : '—'}</div>
              </div>
              <div className="metric-card">
                <h3>Максимум</h3>
                <div className="value">{blockMax ? Math.round(blockMax).toLocaleString() : '—'}</div>
              </div>
            </div>

            {/* Positions table - simplified */}
            <div className="b1-positions-container">
              <div className="b1-positions-table b1-table-simple">
                <div className="b1-table-header">
                  <div className="b1-col-name">Должность</div>
                  <div className="b1-col-salary">Зарплата</div>
                </div>
                {selectedBlock.positions.map((position, idx) => (
                  <div key={idx} className="b1-table-row">
                    <div className="b1-col-name">
                      <div className="b1-position-name">{position.name}</div>
                    </div>
                    <div className="b1-col-salary b1-salary-main">
                      {formatSalary(position.monthly_salary.median || position.monthly_salary.avg)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </>
    )
  }

  return (
    <div className="container">
      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'vvss' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('vvss')
            window.history.pushState({}, '', '/')
          }}
        >
          ВВСС
        </button>
        <button 
          className={`tab-btn ${activeTab === 'b1' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('b1')
            window.history.pushState({}, '', '/b1')
          }}
        >
          Б1
        </button>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'vvss' ? renderVVSSContent() : renderB1Content()}
    </div>
  )
}

export default App
