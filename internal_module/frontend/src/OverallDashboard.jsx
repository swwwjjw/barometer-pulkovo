import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'
import './App.css'

/**
 * Unified Color Palette
 * These values match the CSS variables defined in index.css
 */
const CHART_COLORS = {
  palette: [
    '#3b82f6', // Blue 500
    '#22d3ee', // Cyan 400
    '#a78bfa', // Violet 400
    '#f472b6', // Pink 400
    '#fbbf24'  // Amber 400
  ],
  primary: '#3b82f6',
  secondary: '#60a5fa',
  axis: '#94a3b8',
  grid: '#334155'
};

function OverallDashboard() {
  const [overallStats, setOverallStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    let cancelled = false
    
    axios.get('/api/overall-stats')
      .then(res => {
        if (!cancelled) {
          setOverallStats(res.data)
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Не удалось загрузить общую статистику")
          setLoading(false)
        }
      })
    
    return () => {
      cancelled = true
    }
  }, [])

  const handleBackClick = () => {
    navigate('/')
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Общая статистика</h1>
        <div className="controls">
          <button className="back-btn" onClick={handleBackClick}>
            ← Назад к профессиям
          </button>
          {overallStats && (
            <div className="vacancy-count">
              Всего вакансий: <span>{overallStats.total_count}</span>
            </div>
          )}
        </div>
      </div>

      {loading && <div className="loading">Загрузка...</div>}
      
      {error && <div className="error">{error}</div>}

      {!loading && overallStats && overallStats.metrics && (
        <>
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

          <div className="charts-grid">
            <div className="chart-card">
              <h3>Распределение опыта</h3>
              <ResponsiveContainer width="100%" height="65%">
                <PieChart>
                  <Pie
                    data={overallStats.experience_dist.filter(item => item.value > 0)}
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
                    {overallStats.experience_dist.filter(item => item.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS.palette[index % CHART_COLORS.palette.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Распределение по типу занятости</h3>
              <ResponsiveContainer width="100%" height="65%">
                <BarChart
                  data={overallStats.employment_dist}
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

            <div className="chart-card chart-card-fullscreen">
              <h3>Распределение по графику работы</h3>
              <ResponsiveContainer width="100%" height="65%">
                <BarChart
                  data={overallStats.schedule_dist}
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis interval="0" dataKey="name" stroke={CHART_COLORS.axis} />
                  <YAxis stroke={CHART_COLORS.axis} />
                  <Tooltip />
                  <Bar dataKey="count" fill={CHART_COLORS.palette[1]} name="Количество" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default OverallDashboard
