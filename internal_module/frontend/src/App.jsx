import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis, PieChart, Pie, Cell
} from 'recharts'
import './App.css'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

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
        <h1>Vacancy Dashboard</h1>
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
              <h3>Avg Salary</h3>
              <div className="value">{Math.round(stats.metrics.avg).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Median Salary</h3>
              <div className="value">{Math.round(stats.metrics.median).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Min Salary</h3>
              <div className="value">{Math.round(stats.metrics.min).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Max Salary</h3>
              <div className="value">{Math.round(stats.metrics.max).toLocaleString()}</div>
            </div>
          </div>

          <div className="charts-grid">
            <div className="chart-card">
              <h3>Salary vs Experience (Bubble)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid />
                  <XAxis type="number" dataKey="salary" name="Salary" unit="₽" />
                  <YAxis type="number" dataKey="experience" name="Experience (Years)" />
                  <ZAxis type="number" dataKey="count" range={[60, 400]} name="Vacancies" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter name="Vacancies" data={stats.bubble_data} fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Pulkovo vs Market</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={[
                    { name: 'Pulkovo', salary: stats.comparison.pulkovo },
                    { name: 'Market', salary: stats.comparison.market }
                  ]}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="salary" fill="#d00000">
                    {
                      [{ name: 'Pulkovo' }, { name: 'Market' }].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={index === 0 ? '#d00000' : '#8884d8'} />
                      ))
                    }
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Salary Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={stats.salary_dist}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Experience Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={stats.experience_dist}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {stats.experience_dist.map((entry, index) => (
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
