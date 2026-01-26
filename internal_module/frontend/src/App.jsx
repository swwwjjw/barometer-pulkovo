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
        <h1>Барометр вакансий</h1>
        <div className="controls">
          <select value={selectedRoleIndex} onChange={handleRoleChange}>
            {roles.map((role, idx) => (
              <option key={idx} value={idx}>{role.name}</option>
            ))}
          </select>
        </div>
      </div>

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
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
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
              <h3>Пулково vs Рынок</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={[
                    { name: 'Пулково', salary: stats.comparison.pulkovo },
                    { name: 'Рынок', salary: stats.comparison.market }
                  ]}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Зарплата">
                    {
                      [{ name: 'Пулково' }, { name: 'Маркет' }].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={index === 0 ? ACCENT_PRIMARY : '#22d3ee'} />
                      ))
                    }
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Распределение зарплат</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={stats.salary_dist}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="range" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip />
                  <Bar dataKey="count" fill={ACCENT_SECONDARY} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Распределение опыта</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={stats.experience_dist.filter(item => item.value > 0)}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
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
          </div>
        </>
      )}
    </div>
  )
}

export default App
