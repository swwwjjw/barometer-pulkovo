import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis, PieChart, Pie, Cell
} from 'recharts'
import './App.css'

// New color palette
const COLORS = [
  '#3b82f6', // Blue 500
  '#22d3ee', // Cyan 400
  '#a78bfa', // Violet 400
  '#f472b6', // Pink 400
  '#fbbf24'  // Amber 400
];

const ACCENT_PRIMARY = '#3b82f6';
const ACCENT_SECONDARY = '#60a5fa';

function App() {
  const [roles, setRoles] = useState([])
  const [selectedRoleIndex, setSelectedRoleIndex] = useState(0)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios.get('/api/roles')
      .then(res => {
        setRoles(res.data)
        if (res.data.length > 0) {
          fetchStats(0)
        }
      })
      .catch(err => setError("Failed to load roles"))
  }, [])

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

  return (
    <div className="container">
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
              Всего вакансий: <span>{stats.metrics.count}</span>
            </div>
          )}
        </div>
      </div>

      {!loading && stats && stats.metrics && stats.comparison && (
        <div className="chart-card">
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
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis type="number" dataKey="salary" name="Зарплата" unit="₽" stroke="#94a3b8" />
                  <YAxis type="number" dataKey="experience" name="Опыт" stroke="#94a3b8" />
                  <ZAxis type="number" dataKey="count" range={[60, 400]} name="Вакансии" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter name="Vacancies" data={stats.bubble_data} fill={ACCENT_PRIMARY} />
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
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {stats.experience_dist.filter(item => item.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
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
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis interval="0" dataKey="range" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip />
                  <Bar dataKey="count" fill={ACCENT_PRIMARY} name="Количество" />
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
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis interval="0" dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip />
                  <Bar dataKey="count" fill={ACCENT_PRIMARY} name="Количество" />
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
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis interval="0" dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip />
                  <Bar dataKey="count" fill={ACCENT_PRIMARY} name="Количество" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default App
